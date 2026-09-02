"""
Property-based fuzz suite for FlatMerkleTree (src/agent_keeper/merkle_tree.py).

Targets the two safety properties that matter for a Merkle audit primitive:
  1. Construction, proof generation, and genuine-proof verification never
     raise on any well-typed leaf set, across randomized leaf counts and
     tree topologies (odd/even layer widths exercise the duplicate-tail path).
  2. A proof tampered in any of several realistic ways (wrong sibling hash,
     flipped position tag, truncated path, appended garbage step, wrong
     root) is rejected 100% of the time -- it must return False, never True,
     and never raise.
"""

import string

from hypothesis import assume, given, settings, strategies as st
from hypothesis import HealthCheck

from agent_keeper.merkle_tree import FlatMerkleTree

# Leaf content: printable text including empty strings and unicode, so the
# fuzzer isn't just hashing distinct ASCII words.
leaf_text = st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=0x2FFFF, blacklist_categories=("Cs",)), max_size=40)

# Leaf lists: 1-64 leaves. Bounded above to keep 5,000 examples tractable;
# still exercises every odd/even duplicate-tail topology up to a 6-layer tree.
leaf_lists = st.lists(leaf_text, min_size=1, max_size=64)

HEX_CHARS = "0123456789abcdef"


def _hash_entering_step(leaf: str, proof, step_index: int) -> bytes:
    """Replay verify_proof's hash chain up to (not including) proof[step_index],
    returning the 'current' bytes that step would combine with its sibling."""
    from eth_utils import keccak

    current = keccak(leaf.encode("utf-8"))
    for sib_hex, pos in proof[:step_index]:
        sibling_bytes = bytes.fromhex(sib_hex[2:])
        current = keccak(sibling_bytes + current) if pos == "left" else keccak(current + sibling_bytes)
    return current


@settings(max_examples=5000, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(leaves=leaf_lists, data=st.data())
def test_fuzz_build_and_genuine_proof_never_panics(leaves, data):
    """Random leaf counts/topologies: build + every leaf's own proof must
    verify True against the tree's own root, with no exception anywhere."""
    tree = FlatMerkleTree(leaves)

    root = tree.root
    assert root.startswith("0x")
    assert len(root) == 66  # 0x + 32 bytes hex

    leaf_index = data.draw(st.integers(min_value=0, max_value=len(leaves) - 1))
    proof = tree.get_proof(leaf_index)

    assert FlatMerkleTree.verify_proof(leaves[leaf_index], proof, root) is True


@settings(max_examples=5000, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(leaves=leaf_lists, data=st.data())
def test_fuzz_tampered_proof_rejected_100_percent(leaves, data):
    """A proof mutated by any of several realistic tampering strategies must
    be rejected -- verify_proof returns False, never True, never raises."""
    tree = FlatMerkleTree(leaves)
    root = tree.root

    leaf_index = data.draw(st.integers(min_value=0, max_value=len(leaves) - 1))
    proof = tree.get_proof(leaf_index)
    leaf = leaves[leaf_index]

    if not proof:
        # Single-leaf tree: no proof steps exist to tamper with. The only
        # tampering available is asserting a wrong root, covered below.
        assert FlatMerkleTree.verify_proof(leaf, proof, "0x" + "00" * 32) is False
        return

    strategy = data.draw(st.sampled_from([
        "flip_sibling_hash",
        "swap_position",
        "truncate",
        "append_garbage_step",
        "wrong_root",
        "reorder_steps",
    ]))

    tampered_proof = list(proof)
    tampered_root = root

    if strategy == "flip_sibling_hash":
        i = data.draw(st.integers(min_value=0, max_value=len(tampered_proof) - 1))
        sib_hex, pos = tampered_proof[i]
        # Flip one hex nibble -- stays syntactically valid hex, semantically wrong.
        nibble_idx = data.draw(st.integers(min_value=2, max_value=len(sib_hex) - 1))
        orig_char = sib_hex[nibble_idx]
        new_char = data.draw(st.sampled_from([c for c in HEX_CHARS if c != orig_char.lower()]))
        mutated = sib_hex[:nibble_idx] + new_char + sib_hex[nibble_idx + 1:]
        tampered_proof[i] = (mutated, pos)

    elif strategy == "swap_position":
        i = data.draw(st.integers(min_value=0, max_value=len(tampered_proof) - 1))
        sib_hex, pos = tampered_proof[i]
        # KNOWN PROPERTY (see test_duplicate_leaf_position_swap_is_undetectable
        # below): when the sibling entering this step hashes identically to
        # the accumulator entering this step (duplicate-leaf trees), A+B and
        # B+A are byte-identical, so swapping "left"/"right" here is
        # mathematically undetectable -- not a bug in verify_proof, a
        # documented limitation. Skip only that degenerate case.
        current_before = _hash_entering_step(leaf, proof, i)
        sibling_bytes = bytes.fromhex(sib_hex[2:])
        assume(sibling_bytes != current_before)
        flipped = "left" if pos == "right" else "right"
        tampered_proof[i] = (sib_hex, flipped)

    elif strategy == "truncate":
        cut = data.draw(st.integers(min_value=0, max_value=len(tampered_proof) - 1))
        tampered_proof = tampered_proof[:cut]

    elif strategy == "append_garbage_step":
        garbage_hash = "0x" + "ab" * 32
        garbage_pos = data.draw(st.sampled_from(["left", "right"]))
        tampered_proof = tampered_proof + [(garbage_hash, garbage_pos)]

    elif strategy == "wrong_root":
        # Leave proof genuine; corrupt the root instead.
        tampered_root = "0x" + ("0" if root[2] != "0" else "1") + root[3:]

    elif strategy == "reorder_steps":
        if len(tampered_proof) < 2:
            cut = 0
            tampered_proof = tampered_proof[:cut]
        else:
            tampered_proof = list(reversed(tampered_proof))

    result = FlatMerkleTree.verify_proof(leaf, tampered_proof, tampered_root)
    assert result is False


def test_duplicate_leaf_position_swap_is_undetectable():
    """
    FINDING (discovered by test_fuzz_tampered_proof_rejected_100_percent):
    FlatMerkleTree.verify_proof does NOT reject 100% of tampered proofs.

    With two leaves that hash identically (e.g. two equal strings), the
    single proof step's sibling hash equals the leaf's own hash (both are
    keccak(leaf)). Concatenation is then D+D regardless of declared
    position ("left" vs "right"), since both operands are identical bytes.
    Flipping the position tag is therefore silently accepted as if it were
    the genuine proof.

    This is not a leaf-forgery vulnerability (the attacker still needs the
    exact real leaf value to produce a matching accumulator), but it does
    mean a proof's (sibling_hash, position) pairs are not a strict,
    tamper-evident encoding of tree position when the tree contains
    duplicate leaf values. Callers that need position-uniqueness guarantees
    (e.g. distinguishing "leaf X at index 0" from "leaf X at index 1" when
    X appears twice) should not rely on this proof format alone.
    """
    tree = FlatMerkleTree(["", ""])
    proof = tree.get_proof(0)
    assert len(proof) == 1
    sib_hex, pos = proof[0]

    genuine = FlatMerkleTree.verify_proof("", proof, tree.root)
    assert genuine is True

    tampered = [(sib_hex, "left" if pos == "right" else "right")]
    still_accepts = FlatMerkleTree.verify_proof("", tampered, tree.root)

    # Documents the actual (surprising) current behavior rather than the
    # ideal one, so a future fix to this ambiguity turns this into a
    # failing test that must be consciously updated, not a silent gap.
    assert still_accepts is True


def test_empty_leaves_raises_documented_assertion_not_a_wild_panic():
    """The documented contract for empty input is an AssertionError, not an
    unhandled TypeError/IndexError from deeper in the tree-building code."""
    try:
        FlatMerkleTree([])
        raise RuntimeError("expected AssertionError for empty leaf list, none was raised")
    except AssertionError as e:
        assert "cannot be empty" in str(e)
