"""Tests for Circle Arc Testnet (Chain ID 5042002) Integration & Native USDC Settlement.

Deterministic Safety Standards:
- Minimum 2 assertions per function.
- Function length <= 60 lines.
"""

from agent_keeper.config import (
    ARC_TESTNET_CHAIN_ID,
    SUPPORTED_CHAINS,
)
from agent_keeper.schemas import (
    TxExecutionRequest,
    X402PaymentRequest,
)
from agent_keeper.server import keeper_agent_balance
from agent_keeper.x402 import X402PaymentManager, resolve_verifier


TEST_VERIFIER = "0xABaBaBaBABabABabAbAbABAbABabababaBaBABaB"


def test_arc_testnet_chain_id_and_network_registry():
    """Verify Arc Testnet chain ID 5042002 is registered in supported chains."""
    assert ARC_TESTNET_CHAIN_ID == 5042002, "Arc Testnet chain ID must be 5042002"
    assert 5042002 in SUPPORTED_CHAINS, "Chain ID 5042002 must be in SUPPORTED_CHAINS"
    assert (
        SUPPORTED_CHAINS[5042002] == "Arc Testnet"
    ), "Chain 5042002 must map to 'Arc Testnet'"


def test_arc_testnet_x402_permit_domain_binding(monkeypatch):
    """Verify EIP-712 micro-payment permit correctly binds to Arc Testnet."""
    monkeypatch.setenv("ARC_X402_VERIFIER", TEST_VERIFIER)
    mgr = X402PaymentManager()
    req = X402PaymentRequest(
        resource_url="https://api.testnet.arc.network/v1/oracle",
        amount_usdc=0.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042002,
    )
    res = mgr.settle_payment(req)
    assert res.success is True, "Payment on Arc Testnet must succeed"
    assert res.payment_hash.startswith("0x"), "Payment hash must be hex string"
    assert len(res.payment_hash) == 66, "Payment hash must be 32 bytes (66 chars)"
    assert res.signature is not None, "Signature must not be None"
    assert len(res.signature) == 132, "EIP-712 signature must be 65 bytes hex"


def test_arc_testnet_resolve_verifier(monkeypatch):
    """Verify resolve_verifier accepts Arc Testnet chain ID 5042002."""
    monkeypatch.setenv("ARC_X402_VERIFIER", TEST_VERIFIER)
    v_main = resolve_verifier(5042)
    v_test = resolve_verifier(5042002)
    assert v_main == TEST_VERIFIER, "Mainnet verifier must match"
    assert v_test == TEST_VERIFIER, "Testnet verifier must match"


def test_arc_testnet_execution_request_schema():
    """Verify TxExecutionRequest validates Arc Testnet chain ID 5042002."""
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x",
        chain_id=5042002,
        value_wei=0,
    )
    assert req.chain_id == 5042002, "Chain ID must match Arc Testnet"
    assert req.value_wei == 0, "Value wei must be 0"
    assert req.target_address.startswith("0x"), "Target must start with 0x"


def test_arc_testnet_treasury_balance_query():
    """Verify keeper_agent_balance includes Arc Testnet entry."""
    treasury = keeper_agent_balance()
    assert "balances" in treasury, "Treasury must contain balances key"
    assert "Arc Testnet (5042002)" in treasury["balances"], "Must include Arc Testnet"
    assert isinstance(treasury["balances"]["Arc Testnet (5042002)"], dict), "Must be dict"
