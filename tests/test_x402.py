"""
Test Suite for Autonomous x402 Micro-Payment Settlement
"""

from agent_keeper.schemas import X402PaymentRequest
from agent_keeper.x402 import X402PaymentManager


def test_payment_manager_initialization():
    mgr = X402PaymentManager()
    assert mgr.safety_limit == 5.00
    assert mgr.total_spent == 0.0


def test_successful_x402_settlement():
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
