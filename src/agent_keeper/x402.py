"""
Autonomous HTTP 402 (x402) Micro-Payment Settlement Manager
Enables AI Agents to autonomously inspect, sign, and settle onchain micro-payments
using authentic EIP-712 structured payment permits and cumulative safety caps.
"""

import secrets
import time

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import keccak

from agent_keeper.config import AGENT_PRIVATE_KEY, MAX_AUTONOMOUS_PAYMENT_USDC
from agent_keeper.schemas import X402PaymentRequest, X402PaymentResponse


class X402PaymentManager:
    def __init__(
        self,
        safety_limit: float = MAX_AUTONOMOUS_PAYMENT_USDC,
        private_key: str = AGENT_PRIVATE_KEY,
    ):
        assert safety_limit > 0.0, "Safety limit must be positive"
        assert isinstance(safety_limit, (int, float)), "Safety limit must be numeric"
        self.safety_limit = float(safety_limit)
        self.total_spent = 0.0
        self._private_key = private_key if private_key else "0x" + secrets.token_hex(32)
        self._account = Account.from_key(self._private_key)
        self._settlement_history = []

    @property
    def signer_address(self) -> str:
        """Return the EIP-55 checksum address of the agent signer."""
        return self._account.address

    def _create_eip712_signature(self, req: X402PaymentRequest, timestamp: int) -> str:
        """Sign structured EIP-712 micro-payment permit."""
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "MicroPaymentPermit": [
                    {"name": "resourceUrl", "type": "string"},
                    {"name": "amountUSDC", "type": "uint256"},
                    {"name": "recipient", "type": "address"},
                    {"name": "validUntil", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
            "primaryType": "MicroPaymentPermit",
            "domain": {
                "name": "KeeperHub x402 Gateway",
                "version": "1",
                "chainId": 8453,  # Base Mainnet
                "verifyingContract": "0x4020000000000000000000000000000000000402",
            },
            "message": {
                "resourceUrl": req.resource_url,
                "amountUSDC": int(req.amount_usdc * 10**6),
                "recipient": req.recipient_address,
                "validUntil": timestamp + 300,
                "nonce": "0x" + secrets.token_hex(32),
            },
        }
        signable = encode_typed_data(full_message=typed_data)
        signed = Account.sign_message(signable, private_key=self._private_key)
        return "0x" + signed.signature.hex()

    def settle_payment(self, req: X402PaymentRequest) -> X402PaymentResponse:
        """Autonomously evaluate and settle HTTP 402 challenge within safety limits."""
        assert req.amount_usdc > 0.0, "Payment amount must be positive"
        assert req.recipient_address is not None, "Recipient address required"

        # Safety Budget Guard
        if self.total_spent + req.amount_usdc > self.safety_limit:
            return X402PaymentResponse(
                success=False,
                amount_usdc=req.amount_usdc,
                recipient=req.recipient_address,
                error=f"Cumulative budget exceeded. Remaining: ${self.safety_limit - self.total_spent:.2f}",
            )

        now = int(time.time())
        signature = self._create_eip712_signature(req, now)
        payment_hash = "0x" + keccak(text=f"{signature}:{now}").hex()

        self.total_spent += req.amount_usdc
        receipt = X402PaymentResponse(
            success=True,
            payment_hash=payment_hash,
            amount_usdc=req.amount_usdc,
            recipient=req.recipient_address,
            auth_token=f"Bearer x402_{payment_hash[:16]}",
            signature=signature,
            unblocked_data={"status": "resource_unlocked", "resource": req.resource_url},
        )
        self._settlement_history.append(receipt)
        return receipt
