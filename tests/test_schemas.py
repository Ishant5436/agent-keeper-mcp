"""
Test Suite for AgentKeeper Type System & Input Invariants
"""

import pytest
from pydantic import ValidationError

from agent_keeper.schemas import (
    TxExecutionRequest,
    X402PaymentRequest,
)


def test_valid_tx_execution_request():
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0xa9059cbb000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa960450000000000000000000000000000000000000000000000000de0b6b3a7640000",
        value_wei=0,
        chain_id=1,
    )
    assert req.target_address == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert req.chain_id == 1


def test_invalid_address_rejection():
    with pytest.raises(ValidationError):
        TxExecutionRequest(
            target_address="0xInvalidAddress123",
            calldata_hex="0x",
            value_wei=0,
            chain_id=1,
        )


def test_calldata_overflow_rejection():
    # 130 KB calldata exceeds 128 KB max
    giant_calldata = "0x" + "aa" * (131072 + 10)
    with pytest.raises(ValidationError):
        TxExecutionRequest(
            target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            calldata_hex=giant_calldata,
            value_wei=0,
            chain_id=1,
        )


def test_x402_payment_request_bounds():
    # Valid
    req = X402PaymentRequest(
        resource_url="https://api.paidservice.ai/v1/query",
        amount_usdc=1.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    assert req.amount_usdc == 1.50

    # Negative amount rejection
    with pytest.raises(ValidationError):
        X402PaymentRequest(
            resource_url="https://api.paidservice.ai/v1/query",
            amount_usdc=-0.50,
            recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        )

    # Above safety budget rejection ($100.00 > $5.00 limit)
    with pytest.raises(ValidationError):
        X402PaymentRequest(
            resource_url="https://api.paidservice.ai/v1/query",
            amount_usdc=100.00,
            recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        )
