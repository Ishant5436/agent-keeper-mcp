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
        calldata_hex="0xa9059cbb",
        value_wei=0,
        chain_id=1,
    )
    assert req.target_address == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert req.chain_id == 1


def test_strict_eip55_checksum_enforcement():
    # Valid all-lowercase address -> normalized to checksum
    req_lower = TxExecutionRequest(
        target_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    )
    assert req_lower.target_address == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    # Corrupted mixed-case checksum (single character flipped: 'B' -> 'b') -> MUST REJECT
    broken_checksum = "0xd8dA6bF26964aF9D7eEd9e03E53415D37aA96045"
    with pytest.raises(ValidationError) as excinfo:
        TxExecutionRequest(target_address=broken_checksum)
    assert "EIP-55 checksum validation failed" in str(excinfo.value)


def test_value_wei_safety_ceiling():
    # Valid small transfer (0.01 ETH)
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        value_wei=10000000000000000,  # 0.01 ETH
    )
    assert req.value_wei == 10000000000000000

    # Excessive transfer exceeding 0.10 ETH safety ceiling (e.g. 1,000 ETH) -> MUST REJECT
    with pytest.raises(ValidationError) as excinfo:
        TxExecutionRequest(
            target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            value_wei=10**24,  # 1,000,000 ETH
        )
    assert "exceeds autonomous safety ceiling" in str(excinfo.value)


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


def test_mantle_chain_id_support():
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x",
        value_wei=0,
        chain_id=5000,
    )
    assert req.chain_id == 5000


def test_creditcoin_chain_id_support():
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x",
        value_wei=0,
        chain_id=1024,
    )
    assert req.chain_id == 1024
