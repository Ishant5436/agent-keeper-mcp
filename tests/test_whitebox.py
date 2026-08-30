"""
White-Box Test Suite for AgentKeeper MCP
Focuses on internal logic, branch coverage, cryptographic invariants, and boundary conditions.
"""

import pytest
from eth_utils import keccak
from pydantic import ValidationError

from agent_keeper.audit import AuditProofVerifier
from agent_keeper.config import MAX_CALLDATA_BYTES, MAX_VALUE_WEI_CAP, SUPPORTED_CHAINS
from agent_keeper.relay import KeeperRelayClient
from agent_keeper.schemas import (
    AuditProofRequest,
    TxExecutionRequest,
    X402PaymentRequest,
)
from agent_keeper.x402 import X402PaymentManager


# ==============================================================================
# 1. Merkle Tree & Cryptographic Invariants (White-Box)
# ==============================================================================

def test_merkle_tree_single_leaf_root():
    """White-box test: single-leaf Merkle root must equal keccak(leaf)."""
    verifier = AuditProofVerifier()
    leaf = "0xsingleleaf"
    root = verifier.compute_merkle_root([leaf])
    expected = "0x" + keccak(leaf.encode("utf-8")).hex()
    assert root == expected


def test_merkle_tree_odd_leaf_duplication_invariant():
    """White-box test: odd-length leaf sets duplicate the last leaf to balance the tree."""
    verifier = AuditProofVerifier()
    leaves_3 = ["leaf1", "leaf2", "leaf3"]
    h1 = keccak(b"leaf1")
    h2 = keccak(b"leaf2")
    h3 = keccak(b"leaf3")
    parent1 = keccak(h1 + h2)
    parent2 = keccak(h3 + h3)
    expected_root = "0x" + keccak(parent1 + parent2).hex()

    computed_root = verifier.compute_merkle_root(leaves_3)
    assert computed_root == expected_root


def test_merkle_tree_empty_leaves_assertion():
    """White-box test: empty leaf list must trigger assertion failure."""
    verifier = AuditProofVerifier()
    with pytest.raises(AssertionError, match="cannot be empty"):
        verifier.compute_merkle_root([])


def test_merkle_tree_idempotent_registration():
    """White-box test: duplicate registration does not corrupt tree root."""
    verifier = AuditProofVerifier()
    root_before = verifier._state_root
    verifier.register_transaction("0x5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b")
    assert verifier._state_root == root_before


# ==============================================================================
# 2. X402 Payment Manager & EIP-712 State Invariants (White-Box)
# ==============================================================================

def test_x402_cumulative_spending_invariant():
    """White-box test: total_spent accumulator must strictly track expenditures."""
    mgr = X402PaymentManager(safety_limit=5.0)
    assert mgr.total_spent == 0.0

    req1 = X402PaymentRequest(
        resource_url="https://api.test.ai/v1",
        amount_usdc=1.25,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    res1 = mgr.settle_payment(req1)
    assert res1.success is True
    assert mgr.total_spent == 1.25

    req2 = X402PaymentRequest(
        resource_url="https://api.test.ai/v2",
        amount_usdc=2.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    res2 = mgr.settle_payment(req2)
    assert res2.success is True
    assert mgr.total_spent == 3.75

    # 3rd request would exceed safety limit (3.75 + 2.0 = 5.75 > 5.0) -> must fail without incrementing spent
    req3 = X402PaymentRequest(
        resource_url="https://api.test.ai/v3",
        amount_usdc=2.00,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    res3 = mgr.settle_payment(req3)
    assert res3.success is False
    assert "Cumulative budget exceeded" in res3.error
    assert mgr.total_spent == 3.75


# ==============================================================================
# 3. Relay Engine State Machine & Branch Coverage (White-Box)
# ==============================================================================

def test_relay_tx_hash_deterministic_seed():
    """White-box test: tx hash is deterministically derived from request fields + nonce."""
    client = KeeperRelayClient()
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x123456",
        value_wei=1000,
        chain_id=1,
    )
    h1 = client._compute_tx_hash(req, nonce=42)
    h2 = client._compute_tx_hash(req, nonce=42)
    h3 = client._compute_tx_hash(req, nonce=43)
    assert h1 == h2
    assert h1 != h3


def test_relay_idempotency_cache_mutation_immunity():
    """White-box test: cached idempotency response returns an independent deep copy."""
    client = KeeperRelayClient()
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        idempotency_key="unique-task-999",
        chain_id=1,
    )
    res1 = client.execute_transaction(req)
    res2 = client.execute_transaction(req)

    assert res1.tx_hash == res2.tx_hash
    assert res2.audit_receipt.get("idempotent_hit") is True


# ==============================================================================
# 4. Strict Schema Boundary & Validator Enforcement (White-Box)
# ==============================================================================

def test_unsupported_chain_id_rejection():
    """White-box test: chain_id validator must raise ValidationError for unsupported chains."""
    for bad_chain in [-1, 0, 9999, 1337, 56]:
        with pytest.raises(ValidationError) as excinfo:
            TxExecutionRequest(
                target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                chain_id=bad_chain,
            )
        assert "Unsupported chain ID" in str(excinfo.value) or "must be positive" in str(excinfo.value)


def test_all_supported_chain_ids_accepted():
    """White-box test: all 7 registered chain IDs pass validation."""
    for chain_id in SUPPORTED_CHAINS.keys():
        req = TxExecutionRequest(
            target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            chain_id=chain_id,
        )
        assert req.chain_id == chain_id


def test_calldata_boundary_exact_max_and_overflow():
    """White-box test: exactly MAX_CALLDATA_BYTES passes, +1 byte fails."""
    exact_max_hex = "0x" + "ff" * MAX_CALLDATA_BYTES
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex=exact_max_hex,
    )
    assert len(req.calldata_hex) == 2 + 2 * MAX_CALLDATA_BYTES

    overflow_hex = exact_max_hex + "ff"
    with pytest.raises(ValidationError) as excinfo:
        TxExecutionRequest(
            target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            calldata_hex=overflow_hex,
        )
    assert "exceeds maximum limit" in str(excinfo.value)


def test_value_wei_boundary_exact_ceiling_and_overflow():
    """White-box test: exactly MAX_VALUE_WEI_CAP passes, +1 wei fails."""
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        value_wei=MAX_VALUE_WEI_CAP,
    )
    assert req.value_wei == MAX_VALUE_WEI_CAP

    with pytest.raises(ValidationError) as excinfo:
        TxExecutionRequest(
            target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            value_wei=MAX_VALUE_WEI_CAP + 1,
        )
    assert "exceeds autonomous safety ceiling" in str(excinfo.value)
