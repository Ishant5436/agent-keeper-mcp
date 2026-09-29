"""
Autonomous HTTP 402 (x402) Micro-Payment Settlement Manager
Enables AI Agents to autonomously inspect, sign, and settle onchain micro-payments
using authentic EIP-712 structured payment permits and cumulative safety caps.
"""

import os
import secrets
import time

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import is_checksum_address, keccak

from agent_keeper.config import AGENT_PRIVATE_KEY, MAX_AUTONOMOUS_PAYMENT_USDC
from agent_keeper.schemas import X402PaymentRequest, X402PaymentResponse


ARC_CHAIN_ID = 5042
VERIFIER_ENV_VAR = "ARC_X402_VERIFIER"
ZERO_ADDRESS = "0x" + "00" * 20
PERMIT_TTL_SECONDS = 300
# Former hardcoded placeholder: no contract was ever deployed there.
REJECTED_LEGACY_PLACEHOLDER = "0x4020000000000000000000000000000000000402"


class VerifierNotConfiguredError(RuntimeError):
    """Raised when no valid X402Receipt verifier address is configured."""


def resolve_verifier(chain_id: int) -> str:
    """Return the checksum-validated X402Receipt address, or fail closed.

    There is deliberately no default: a permit signed against an address with
    no contract behind it can never be redeemed.
    """
    if chain_id != ARC_CHAIN_ID:
        raise VerifierNotConfiguredError(
            f"No X402Receipt verifier is configured for chain {chain_id}; "
            f"only Arc Mainnet ({ARC_CHAIN_ID}) is supported via {VERIFIER_ENV_VAR}."
        )
    raw = os.environ.get(VERIFIER_ENV_VAR, "").strip()
    if not raw:
        raise VerifierNotConfiguredError(
            f"{VERIFIER_ENV_VAR} is not set. Deploy contracts/X402Receipt.sol to Arc "
            "Mainnet (scripts/deploy_arc_verifier.py --broadcast) and set "
            f"{VERIFIER_ENV_VAR} to the deployed EIP-55 checksum address."
        )
    if not is_checksum_address(raw) or raw in (ZERO_ADDRESS, REJECTED_LEGACY_PLACEHOLDER):
        raise VerifierNotConfiguredError(
            f"{VERIFIER_ENV_VAR} must be a deployed, non-zero EIP-55 checksum address "
            f"(not the retired placeholder), got '{raw}'."
        )
    return raw


def build_permit_typed_data(
    chain_id: int,
    verifying_contract: str,
    payer: str,
    payee: str,
    amount: int,
    nonce: int,
    deadline: int,
) -> dict:
    """EIP-712 payload matching X402Receipt.settle(payer, payee, amount, nonce, deadline, sig)."""
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Permit": [
                {"name": "payer", "type": "address"},
                {"name": "payee", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "primaryType": "Permit",
        "domain": {
            "name": "KeeperHub x402 Gateway",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": verifying_contract,
        },
        "message": {
            "payer": payer,
            "payee": payee,
            "amount": amount,
            "nonce": nonce,
            "deadline": deadline,
        },
    }


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
        """Sign an EIP-712 permit redeemable via X402Receipt.settle()."""
        chain_id = getattr(req, "chain_id", ARC_CHAIN_ID)
        typed_data = build_permit_typed_data(
            chain_id=chain_id,
            verifying_contract=resolve_verifier(chain_id),
            payer=self.signer_address,
            payee=req.recipient_address,
            amount=int(round(req.amount_usdc * 10**6)),
            nonce=secrets.randbits(256),
            deadline=timestamp + PERMIT_TTL_SECONDS,
        )
        signable = encode_typed_data(full_message=typed_data)
        signed = Account.sign_message(signable, private_key=self._private_key)
        return "0x" + signed.signature.hex()

    def settle_payment(self, req: X402PaymentRequest) -> X402PaymentResponse:
        """Autonomously evaluate and settle HTTP 402 challenge within safety limits."""
        assert req.amount_usdc > 0.0, "Payment amount must be positive"
        assert req.recipient_address is not None, "Recipient address required"

        # Fail closed before spending any budget if no verifier is configured.
        try:
            resolve_verifier(getattr(req, "chain_id", ARC_CHAIN_ID))
        except VerifierNotConfiguredError as exc:
            return X402PaymentResponse(
                success=False,
                amount_usdc=req.amount_usdc,
                recipient=req.recipient_address,
                error=str(exc),
            )

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

        self.total_spent = round(self.total_spent + req.amount_usdc, 6)
        receipt = X402PaymentResponse(
            success=True,
            payment_hash=payment_hash,
            amount_usdc=req.amount_usdc,
            recipient=req.recipient_address,
            auth_token=f"Bearer x402_{payment_hash[:16]}",
            signature=signature,
            unblocked_data={
                "status": "resource_unlocked",
                "resource": req.resource_url,
            },
        )
        self._settlement_history.append(receipt)
        return receipt
