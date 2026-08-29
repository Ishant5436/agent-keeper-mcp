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
