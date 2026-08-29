"""
Test Suite for KeeperHub Upstream FastMCP Plugin
"""

from keeper_mcp_plugin import execute_onchain_task


def test_dynamic_tx_execution():
    res1 = execute_onchain_task(
        to_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata="0xa9059cbb",
        chain_id=8453,
    )
    res2 = execute_onchain_task(
        to_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        calldata="0x123456",
        chain_id=1,
    )
    assert res1["success"] is True
    assert res2["success"] is True
    # Verify hashes are dynamic and non-identical
    assert res1["tx_hash"] != res2["tx_hash"]
    assert res1["chain_id"] == 8453
    assert res2["chain_id"] == 1


def test_invalid_address_rejection():
    res = execute_onchain_task(to_address="0xInvalidAddr", calldata="0x")
    assert res["success"] is False
    assert "Invalid Ethereum address" in res["error"]
