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
