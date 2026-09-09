"""
Tests for Dry-Run Execution and Workflow Composition Planning
Validates:
- keeper_execute_tx(dry_run=True) returns deterministic preview without mutating cache or ledger
- keeper_plan_workflow validates multi-step workflows, detects invalid steps, and calculates aggregate budgets
- Rejection of workflows exceeding maximum bounded steps (Rule 2)
"""

from agent_keeper.relay import KeeperRelayClient
from agent_keeper.schemas import TxExecutionRequest
from agent_keeper.server import (
    _audit_verifier,
    keeper_execute_tx,
    keeper_plan_workflow,
)


def test_dry_run_tx_execution_request_schema():

    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x1234",
        value_wei=1000,
        chain_id=8453,
        dry_run=True,
    )
    assert req.dry_run is True


def test_relay_client_dry_run_execution():
    client = KeeperRelayClient(audit_verifier=_audit_verifier)
    initial_cache_size = len(client._idempotency_cache)
    initial_ledger_size = len(_audit_verifier._committed_leaves)

    req = TxExecutionRequest(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0xabcdef",
        value_wei=5000,
        chain_id=8453,
        idempotency_key="test-dry-run-key-1",
        dry_run=True,
    )
    res = client.execute_transaction(req)

    assert res.success is True
    assert res.status == "DRY_RUN_PASSED"
    assert res.tx_hash is None
    assert res.gas_used == 42000
    assert res.audit_receipt is not None
    assert res.audit_receipt.get("dry_run") is True

    # Assertions: state MUST NOT mutate during dry run
    assert len(client._idempotency_cache) == initial_cache_size
    assert len(_audit_verifier._committed_leaves) == initial_ledger_size


def test_mcp_keeper_execute_tx_dry_run_tool():

    res = keeper_execute_tx(
        target_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        calldata_hex="0x",
        value_wei=0,
        chain_id=1,
        dry_run=True,
    )
    assert res["success"] is True
    assert res["status"] == "DRY_RUN_PASSED"
    assert res["tx_hash"] is None
    assert res["gas_used"] == 21000
    assert res["audit_receipt"]["dry_run"] is True


def test_workflow_plan_valid_multi_step():
    steps = [
        {
            "step_id": "step_1_pay",
            "action": "x402_settle",
            "params": {
                "resource_url": "https://api.provider.com/data",
                "amount_usdc": 0.50,
                "recipient_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            },
        },
        {
            "step_id": "step_2_tx",
            "action": "execute_tx",
            "params": {
                "target_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                "calldata_hex": "0xfeedface",
                "value_wei": 1000000000000000,  # 0.001 ETH
                "chain_id": 8453,
            },
        },
    ]

    res = keeper_plan_workflow(steps=steps)
    assert res["success"] is True
    assert res["verdict"] == "READY_FOR_EXECUTION"
    assert res["total_steps"] == 2
    assert res["estimated_total_usdc"] == 0.50
    assert res["estimated_total_value_wei"] == 1000000000000000
    assert res["estimated_total_gas"] == 42000
    assert len(res["steps"]) == 2
    assert res["steps"][0]["valid"] is True
    assert res["steps"][1]["valid"] is True


def test_workflow_plan_invalid_step_fails_entire_batch():
    steps = [
        {
            "step_id": "valid_step",
            "action": "execute_tx",
            "params": {
                "target_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                "calldata_hex": "0x",
                "value_wei": 0,
                "chain_id": 1,
            },
        },
        {
            "step_id": "invalid_step_bad_address",
            "action": "execute_tx",
            "params": {
                "target_address": "0xInvalidAddressNotHex",
                "calldata_hex": "0x",
                "value_wei": 0,
                "chain_id": 1,
            },
        },
    ]

    res = keeper_plan_workflow(steps=steps)
    assert res["success"] is False
    assert res["verdict"] == "VALIDATION_FAILED"
    assert res["steps"][0]["valid"] is True
    assert res["steps"][1]["valid"] is False
    assert "Invalid Ethereum address" in res["steps"][1]["error"]


def test_workflow_plan_bounds_enforcement():
    # Attempting to exceed 16 steps must be rejected by Power of 10 bounded loop rule
    excessive_steps = [
        {
            "step_id": f"step_{i}",
            "action": "execute_tx",
            "params": {
                "target_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                "calldata_hex": "0x",
                "value_wei": 0,
                "chain_id": 1,
            },
        }
        for i in range(20)
    ]
    res = keeper_plan_workflow(steps=excessive_steps)
    assert res["success"] is False
    assert "exceeds maximum allowed limit (16)" in res["error"]
