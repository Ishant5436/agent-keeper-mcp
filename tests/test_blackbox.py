"""
Black-Box Test Suite for AgentKeeper MCP
Focuses on external interface contracts, input/output validation, error handling,
adversarial payloads, and end-to-end tool execution behavior.
"""

import pytest

from agent_keeper.server import (
    keeper_agent_balance,
    keeper_audit_verify,
    keeper_execute_tx,
    keeper_x402_settle,
)


# ==============================================================================
# 1. Functional Tool Contract Tests (Black-Box)
# ==============================================================================

def test_blackbox_execute_tx_success_contract():
    """Black-box: executing a valid tx returns structured dictionary with expected keys."""
    res = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0xa9059cbb",
        value_wei=1000000000000000,  # 0.001 ETH
        chain_id=1,
    )
    assert isinstance(res, dict)
    assert res["success"] is True
    assert "tx_hash" in res and res["tx_hash"].startswith("0x")
    assert res["chain_id"] == 1
    assert res["status"] == "CONFIRMED"
    assert "audit_receipt" in res
    assert res["audit_receipt"]["relay_status"] == "RELAYED_VIA_KEEPERHUB"


def test_blackbox_execute_tx_adversarial_rejected():
    """Black-box: invalid inputs return structured failure without unhandled crash."""
    # Invalid chain ID
    res_bad_chain = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=999999,
    )
    assert res_bad_chain["success"] is False
    assert "error" in res_bad_chain
    assert "Unsupported chain ID" in res_bad_chain["error"]

    # Value above safety limit
    res_huge_val = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        value_wei=10**22,
    )
    assert res_huge_val["success"] is False
    assert "exceeds autonomous safety ceiling" in res_huge_val["error"]


def test_blackbox_x402_settle_contract():
    """Black-box: micro-payment settlement returns valid EIP-712 signature and token."""
    res = keeper_x402_settle(
        resource_url="https://api.paidservice.ai/v1/inference",
        amount_usdc=0.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    assert isinstance(res, dict)
    assert res["success"] is True
    assert res["amount_usdc"] == 0.50
    assert "signature" in res and res["signature"].startswith("0x")
    assert "payment_hash" in res and res["payment_hash"].startswith("0x")
    assert "auth_token" in res


def test_blackbox_audit_verify_contract():
    """Black-box: verifying a valid vs invalid hash returns correct boolean status."""
    # Valid pre-committed root hash
    valid_tx = "0x5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b"
    res_valid = keeper_audit_verify(tx_hash=valid_tx, chain_id=1)
    assert res_valid["verified"] is True
    assert "merkle_root" in res_valid
    assert res_valid["confirmations"] >= 1

    # Fake uncommitted hash
    fake_tx = "0x000000000000000000000000000000000000000000000000000000000000dead"
    res_fake = keeper_audit_verify(tx_hash=fake_tx, chain_id=1)
    assert res_fake["verified"] is False
    assert "Merkle inclusion proof failed" in res_fake["error"]


def test_blackbox_agent_balance_contract():
    """Black-box: balance inspection across multiple chains returns structured dictionary."""
    res = keeper_agent_balance(
        address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    assert isinstance(res, dict)
    assert res["success"] is True
    assert "queried_address" in res
    assert "balances" in res
    assert "spending_limit_usdc" in res
    assert "remaining_budget_usdc" in res


# ==============================================================================
# 2. Adversarial & Fuzzing Payloads (Black-Box)
# ==============================================================================

@pytest.mark.parametrize("malicious_input", [
    "'; DROP TABLE transactions; --",
    "<script>alert(1)</script>",
    "../../../etc/passwd",
    "\\x00\\x00\\x00",
    "A" * 1000,
    "🔥🚀💸",
])
def test_blackbox_fuzz_idempotency_key(malicious_input):
    """Black-box fuzzing: adversarial string payloads in idempotency_key must be handled cleanly."""
    res = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        idempotency_key=malicious_input,
        chain_id=1,
    )
    assert isinstance(res, dict)
    assert "success" in res


@pytest.mark.parametrize("bad_addr", [
    "",
    "0x",
    "0x123",
    "not_an_address",
    "0xGGGG6BF26964aF9D7eEd9e03E53415D37aA96045",
    None,
])
def test_blackbox_fuzz_invalid_addresses(bad_addr):
    """Black-box fuzzing: malformed addresses must return success=False with clear error."""
    res = keeper_execute_tx(
        target_address=bad_addr if bad_addr is not None else "",
        chain_id=1,
    )
    assert res["success"] is False
    assert "error" in res
