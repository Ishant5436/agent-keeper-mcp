"""
Unit & White-Box Tests for Creditcoin & Attestcoin Solver Settlement Module
Verifies O(log N) Merkle Proof Cryptographic Inclusion and Escrow Life Cycle.
"""

import pytest
from agent_keeper.creditcoin import CreditcoinSettlementManager, CREDITCOIN_CHAIN_ID
from agent_keeper.merkle_tree import FlatMerkleTree


def _create_mock_merkle_context():
    """Build a real Merkle tree with 4 mock intent fulfillment receipts."""
    intent_id = "intent_123"
    source_chain = "ethereum"
    tx_hash = "0x" + "a" * 64
    recipient = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    target_leaf = f"{intent_id}:{source_chain}:{tx_hash}:{recipient}"
    other_leaves = [
        "intent_120:base:0x" + "1"*64 + ":0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "intent_121:arbitrum:0x" + "2"*64 + ":0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "intent_122:optimism:0x" + "3"*64 + ":0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        target_leaf
    ]
    tree = FlatMerkleTree(other_leaves)
    proof = tree.get_proof(3)  # Index of target_leaf
    return intent_id, source_chain, tx_hash, recipient, proof, tree.root


def test_creditcoin_initialization():
    mgr = CreditcoinSettlementManager()
    assert mgr is not None
    assert CREDITCOIN_CHAIN_ID == 102031


def test_register_escrow_success():
    mgr = CreditcoinSettlementManager()
    intent_id = "intent_999"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    res = mgr.register_escrow(intent_id, solver, 100.5)
    assert res is True
    assert mgr.get_escrow_balance(intent_id) == 100.5


def test_register_escrow_zero_or_negative_amount_fails():
    mgr = CreditcoinSettlementManager()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    with pytest.raises(AssertionError):
        mgr.register_escrow("intent_fail", solver, 0.0)
    with pytest.raises(AssertionError):
        mgr.register_escrow("intent_fail", solver, -10.0)


def test_register_escrow_invalid_solver_address_fails():
    mgr = CreditcoinSettlementManager()
    with pytest.raises(AssertionError):
        mgr.register_escrow("intent_fail", "0xInvalidShort", 50.0)


def test_verify_attestcoin_proof_valid_merkle():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()

    is_valid = mgr.verify_attestcoin_proof(
        intent_id=intent_id,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert is_valid is True


def test_verify_attestcoin_proof_tampered_tx_hash():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, _, recip, proof, root = _create_mock_merkle_context()
    tampered_tx = "0x" + "f" * 64

    is_valid = mgr.verify_attestcoin_proof(
        intent_id=intent_id,
        source_chain=chain,
        source_tx_hash=tampered_tx,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert is_valid is False


def test_verify_attestcoin_proof_corrupted_sibling():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    # Corrupt sibling hash
    corrupted_proof = [("0x" + "0"*64, proof[0][1])] + proof[1:]

    is_valid = mgr.verify_attestcoin_proof(
        intent_id=intent_id,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=corrupted_proof,
        merkle_root=root
    )
    assert is_valid is False


def test_verify_attestcoin_proof_invalid_tx_hash_format():
    mgr = CreditcoinSettlementManager()
    with pytest.raises(AssertionError):
        mgr.verify_attestcoin_proof(
            "intent_123",
            "ethereum",
            "0xShortHash",
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            [],
            "0x" + "b" * 64,
        )


def test_execute_solver_reimbursement_success():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    mgr.register_escrow(intent_id, solver, 250.0)
    assert mgr.get_escrow_balance(intent_id) == 250.0

    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert receipt["success"] is True
    assert receipt["amount_ctc_released"] == 250.0
    assert receipt["chain_id"] == 102031
    assert mgr.get_escrow_balance(intent_id) == 0.0


def test_execute_solver_reimbursement_rejected_on_invalid_proof():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, _, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    tampered_tx = "0x" + "e" * 64

    mgr.register_escrow(intent_id, solver, 250.0)
    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tampered_tx,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert receipt["success"] is False
    assert "retained" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 250.0


def test_execute_solver_reimbursement_unregistered_intent_fails():
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    with pytest.raises(AssertionError):
        mgr.execute_solver_reimbursement(
            "unregistered_intent", solver, chain, tx_hash, recip, proof, root
        )


def test_escrow_fifo_capacity_bound():
    mgr = CreditcoinSettlementManager()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    for i in range(2050):
        mgr.register_escrow(f"intent_{i}", solver, 1.0)
    assert len(mgr._escrow_balances) == 2048


def test_execute_solver_reimbursement_unauthorized_solver_rejected():
    """Verify that an attacker attempting to settle a legitimate intent to their own address is rejected."""
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    legit_solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    attacker_solver = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"

    mgr.register_escrow(intent_id, legit_solver, 500.0)

    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=attacker_solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert receipt["success"] is False
    assert "Unauthorized solver" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 500.0


def test_execute_solver_reimbursement_unanchored_merkle_root_rejected():
    """Verify that a caller supplying an unanchored Merkle root is rejected when oracle roots are configured."""
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    # Register an official attested root for ethereum
    official_oracle_root = "0x" + "9" * 64
    mgr.register_trusted_root(chain, official_oracle_root)

    mgr.register_escrow(intent_id, solver, 300.0)

    # Calling with forged/unattested root (even if mathematically self-consistent) must fail
    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root
    )
    assert receipt["success"] is False
    assert "Unanchored Merkle root" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 300.0
