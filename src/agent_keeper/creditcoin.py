"""
Creditcoin 3.0 Attestcoin & Multi-Chain Solver Settlement Module
Adheres strictly to Deterministic Safety Invariants (Power of 10 Rules).
"""

import time
from typing import Dict, Any, List, Tuple
from agent_keeper.merkle_tree import FlatMerkleTree

CREDITCOIN_CHAIN_ID = 102031
MAX_INTENTS_CAPACITY = 2048


class CreditcoinSettlementManager:
    """
    Manages Creditcoin 3.0 Attestcoin intent proofs and cross-chain solver settlements.
    Provides mathematical verification of source-chain fulfillment via cryptographic Merkle inclusion proofs.
    """
    def __init__(self):
        self._settled_intents: Dict[str, Dict[str, Any]] = {}
        self._escrow_balances: Dict[str, float] = {}

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

        self._escrow_balances[intent_id] = round(amount_ctc, 6)
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
