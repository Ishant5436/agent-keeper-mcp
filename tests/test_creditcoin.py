"""
Unit & White-Box Tests for Creditcoin & Attestcoin Solver Settlement Module
Verifies O(log N) Merkle Proof Cryptographic Inclusion and Escrow Life Cycle.
"""

import json
import httpx
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

    mgr.register_trusted_root(chain, root)
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

    mgr.register_trusted_root(chain, root)
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

    mgr.register_trusted_root(chain, root)
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


def test_execute_solver_reimbursement_unanchored_root_rejected_on_fresh_manager():
    """Verify that an unanchored root submitted on a fresh unconfigured chain is rejected (deny-by-default)."""
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False)
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    mgr.register_escrow(intent_id, solver, 400.0)

    # Calling with unanchored root when chain has zero registered roots must fail
    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain="mantle",
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root,
    )
    assert receipt["success"] is False
    assert "Unanchored Merkle root" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 400.0


def _make_rpc_transport(
    receipt_result=None,
    block_result=None,
    latest_block_result=None,
    receipt_status_code=200,
    block_status_code=200,
    call_log=None,
):
    """Factory creating an in-memory httpx.MockTransport simulating EVM JSON-RPC responses."""
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content.decode("utf-8"))
        method = data.get("method")
        if call_log is not None:
            call_log.append((method, data.get("params")))

        if method == "eth_getTransactionReceipt":
            if receipt_status_code != 200:
                return httpx.Response(receipt_status_code, json={"error": "RPC Error"})
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": receipt_result, "id": data.get("id")})
        elif method == "eth_getBlockByHash":
            if block_status_code != 200:
                return httpx.Response(block_status_code, json={"error": "Block Error"})
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": block_result, "id": data.get("id")})
        elif method == "eth_getBlockByNumber":
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": latest_block_result, "id": data.get("id")})
        return httpx.Response(404, json={"error": f"Unknown method: {method}"})

    return httpx.MockTransport(handler)


# ==============================================================================
# 1. DIRECT UNIT TESTS FOR _query_oracle_rpc & HELPERS
# ==============================================================================

def test_query_oracle_rpc_matching_receipts_root_direct():
    """Unit: _query_oracle_rpc directly returns True when root matches block receiptsRoot."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={"receiptsRoot": root, "stateRoot": "0x" + "0" * 64, "transactionsRoot": "0x" + "0" * 64},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is True


def test_query_oracle_rpc_matching_state_root_direct():
    """Unit: _query_oracle_rpc directly returns True when root matches block stateRoot."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={"receiptsRoot": "0x" + "0" * 64, "stateRoot": root, "transactionsRoot": "0x" + "0" * 64},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is True


def test_query_oracle_rpc_matching_transactions_root_direct():
    """Unit: _query_oracle_rpc directly returns True when root matches block transactionsRoot."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={"receiptsRoot": "0x" + "0" * 64, "stateRoot": "0x" + "0" * 64, "transactionsRoot": root},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is True


def test_query_oracle_rpc_mismatched_root_direct():
    """Unit: _query_oracle_rpc returns False when block roots do not match candidate Merkle root."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={
            "receiptsRoot": "0x" + "1" * 64,
            "stateRoot": "0x" + "2" * 64,
            "transactionsRoot": "0x" + "3" * 64,
        },
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_reverted_tx_receipt_direct():
    """Unit: _query_oracle_rpc returns False when transaction status is 0x0 (reverted)."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x0", "blockHash": "0x" + "b" * 64},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_missing_receipt_direct():
    """Unit: _query_oracle_rpc returns False when transaction receipt is null."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(receipt_result=None)
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_missing_block_direct():
    """Unit: _query_oracle_rpc returns False when block is not found."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result=None,
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_http_500_error_direct():
    """Unit: _query_oracle_rpc gracefully returns False on HTTP 500 error."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(receipt_status_code=500)
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_transport_exception_direct():
    """Unit: _query_oracle_rpc gracefully returns False on transport network exceptions."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()

    def error_handler(request: httpx.Request):
        raise httpx.ConnectTimeout("Connection to RPC timed out")

    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=httpx.MockTransport(error_handler))
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_malformed_tx_hash_direct():
    """Unit: _query_oracle_rpc returns False for invalid or non-66-character tx hash strings."""
    _, chain, _, _, _, root = _create_mock_merkle_context()
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash="0xshort") is False
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash="not_hex") is False


def test_query_oracle_rpc_unsupported_chain_direct():
    """Unit: _query_oracle_rpc returns False for unregistered source chains."""
    _, _, tx_hash, _, _, root = _create_mock_merkle_context()
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False)
    assert mgr._query_oracle_rpc("solana", root, source_tx_hash=tx_hash) is False


def test_query_oracle_rpc_no_tx_hash_latest_block_matching():
    """Unit: when source_tx_hash is None, _query_oracle_rpc verifies against latest block."""
    _, chain, _, _, _, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        latest_block_result={"receiptsRoot": root, "stateRoot": "0x" + "0" * 64, "transactionsRoot": "0x" + "0" * 64}
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=None) is True


def test_query_oracle_rpc_no_tx_hash_latest_block_mismatch():
    """Unit: when source_tx_hash is None and latest block doesn't match, returns False."""
    _, chain, _, _, _, root = _create_mock_merkle_context()
    transport = _make_rpc_transport(
        latest_block_result={"receiptsRoot": "0x" + "1" * 64, "stateRoot": "0x" + "2" * 64}
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    assert mgr._query_oracle_rpc(chain, root, source_tx_hash=None) is False


# ==============================================================================
# 2. WHITE-BOX BRANCH COVERAGE & SUBROUTINE TESTS
# ==============================================================================

def test_whitebox_oracle_branch_with_tx_hash_never_calls_latest_block():
    """White-box: supplying source_tx_hash takes tx branch and NEVER calls eth_getBlockByNumber."""
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    call_log = []
    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={"receiptsRoot": root},
        call_log=call_log,
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    res = mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash)

    assert res is True
    methods_called = [item[0] for item in call_log]
    assert methods_called == ["eth_getTransactionReceipt", "eth_getBlockByHash"]
    assert "eth_getBlockByNumber" not in methods_called


def test_whitebox_oracle_branch_without_tx_hash_calls_only_latest_block():
    """White-box: omitting source_tx_hash takes latest branch and NEVER calls receipt/blockByHash."""
    _, chain, _, _, _, root = _create_mock_merkle_context()
    call_log = []
    transport = _make_rpc_transport(
        latest_block_result={"receiptsRoot": root},
        call_log=call_log,
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    res = mgr._query_oracle_rpc(chain, root, source_tx_hash=None)

    assert res is True
    methods_called = [item[0] for item in call_log]
    assert methods_called == ["eth_getBlockByNumber"]
    assert "eth_getTransactionReceipt" not in methods_called
    assert "eth_getBlockByHash" not in methods_called


def test_whitebox_oracle_reverted_tx_halts_early_without_fetching_block():
    """White-box: reverted tx halts immediately and NEVER calls eth_getBlockByHash."""
    _, chain, tx_hash, _, _, root = _create_mock_merkle_context()
    call_log = []
    transport = _make_rpc_transport(
        receipt_result={"status": "0x0", "blockHash": "0x" + "b" * 64},
        call_log=call_log,
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    res = mgr._query_oracle_rpc(chain, root, source_tx_hash=tx_hash)

    assert res is False
    methods_called = [item[0] for item in call_log]
    assert methods_called == ["eth_getTransactionReceipt"]
    assert "eth_getBlockByHash" not in methods_called


def test_whitebox_block_contains_root_subroutine():
    """White-box: verify _block_contains_root handles case-insensitivity, missing keys, and bad types."""
    root = "0x" + "a" * 64
    upper_root = "0X" + "A" * 64

    assert CreditcoinSettlementManager._block_contains_root({"receiptsRoot": root}, root) is True
    assert CreditcoinSettlementManager._block_contains_root({"receiptsRoot": upper_root}, root) is True
    assert CreditcoinSettlementManager._block_contains_root({"stateRoot": root}, root) is True
    assert CreditcoinSettlementManager._block_contains_root({"transactionsRoot": root}, root) is True
    assert CreditcoinSettlementManager._block_contains_root({}, root) is False
    assert CreditcoinSettlementManager._block_contains_root({"receiptsRoot": "0x" + "0" * 64}, root) is False

    with pytest.raises(AssertionError):
        CreditcoinSettlementManager._block_contains_root("not_a_dict", root)
    with pytest.raises(AssertionError):
        CreditcoinSettlementManager._block_contains_root({}, "not_hex")


def test_whitebox_fetch_block_by_tx_subroutine():
    """White-box: verify _fetch_block_by_tx returns None on status errors or missing blocks."""
    tx_hash = "0x" + "c" * 64
    rpc_url = "https://fake.rpc"

    # 1. Missing receipt returns None
    with httpx.Client(transport=_make_rpc_transport(receipt_result=None)) as client:
        assert CreditcoinSettlementManager._fetch_block_by_tx(client, rpc_url, tx_hash) is None

    # 2. Reverted status returns None
    with httpx.Client(transport=_make_rpc_transport(receipt_result={"status": "0x0", "blockHash": "0x123"})) as client:
        assert CreditcoinSettlementManager._fetch_block_by_tx(client, rpc_url, tx_hash) is None

    # 3. Successful block fetch returns block dict
    block_dict = {"receiptsRoot": "0x" + "d" * 64}
    with httpx.Client(transport=_make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x123"},
        block_result=block_dict,
    )) as client:
        res = CreditcoinSettlementManager._fetch_block_by_tx(client, rpc_url, tx_hash)
        assert res == block_dict


# ==============================================================================
# 3. BLACK-BOX TESTS (REAL TRANSPORT, ZERO MONKEYPATCHING)
# ==============================================================================

def test_execute_solver_reimbursement_dynamic_anchoring_success():
    """
    Black-box: Real execute_solver_reimbursement with native MockTransport.
    NO monkeypatching of _query_oracle_rpc! Genuine verification release.
    """
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "d" * 64},
        block_result={"receiptsRoot": root, "stateRoot": "0x" + "e" * 64, "transactionsRoot": "0x" + "f" * 64},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    mgr.register_escrow(intent_id, solver, 850.0)

    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root,
    )
    assert receipt["success"] is True
    assert receipt["amount_ctc_released"] == 850.0
    assert mgr.get_escrow_balance(intent_id) == 0.0
    assert mgr.is_trusted_root(chain, root) is True


def test_execute_solver_reimbursement_mismatched_merkle_root_rejected():
    """
    Black-box: Attacker submits genuine tx_hash but mismatched Merkle root.
    NO monkeypatching! Transport feeds real receipt, settlement strictly rejected.
    """
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    transport = _make_rpc_transport(
        receipt_result={"status": "0x1", "blockHash": "0x" + "b" * 64},
        block_result={
            "receiptsRoot": "0x" + "1" * 64,
            "stateRoot": "0x" + "2" * 64,
            "transactionsRoot": "0x" + "3" * 64,
        },
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    mgr.register_escrow(intent_id, solver, 1000.0)

    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root,
    )
    assert receipt["success"] is False
    assert "Unanchored Merkle root" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 1000.0
    assert mgr.is_trusted_root(chain, root) is False


def test_execute_solver_reimbursement_reverted_tx_rejected():
    """
    Black-box: Reverted transaction receipt on source chain rejects settlement.
    """
    intent_id, chain, tx_hash, recip, proof, root = _create_mock_merkle_context()
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    transport = _make_rpc_transport(
        receipt_result={"status": "0x0", "blockHash": "0x" + "a" * 64},
    )
    mgr = CreditcoinSettlementManager(bootstrap_defaults=False, transport=transport)
    mgr.register_escrow(intent_id, solver, 500.0)

    receipt = mgr.execute_solver_reimbursement(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=root,
    )
    assert receipt["success"] is False
    assert "Unanchored Merkle root" in receipt["error"]
    assert mgr.get_escrow_balance(intent_id) == 500.0


def test_verify_attestcoin_proof_depth_exceeds_64_fails():
    """Verify that a Merkle proof exceeding maximum tree depth of 64 triggers invariant failure."""
    mgr = CreditcoinSettlementManager()
    intent_id, chain, tx_hash, recip, _, root = _create_mock_merkle_context()
    oversized_proof = [("0x" + "1" * 64, "left") for _ in range(65)]

    with pytest.raises(AssertionError) as exc_info:
        mgr.verify_attestcoin_proof(
            intent_id=intent_id,
            source_chain=chain,
            source_tx_hash=tx_hash,
            expected_recipient=recip,
            merkle_proof=oversized_proof,
            merkle_root=root,
        )
    assert "64" in str(exc_info.value)
