"""
Unit tests for Flat Array Merkle Tree engine.
"""

from agent_keeper.merkle_tree import FlatMerkleTree


def test_merkle_tree_root_consistency():
    leaves = [
        "tx_hash_001",
        "tx_hash_002",
        "tx_hash_003",
        "tx_hash_004"
    ]
    tree = FlatMerkleTree(leaves)
    assert tree.root.startswith("0x")
    assert len(tree.root) == 66  # 32 bytes hex + '0x'


def test_merkle_proof_generation_and_verification():
    leaves = [
        "0x1111111111111111111111111111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333333333333333333333333333",
        "0x4444444444444444444444444444444444444444444444444444444444444444",
        "0x5555555555555555555555555555555555555555555555555555555555555555"
    ]
    tree = FlatMerkleTree(leaves)
    root = tree.root

    for i, leaf in enumerate(leaves):
        proof = tree.get_proof(i)
        assert len(proof) > 0
        assert FlatMerkleTree.verify_proof(leaf, proof, root) is True

    # Tampered leaf verification should fail
    tampered_leaf = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    proof0 = tree.get_proof(0)
    assert FlatMerkleTree.verify_proof(tampered_leaf, proof0, root) is False
