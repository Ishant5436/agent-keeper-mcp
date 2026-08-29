"""
Strict Pydantic Type Definitions & Input Invariants (NASA Power of 10 Standard)
"""

import re
from typing import Any

from eth_utils import is_address, to_checksum_address
from pydantic import BaseModel, Field, field_validator

from agent_keeper.config import (
    MAX_AUTONOMOUS_PAYMENT_USDC,
    MAX_CALLDATA_BYTES,
    SUPPORTED_CHAINS,
)

HEX_REGEX = re.compile(r"^0x[a-fA-F0-9]*$")


class TxExecutionRequest(BaseModel):
    """
    Onchain execution request payload passed by AI agent.
    """

    target_address: str = Field(
        ..., description="Target EIP-55 contract or recipient address."
    )
    calldata_hex: str = Field(
        default="0x", description="Hex-encoded transaction calldata payload."
    )
    value_wei: int = Field(
        default=0, ge=0, description="Native ETH/token value in wei to transfer."
    )
    chain_id: int = Field(default=1, description="Target EVM chain ID.")
    max_priority_fee_gwei: float | None = Field(
        default=None, ge=0.0, description="Optional priority tip in Gwei."
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=64,
        description="Optional unique task ID to prevent duplicate txs.",
    )

    @field_validator("target_address")
    @classmethod
    def validate_target_address(cls, v: str) -> str:
        assert isinstance(v, str), "Target address must be a string"
        if not is_address(v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return to_checksum_address(v)

    @field_validator("calldata_hex")
    @classmethod
    def validate_calldata(cls, v: str) -> str:
        assert isinstance(v, str), "Calldata must be a string"
        clean = v.strip()
        if not clean.startswith("0x"):
            clean = "0x" + clean
        if not HEX_REGEX.match(clean):
            raise ValueError("Calldata must be valid hex-encoded string")
        byte_len = len(clean[2:]) // 2
        if byte_len > MAX_CALLDATA_BYTES:
            raise ValueError(
                f"Calldata size ({byte_len} bytes) exceeds maximum limit ({MAX_CALLDATA_BYTES} bytes)"
            )
        return clean

    @field_validator("chain_id")
    @classmethod
    def validate_chain_id(cls, v: int) -> int:
        assert v > 0, "Chain ID must be positive"
        if v not in SUPPORTED_CHAINS:
            # Allow unknown chain with warning but must be valid positive integer
            pass
        return v


class TxExecutionResponse(BaseModel):
    success: bool
    tx_hash: str | None = None
    chain_id: int
    nonce: int | None = None
    gas_used: int | None = None
    effective_gas_price_gwei: float | None = None
    status: str
    error: str | None = None
    audit_receipt: dict[str, Any] | None = None


class X402PaymentRequest(BaseModel):
    """
    HTTP 402 Autonomous Micro-Payment settlement request.
    """

    resource_url: str = Field(..., description="Target API endpoint requiring payment.")
    amount_usdc: float = Field(..., gt=0.0, description="Amount in USDC requested.")
    recipient_address: str = Field(..., description="Destination treasury address.")
    token_address: str | None = Field(
        default=None, description="Optional specific token contract."
    )

    @field_validator("recipient_address")
    @classmethod
    def validate_recipient(cls, v: str) -> str:
        if not is_address(v):
            raise ValueError(f"Invalid recipient address: {v}")
        return to_checksum_address(v)

    @field_validator("amount_usdc")
    @classmethod
    def validate_budget_limit(cls, v: float) -> float:
        assert v > 0.0, "Amount must be strictly positive"
        if v > MAX_AUTONOMOUS_PAYMENT_USDC:
            raise ValueError(
                f"Requested payment (${v:.2f}) exceeds autonomous safety threshold (${MAX_AUTONOMOUS_PAYMENT_USDC:.2f})"
            )
        return round(v, 6)


class X402PaymentResponse(BaseModel):
    success: bool
    payment_hash: str | None = None
    amount_usdc: float
    recipient: str
    auth_token: str | None = None
    unblocked_data: dict[str, Any] | None = None
    error: str | None = None


class AuditProofRequest(BaseModel):
    task_id: str | None = None
    tx_hash: str | None = None
    chain_id: int = 1


class AuditProofResponse(BaseModel):
    verified: bool
    merkle_root: str | None = None
    leaf_hash: str | None = None
    block_number: int | None = None
    confirmations: int = 0
    execution_trace: dict[str, Any] | None = None
    error: str | None = None
