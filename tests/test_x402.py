"""
Test Suite for Autonomous x402 Micro-Payment Settlement
"""

import pytest
from eth_account import Account
from eth_account.messages import encode_typed_data

from agent_keeper import x402
from agent_keeper.schemas import X402PaymentRequest
from agent_keeper.x402 import X402PaymentManager
TEST_VERIFIER = "0xABaBaBaBABabABabAbAbABAbABabababaBaBABaB"  # same value as tests/conftest.py

RECIPIENT = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_payment_manager_initialization():
    mgr = X402PaymentManager()
    assert mgr.safety_limit == 5.00
    assert mgr.total_spent == 0.0
    assert mgr._account.address.startswith("0x")


def test_successful_x402_settlement_with_eip712():
    mgr = X402PaymentManager()
    req = X402PaymentRequest(
        resource_url="https://api.quant-analytics.io/v1/alpha_signal",
        amount_usdc=0.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    res = mgr.settle_payment(req)
    assert res.success is True
    assert res.payment_hash.startswith("0x")
    assert res.auth_token is not None
    assert res.signature is not None
    assert res.signature.startswith("0x")
    assert len(res.signature) == 132  # 65-byte hex signature (0x + 130 hex chars)
    assert mgr.total_spent == 0.50


def test_cumulative_safety_budget_exhaustion():
    mgr = X402PaymentManager(safety_limit=2.00)
    req = X402PaymentRequest(
        resource_url="https://api.quant-analytics.io/v1/alpha_signal",
        amount_usdc=1.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    # First payment succeeds ($1.50 spent out of $2.00 limit)
    res1 = mgr.settle_payment(req)
    assert res1.success is True

    # Second payment of $1.50 would exceed cumulative $2.00 limit -> Rejected
    res2 = mgr.settle_payment(req)
    assert res2.success is False
    assert "Cumulative budget exceeded" in res2.error


def test_x402_settlement_on_arc_mainnet():
    mgr = X402PaymentManager()
    req = X402PaymentRequest(
        resource_url="https://api.arc.quant/v1/feed",
        amount_usdc=0.25,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        chain_id=5042,
    )
    res = mgr.settle_payment(req)
    assert res.success is True
    assert res.payment_hash.startswith("0x")
    assert res.signature is not None
    assert len(res.signature) == 132


def _req(**kw):
    return X402PaymentRequest(
        resource_url="https://api.arc.quant/v1/feed", amount_usdc=0.25, recipient_address=RECIPIENT, **kw
    )


@pytest.mark.no_verifier_env
def test_fails_closed_when_verifier_unset():
    mgr = X402PaymentManager()
    res = mgr.settle_payment(_req())
    assert res.success is False
    assert res.signature is None
    assert "ARC_X402_VERIFIER" in res.error and "deploy" in res.error.lower()
    assert mgr.total_spent == 0.0  # no budget consumed on a refused settlement


@pytest.mark.parametrize(
    "bad",
    [
        "0x" + "ab" * 20,  # all lowercase: no checksum
        "0xabababababababababababababababababababab",
        "0x4020000000000000000000000000000000000402",  # retired placeholder, never deployed
        "0x" + "00" * 20,  # zero address
        "not-an-address",
    ],
)
def test_fails_closed_on_invalid_verifier(monkeypatch, bad):
    monkeypatch.setenv("ARC_X402_VERIFIER", bad)
    res = X402PaymentManager().settle_payment(_req())
    assert res.success is False
    assert "checksum" in res.error


def test_fails_closed_for_non_arc_chain():
    res = X402PaymentManager().settle_payment(_req(chain_id=8453))
    assert res.success is False
    assert "8453" in res.error


def test_signature_recovers_to_agent_over_configured_verifier(monkeypatch):
    monkeypatch.setattr(x402.secrets, "randbits", lambda _bits: 7)
    monkeypatch.setattr(x402.time, "time", lambda: 1_000_000)
    mgr = X402PaymentManager()
    res = mgr.settle_payment(_req())
    assert res.success is True
    data = x402.build_permit_typed_data(
        5042, TEST_VERIFIER, mgr.signer_address, RECIPIENT, 250_000, 7, 1_000_000 + 300
    )
    recovered = Account.recover_message(encode_typed_data(full_message=data), signature=res.signature)
    assert recovered == mgr.signer_address
    assert data["domain"]["verifyingContract"] == TEST_VERIFIER
