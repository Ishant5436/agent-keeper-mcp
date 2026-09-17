# ISO/DIS 9001:2026 Bidirectional Traceability Matrix: Agent Keeper MCP

This matrix establishes forward and backward traceability between agent settlement requirements, source modules, automated test cases, and verifiable evidence artifacts.

---

## 1. Traceability Mapping

| Requirement ID | Requirement Specification | Test Case ID | Test Implementation | Target Source Component | Verifiable Evidence Artifact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-AK-001** | Strict EIP-55 Ethereum address checksum validation | `TC-SCH-01` | [`test_schemas.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_schemas.py#L18) | [`schemas.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/schemas.py) | Pytest execution log |
| **REQ-AK-002** | Calldata boundary enforcement ($\le 128\text{KB}$) | `TC-SCH-02` | [`test_schemas.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_schemas.py#L32) | [`schemas.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/schemas.py) | Pytest execution log |
| **REQ-AK-003** | FlatMerkleTree cryptographic root generation and proof verification | `TC-MT-01` | [`test_merkle_tree.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_merkle_tree.py#L10) | [`merkle_tree.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/merkle_tree.py) | Pytest execution log |
| **REQ-AK-004** | Property-based fuzzing of Merkle proof tampering rejection | `TC-FUZZ-01` | [`test_fuzz_merkle.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_fuzz_merkle.py#L15) | [`merkle_tree.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/merkle_tree.py) | Hypothesis fuzzer output (100% rejection) |
| **REQ-AK-005** | Creditcoin 3.0 solver reimbursement with dynamic oracle block anchoring | `TC-CC-01` | [`test_creditcoin.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_creditcoin.py#L45) | [`creditcoin.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/creditcoin.py) | Pytest execution log |
| **REQ-AK-006** | Merkle proof iteration depth bound ($\le 64$) preventing DoS | `TC-CC-02` | [`test_creditcoin.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_creditcoin.py#L120) | [`creditcoin.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/creditcoin.py) | Pytest execution log |
| **REQ-AK-007** | Idempotent transaction relay with FIFO memory bounding | `TC-REL-01` | [`test_relay.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_relay.py#L22) | [`relay.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/relay.py) | Pytest execution log |
| **REQ-AK-008** | EIP-712 typed payment permit verification and cumulative spending cap | `TC-X402-01` | [`test_x402.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_x402.py#L20) | [`x402.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/x402.py) | Pytest execution log |
| **REQ-AK-009** | Native Circle Arc Mainnet (Chain ID 5042, 6-decimal USDC) settlement | `TC-ARC-01` | [`test_x402.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_x402.py#L55) | [`config.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/config.py) & [`x402.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/x402.py) | Pytest execution log |
| **REQ-AK-010** | FastMCP autonomous agent tool interfaces with schema enforcement | `TC-MCP-01` | [`test_server.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_server.py#L15) | [`server.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/server.py) | Pytest execution log |
| **REQ-AK-011** | Multi-step agent workflow execution and rollback on failure | `TC-WF-01` | [`test_workflow.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_workflow.py#L20) | [`server.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/server.py) | Pytest execution log |
| **REQ-AK-012** | Blackbox fuzz testing of malformed addresses and corrupted hex inputs | `TC-BB-01` | [`test_blackbox.py`](file:///Users/ishantpanchal/agent-keeper-mcp/tests/test_blackbox.py#L12) | [`schemas.py`](file:///Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/schemas.py) | Pytest execution log |

---

## 2. Verification Coverage
- **Total Tracked Requirements:** 12
- **Automated Verification Coverage:** 100% (106 passing tests across unit, blackbox, fuzz, and whitebox)
- **Static Conformance:** Ruff linter 0 errors, 100% clean.
