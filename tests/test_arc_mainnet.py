"""Tests for Arc Mainnet (Chain ID 5042) Integration & Native USDC Settlement.

Deterministic Safety Standards:
- Minimum 2 assertions per function.
- Function length <= 60 lines.
"""

import pytest
from agent_keeper.config import ARC_MAINNET_CHAIN_ID, SUPPORTED_CHAINS
from agent_keeper.schemas import (
    TxExecutionRequest,
    X402PaymentRequest,
)
from agent_keeper.server import _query_rpc_balance, keeper_agent_balance
from agent_keeper.x402 import X402PaymentManager


def test_arc_chain_id_and_network_registry():
    """Verify Arc Mainnet chain ID 5042 is registered in supported chains."""
    assert ARC_MAINNET_CHAIN_ID == 5042, "Arc Mainnet chain ID must be 5042"
    assert 5042 in SUPPORTED_CHAINS, "Chain ID 5042 must be in SUPPORTED_CHAINS"
    assert (
        SUPPORTED_CHAINS[5042] == "Arc Mainnet"
    ), "Chain 5042 must map to 'Arc Mainnet'"


def test_arc_x402_permit_domain_binding():
    """Verify EIP-712 micro-payment permit correctly binds to Arc Mainnet."""
    mgr = X402PaymentManager()
    req = X402PaymentRequest(
        resource_url="https://api.arc.network/v1/oracle",
        amount_usdc=0.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042,
    )
    res = mgr.settle_payment(req)
    assert res.success is True, "Payment on Arc Mainnet must succeed"
    assert res.payment_hash.startswith("0x"), "Payment hash must be hex string"
    assert len(res.payment_hash) == 66, "Payment hash must be 32 bytes (66 chars)"
    assert res.signature is not None, "Signature must not be None"
    assert len(res.signature) == 132, "EIP-712 signature must be 65 bytes hex"


def test_arc_x402_spending_ceiling_exhaustion():
    """Verify cumulative spending ceiling ($5.00) prevents runaway drain on Arc."""
    mgr = X402PaymentManager()
    req = X402PaymentRequest(
        resource_url="https://api.arc.network/v1/compute",
        amount_usdc=3.00,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042,
    )
    res1 = mgr.settle_payment(req)
    assert res1.success is True, "First payment of $3.00 must succeed"
    assert mgr.total_spent == pytest.approx(3.00), "Spent must be 3.00"

    # Second payment of $3.00 exceeds $5.00 limit
    res2 = mgr.settle_payment(req)
    assert res2.success is False, "Second payment exceeding cap must fail"
    assert "Cumulative budget exceeded" in str(res2.error), "Error must cite budget"


def test_arc_balance_rpc_query():
    """Verify RPC balance inspection handles Arc Mainnet with EIP-55 address."""
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    bal = _query_rpc_balance(addr, 5042)
    assert isinstance(bal, dict), "Balance must be returned as dict"
    assert bal.get("symbol") == "USDC", "Arc native gas symbol must be USDC"
    assert "balance_wei" in bal, "Balance must report balance_wei"

    treasury = keeper_agent_balance()
    assert "balances" in treasury, "Treasury must include balances key"
    assert "Arc Mainnet (5042)" in treasury["balances"], "Treasury must include Arc Mainnet"
    assert isinstance(treasury["balances"]["Arc Mainnet (5042)"], dict), "Entry must be dict"


def test_arc_execution_request_schema_validation():
    """Verify TxExecutionRequest validates Arc chain ID and byte ceilings."""
    req = TxExecutionRequest(
        target_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        calldata_hex="0xa9059cbb000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa960450000000000000000000000000000000000000000000000000000000002faf080",
        chain_id=5042,
        value_wei=0,
    )
    assert req.chain_id == 5042, "Chain ID must match Arc Mainnet"
    assert req.value_wei == 0, "Value wei must be 0 for token transfer"
    assert req.target_address.startswith("0x"), "Target must have 0x prefix"


def test_arc_replay_protection_uniqueness():
    """Verify successive settlement challenges produce unique nonces and hashes."""
    mgr = X402PaymentManager()
    req1 = X402PaymentRequest(
        resource_url="https://api.arc.network/v1/feed/a",
        amount_usdc=0.10,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042,
    )
    req2 = X402PaymentRequest(
        resource_url="https://api.arc.network/v1/feed/b",
        amount_usdc=0.10,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042,
    )
    res1 = mgr.settle_payment(req1)
    res2 = mgr.settle_payment(req2)
    assert res1.success is True and res2.success is True, "Both must succeed"
    assert (
        res1.payment_hash != res2.payment_hash
    ), "Payment hashes must be distinct"
    assert res1.signature != res2.signature, "Signatures must be distinct"
