"""
Test Suite for FastMCP Server Integration
"""

from agent_keeper.server import (
    keeper_agent_balance,
    keeper_audit_verify,
    keeper_execute_tx,
    keeper_x402_settle,
)


def test_mcp_execute_tx_tool():
    res = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0xa9059cbb",
        value_wei=0,
        chain_id=8453,
    )
    assert res["success"] is True
    assert res["tx_hash"].startswith("0x")
    assert res["chain_id"] == 8453


def test_mcp_x402_settle_tool():
    res = keeper_x402_settle(
        resource_url="https://api.market-oracle.ai/data",
        amount_usdc=0.25,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    assert res["success"] is True
    assert res["amount_usdc"] == 0.25
    assert "auth_token" in res


def test_mcp_audit_verify_tool():
    res = keeper_audit_verify(
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        chain_id=1,
    )
    assert res["verified"] is True
    assert res["confirmations"] >= 12


def test_mcp_agent_balance_tool():
    res = keeper_agent_balance()
    assert res["success"] is True
    assert "balances" in res
    assert "Base Mainnet" in str(res["balances"])


def test_mcp_creditcoin_settle_tool():
    from agent_keeper.server import keeper_creditcoin_settle, _creditcoin_manager
    from agent_keeper.merkle_tree import FlatMerkleTree

    intent_id = "mcp_intent_42"
    chain = "arbitrum"
    tx_hash = "0x" + "c" * 64
    recipient = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    leaf = f"{intent_id}:{chain}:{tx_hash}:{recipient}"
    tree = FlatMerkleTree([leaf, "dummy_leaf_2"])
    proof = tree.get_proof(0)

    _creditcoin_manager.register_escrow(intent_id, solver, 500.0)
    _creditcoin_manager.register_trusted_root(chain, tree.root)

    res = keeper_creditcoin_settle(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recipient,
        merkle_proof=proof,
        merkle_root=tree.root,
    )
    assert res["success"] is True
    assert res["amount_ctc_released"] == 500.0
    assert res["chain_id"] == 102031


def test_mcp_creditcoin_settle_tool_dynamic_oracle_anchoring_system():
    """
    System Test: FastMCP tool keeper_creditcoin_settle dynamically queries onchain oracle
    and settles escrow WITHOUT manual pre-registration of trusted roots.
    """
    import json
    import httpx
    from agent_keeper.server import keeper_creditcoin_settle, _creditcoin_manager
    from agent_keeper.merkle_tree import FlatMerkleTree

    intent_id = "mcp_intent_dynamic_99"
    chain = "base"
    tx_hash = "0x" + "7" * 64
    recipient = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    leaf = f"{intent_id}:{chain}:{tx_hash}:{recipient}"
    tree = FlatMerkleTree([leaf, "sibling_leaf"])
    proof = tree.get_proof(0)

    # 1. Register escrow ONLY. DO NOT register root!
    _creditcoin_manager.register_escrow(intent_id, solver, 750.0)

    # 2. Wire native MockTransport into production manager
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content.decode("utf-8"))
        method = data.get("method")
        if method == "eth_getTransactionReceipt":
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "result": {"status": "0x1", "blockHash": "0x" + "8" * 64},
                "id": data.get("id"),
            })
        elif method == "eth_getBlockByHash":
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "result": {"receiptsRoot": tree.root, "stateRoot": "0x0", "transactionsRoot": "0x0"},
                "id": data.get("id"),
            })
        return httpx.Response(404, json={"error": "Not found"})

    _creditcoin_manager._transport = httpx.MockTransport(handler)

    res = keeper_creditcoin_settle(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recipient,
        merkle_proof=proof,
        merkle_root=tree.root,
    )
    assert res["success"] is True
    assert res["amount_ctc_released"] == 750.0
    assert _creditcoin_manager.get_escrow_balance(intent_id) == 0.0
    assert _creditcoin_manager.is_trusted_root(chain, tree.root) is True


def test_mcp_creditcoin_settle_tool_adversarial_unanchored_bypass_rejected_system():
    """
    System Test: Attacker attempts to settle via FastMCP tool using unrelated transaction hash
    and fabricated Merkle root. Verify the tool rejects settlement and retains escrow.
    """
    import json
    import httpx
    from agent_keeper.server import keeper_creditcoin_settle, _creditcoin_manager
    from agent_keeper.merkle_tree import FlatMerkleTree

    intent_id = "mcp_intent_adversarial_00"
    chain = "arbitrum"
    tx_hash = "0x" + "a" * 64
    recipient = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    solver = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    leaf = f"{intent_id}:{chain}:{tx_hash}:{recipient}"
    tree = FlatMerkleTree([leaf, "sibling_leaf"])
    proof = tree.get_proof(0)

    _creditcoin_manager.register_escrow(intent_id, solver, 999.0)

    # RPC returns valid receipt for tx_hash, but the block's roots do NOT match tree.root!
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content.decode("utf-8"))
        method = data.get("method")
        if method == "eth_getTransactionReceipt":
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "result": {"status": "0x1", "blockHash": "0x" + "e" * 64},
                "id": data.get("id"),
            })
        elif method == "eth_getBlockByHash":
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "result": {"receiptsRoot": "0x" + "1" * 64, "stateRoot": "0x" + "2" * 64},
                "id": data.get("id"),
            })
        return httpx.Response(404, json={"error": "Not found"})

    _creditcoin_manager._transport = httpx.MockTransport(handler)

    res = keeper_creditcoin_settle(
        intent_id=intent_id,
        solver_address=solver,
        source_chain=chain,
        source_tx_hash=tx_hash,
        expected_recipient=recipient,
        merkle_proof=proof,
        merkle_root=tree.root,
    )
    assert res["success"] is False
    assert "Unanchored Merkle root" in res["error"]
    assert _creditcoin_manager.get_escrow_balance(intent_id) == 999.0
