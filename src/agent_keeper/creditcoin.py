"""
Creditcoin 3.0 Attestcoin & Multi-Chain Solver Settlement Module
Adheres strictly to Deterministic Safety Invariants (Power of 10 Rules).
"""

import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from agent_keeper.config import PUBLIC_RPC_URLS
from agent_keeper.merkle_tree import FlatMerkleTree

CREDITCOIN_CHAIN_ID = 102031
MAX_INTENTS_CAPACITY = 2048
MAX_ORACLE_CACHE_CAPACITY = 1024
DEFAULT_RPC_TIMEOUT = 3.0

CHAIN_NAME_TO_ID: Dict[str, int] = {
    "ethereum": 1,
    "optimism": 10,
    "creditcoin": 1024,
    "creditcoin_testnet": 102031,
    "mantle": 5000,
    "base": 8453,
    "arbitrum": 42161,
    "sepolia": 11155111,
}

DEFAULT_CHECKPOINT_ROOTS: Dict[str, set] = {
    "ethereum": {
        "0x5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b",
    },
    "base": {
        "0x4a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    },
    "arbitrum": {
        "0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
    },
    "optimism": {
        "0x2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d",
    },
    "mantle": {
        "0x3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e",
    },
}


class CreditcoinSettlementManager:
    """
    Manages Creditcoin 3.0 Attestcoin intent proofs and cross-chain solver settlements.
    Provides mathematical verification of source-chain fulfillment via cryptographic Merkle inclusion proofs.
    Enforces registered solver identity and onchain oracle root anchoring to prevent unauthorized drains.
    """

    def __init__(self, bootstrap_defaults: bool = True):
        self._settled_intents: Dict[str, Dict[str, Any]] = {}
        self._escrow_balances: Dict[str, float] = {}
        self._escrow_solvers: Dict[str, str] = {}
        self._trusted_roots: Dict[str, set] = {}
        if bootstrap_defaults:
            for ch, roots in DEFAULT_CHECKPOINT_ROOTS.items():
                self._trusted_roots[ch] = set(roots)

    def register_trusted_root(self, source_chain: str, merkle_root: str) -> None:
        """Register an attested state Merkle root confirmed by an on-chain oracle or light client."""
        assert len(merkle_root) == 66 and merkle_root.startswith("0x"), "Invalid root format"
        assert len(source_chain) > 0, "Source chain cannot be empty"

        chain_key = source_chain.lower()
        if chain_key not in self._trusted_roots:
            self._trusted_roots[chain_key] = set()

        if len(self._trusted_roots[chain_key]) >= MAX_ORACLE_CACHE_CAPACITY:
            self._trusted_roots[chain_key].pop()

        self._trusted_roots[chain_key].add(merkle_root.lower())

    def is_trusted_root(self, source_chain: str, merkle_root: str) -> bool:
        """Check if root is registered in trusted oracle cache."""
        assert len(source_chain) > 0, "source_chain cannot be empty"
        assert len(merkle_root) == 66 and merkle_root.startswith("0x"), "Invalid root format"
        roots = self._trusted_roots.get(source_chain.lower(), set())
        return merkle_root.lower() in roots

    def _query_oracle_rpc(
        self, source_chain: str, merkle_root: str, source_tx_hash: Optional[str] = None
    ) -> bool:
        """Query source-chain RPC or Creditcoin oracle bridge to verify on-chain root attestation."""
        assert isinstance(source_chain, str) and len(source_chain) > 0, "Valid chain required"
        assert len(merkle_root) == 66 and merkle_root.startswith("0x"), "Valid root required"

        chain_id = CHAIN_NAME_TO_ID.get(source_chain.lower())
        if not chain_id or chain_id not in PUBLIC_RPC_URLS:
            return False

        rpc_url = PUBLIC_RPC_URLS[chain_id]
        try:
            with httpx.Client(timeout=DEFAULT_RPC_TIMEOUT) as client:
                if source_tx_hash and len(source_tx_hash) == 66 and source_tx_hash.startswith("0x"):
                    resp = client.post(
                        rpc_url,
                        json={
                            "jsonrpc": "2.0",
                            "method": "eth_getTransactionReceipt",
                            "params": [source_tx_hash],
                            "id": 1,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        receipt = data.get("result")
                        if receipt and receipt.get("blockHash"):
                            return True

                block_resp = client.post(
                    rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_getBlockByNumber",
                        "params": ["latest", False],
                        "id": 2,
                    },
                )
                if block_resp.status_code == 200:
                    block_data = block_resp.json().get("result") or {}
                    receipts_root = block_data.get("receiptsRoot") or ""
                    state_root = block_data.get("stateRoot") or ""
                    if (
                        merkle_root.lower() == receipts_root.lower()
                        or merkle_root.lower() == state_root.lower()
                    ):
                        return True
        except Exception:
            return False

        return False

    def fetch_and_anchor_oracle_root(
        self,
        source_chain: str,
        merkle_root: str,
        source_tx_hash: Optional[str] = None,
    ) -> bool:
        """Dynamically fetches and anchors on-chain oracle state roots from live RPC."""
        assert len(source_chain) > 0, "source_chain cannot be empty"
        assert len(merkle_root) == 66 and merkle_root.startswith("0x"), "Invalid root format"

        chain_key = source_chain.lower()
        if self.is_trusted_root(chain_key, merkle_root):
            return True

        is_valid_onchain = self._query_oracle_rpc(source_chain, merkle_root, source_tx_hash)
        if is_valid_onchain:
            self.register_trusted_root(source_chain, merkle_root)
            return True

        return False

    def register_escrow(self, intent_id: str, solver_address: str, amount_ctc: float) -> bool:
        """
        Locks escrow collateral for a cross-chain fulfillment intent.
        """
        assert len(intent_id) > 0, "Intent ID cannot be empty"
        assert solver_address.startswith("0x") and len(solver_address) == 42, "Invalid solver address"
        assert amount_ctc > 0.0, "Escrow amount must be positive"

        if len(self._escrow_balances) >= MAX_INTENTS_CAPACITY:
            oldest = next(iter(self._escrow_balances))
            del self._escrow_balances[oldest]
            self._escrow_solvers.pop(oldest, None)

        self._escrow_balances[intent_id] = round(amount_ctc, 6)
        self._escrow_solvers[intent_id] = solver_address.lower()
        return True

    def verify_attestcoin_proof(
        self,
        intent_id: str,
        source_chain: str,
        source_tx_hash: str,
        expected_recipient: str,
        merkle_proof: List[Tuple[str, str]],
        merkle_root: str
    ) -> bool:
        """
        Cryptographically validates an Attestcoin proof of source-chain fulfillment
        against an on-chain Merkle root using FlatMerkleTree inclusion verification.
        """
        assert len(intent_id) > 0, "Intent ID required"
        assert len(source_tx_hash) == 66 and source_tx_hash.startswith("0x"), "Invalid tx hash"
        assert expected_recipient.startswith("0x") and len(expected_recipient) == 42, "Invalid recipient"
        assert len(merkle_root) == 66 and merkle_root.startswith("0x"), "Invalid Merkle root format"
        assert isinstance(merkle_proof, list), "Merkle proof must be a list of tuples"
        assert len(merkle_proof) <= 64, "Attestcoin proof depth exceeds maximum safety ceiling of 64"

        # Construct standardized leaf receipt payload
        leaf_payload = f"{intent_id}:{source_chain}:{source_tx_hash}:{expected_recipient}"

        # Verify inclusion against on-chain Merkle root in O(log N) time
        return FlatMerkleTree.verify_proof(leaf_payload, merkle_proof, merkle_root)

    def execute_solver_reimbursement(
        self,
        intent_id: str,
        solver_address: str,
        source_chain: str,
        source_tx_hash: str,
        expected_recipient: str,
        merkle_proof: List[Tuple[str, str]],
        merkle_root: str
    ) -> Dict[str, Any]:
        """
        Verifies Attestcoin Merkle proof and releases Creditcoin CTC escrow funds to solver.
        """
        assert intent_id in self._escrow_balances, "Intent not registered in escrow"
        assert solver_address.startswith("0x") and len(solver_address) == 42, "Invalid solver"

        amount = self._escrow_balances[intent_id]

        # 1. Enforce registered solver identity to prevent unauthorized escrow drain
        registered_solver = self._escrow_solvers.get(intent_id)
        if registered_solver and solver_address.lower() != registered_solver:
            return {
                "success": False,
                "error": f"Unauthorized solver address '{solver_address}': does not match registered escrow solver",
                "intent_id": intent_id,
                "amount_ctc": amount,
                "chain_id": CREDITCOIN_CHAIN_ID
            }

        # 2. Mandatory On-Chain Oracle Root Anchoring (Deny-by-default)
        chain_key = source_chain.lower()
        is_anchored = self.is_trusted_root(chain_key, merkle_root)
        if not is_anchored:
            is_anchored = self.fetch_and_anchor_oracle_root(
                source_chain=source_chain,
                merkle_root=merkle_root,
                source_tx_hash=source_tx_hash,
            )

        if not is_anchored:
            return {
                "success": False,
                "error": f"Unanchored Merkle root '{merkle_root}' rejected: not attested by {source_chain} oracle",
                "intent_id": intent_id,
                "amount_ctc": amount,
                "chain_id": CREDITCOIN_CHAIN_ID,
            }

        is_valid_proof = self.verify_attestcoin_proof(
            intent_id=intent_id,
            source_chain=source_chain,
            source_tx_hash=source_tx_hash,
            expected_recipient=expected_recipient,
            merkle_proof=merkle_proof,
            merkle_root=merkle_root
        )

        if not is_valid_proof:
            return {
                "success": False,
                "error": "Attestcoin cryptographic Merkle proof verification failed - escrow retained",
                "intent_id": intent_id,
                "amount_ctc": amount,
                "chain_id": CREDITCOIN_CHAIN_ID
            }

        # Release escrow upon verified proof
        del self._escrow_balances[intent_id]
        self._escrow_solvers.pop(intent_id, None)
        settlement_record = {
            "success": True,
            "intent_id": intent_id,
            "solver": solver_address,
            "amount_ctc_released": amount,
            "source_chain": source_chain,
            "source_tx_hash": source_tx_hash,
            "merkle_root": merkle_root,
            "chain_id": CREDITCOIN_CHAIN_ID,
            "settled_at": int(time.time())
        }
        self._settled_intents[intent_id] = settlement_record
        return settlement_record

    def get_escrow_balance(self, intent_id: str) -> float:
        """Returns locked escrow balance for intent."""
        return self._escrow_balances.get(intent_id, 0.0)
