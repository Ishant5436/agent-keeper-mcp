"""
Unit & White-Box Tests for Creditcoin & Attestcoin Solver Settlement Module
"""

import pytest
from agent_keeper.creditcoin import CreditcoinSettlementManager, CREDITCOIN_CHAIN_ID

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

def test_verify_attestcoin_proof_valid():
    mgr = CreditcoinSettlementManager()
    intent_id = "intent_123"
    source_chain = "ethereum"
    tx_hash = "0x" + "a" * 64
    recipient = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    root = "0x" + "b" * 64
    
    is_valid = mgr.verify_attestcoin_proof(intent_id, source_chain, tx_hash, recipient, root)
    assert is_valid is True

def test_verify_attestcoin_proof_invalid_tx_hash():
    mgr = CreditcoinSettlementManager()
    with pytest.raises(AssertionError):
        mgr.verify_attestcoin_proof("intent_123", "ethereum", "0xShortHash", "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "0x" + "b" * 64)

def test_execute_solver_reimbursement_success():
    mgr = CreditcoinSettlementManager()
    intent_id = "intent_888"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    mgr.register_escrow(intent_id, solver, 250.0)
    
    receipt = mgr.execute_solver_reimbursement(intent_id, solver, attestcoin_proof_valid=True)
    assert receipt["success"] is True
    assert receipt["amount_ctc_released"] == 250.0
    assert receipt["chain_id"] == 102031
    assert mgr.get_escrow_balance(intent_id) == 0.0

def test_execute_solver_reimbursement_rejected_on_invalid_proof():
    mgr = CreditcoinSettlementManager()
    intent_id = "intent_777"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    mgr.register_escrow(intent_id, solver, 50.0)
    
    receipt = mgr.execute_solver_reimbursement(intent_id, solver, attestcoin_proof_valid=False)
    assert receipt["success"] is False
    assert "retained" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 50.0

def test_execute_solver_reimbursement_unregistered_intent_fails():
    mgr = CreditcoinSettlementManager()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    with pytest.raises(AssertionError):
        mgr.execute_solver_reimbursement("non_existent_intent", solver, True)

def test_escrow_fifo_capacity_bound():
    mgr = CreditcoinSettlementManager()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    for i in range(2050):
        mgr.register_escrow(f"intent_{i}", solver, 1.0)
    
    # FIFO pruned oldest 2 entries
    assert mgr.get_escrow_balance("intent_0") == 0.0
    assert mgr.get_escrow_balance("intent_1") == 0.0
    assert mgr.get_escrow_balance("intent_2049") == 1.0
