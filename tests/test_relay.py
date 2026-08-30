"""
Test Suite for Onchain Execution Relay (Power of 10 Safety Invariants Invariants)
"""

from agent_keeper.relay import KeeperRelayClient
from agent_keeper.schemas import TxExecutionRequest


def test_relay_client_initialization():
    client = KeeperRelayClient()
    assert client.max_retries == 10
    assert client.api_url is not None


def test_successful_relay_execution():
    client = KeeperRelayClient()
    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x12345678",
        value_wei=0,
        chain_id=1,
    )
    res = client.execute_transaction(req)
    assert res.success is True
    assert res.tx_hash.startswith("0x")
    assert res.status == "CONFIRMED"
    assert res.audit_receipt is not None


def test_idempotent_tx_execution():
    client = KeeperRelayClient()
    req1 = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0xabcdef",
        chain_id=8453,
        idempotency_key="unique-task-99",
    )
    res1 = client.execute_transaction(req1)

    # Second submission with same idempotency key returns cached receipt
    res2 = client.execute_transaction(req1)
    assert res1.tx_hash == res2.tx_hash
    assert res2.audit_receipt["idempotent_hit"] is True


def test_bounded_loop_retry_exhaustion():
    client = KeeperRelayClient()
    req = TxExecutionRequest(
        target_address="0x000000000000000000000000000000000000dEaD",
        calldata_hex="0xdeadbeef",
        chain_id=1,
    )
    # Simulate force failure
    res = client.execute_transaction(req, simulate_failure=True)
    assert res.success is False
    assert "Exhausted all" in res.error
