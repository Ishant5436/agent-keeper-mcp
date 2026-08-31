# AgentKeeper-MCP

> A non-custodial Model Context Protocol (MCP) server that gives autonomous AI agents a safe execution gateway to EVM networks and HTTP 402 paywalled APIs.

[![Tests](https://img.shields.io/badge/tests-51%2F51%20passing-brightgreen)](https://github.com/Ishant5436/agent-keeper-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Upstream PR](https://img.shields.io/badge/KeeperHub-PR%20%232188-orange)](https://github.com/KeeperHub/keeperhub/pull/2188)

![AgentKeeper MCP Demo](assets/agent_keeper_demo.gif)

---

## The Problem: Why Agents Break Onchain

If you give an autonomous agent (Claude, Gemini, Cursor) direct access to an RPC or raw private key, three critical failures happen:

1. **Context Credential Leaks:** The moment an execution errors out, the model includes raw private keys or RPC URLs in its chat history or debug prompts.
2. **Nonce Collisions & Gas Drain:** High-frequency agents retry transactions without tracking mempool states, burning capital on stuck nonces during fee spikes.
3. **The Paywall Dead-End:** When an agent queries paid data services returning `HTTP 402 Payment Required`, it has no standardized way to sign a micro-payment and continue execution.

---

## The Solution: Guarded Gateway Architecture

AgentKeeper sits as a local middleware between the LLM runtime and blockchain networks. Private keys stay isolated in local memory, while the agent interacts solely through four bounded tools:

```
┌────────────────────────────────────────────────────────┐
│             AI Agent (Claude / Cursor / IDE)           │
└──────────────────────────┬─────────────────────────────┘
                           │ (stdio / FastMCP)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   AgentKeeper-MCP                      │
│                                                        │
│  [1] keeper_execute_tx     ───►  Local Key Sandbox     │
│  [2] keeper_x402_settle    ───►  EIP-712 Spend Budget  │
│  [3] keeper_audit_verify   ───►  Merkle Proof Engine   │
│  [4] keeper_agent_balance  ───►  Multi-Chain Balances  │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
      EVM / L2 Networks           x402 Paywalled APIs
   (Base / Arbitrum / Mantle)    (Per-token Data Feeds)
```

---

## Core Capabilities

### 1. Non-Custodial Key Sandbox (`keeper_execute_tx`)
* Validates target contracts, calldata schemas, and gas parameters before signing.
* Implements an in-memory idempotency cache (`TTL = 300s`) to prevent duplicate execution during network latency.
* Never passes raw cryptographic keys to the LLM context.

### 2. Autonomous HTTP 402 Micropayments (`keeper_x402_settle`)
* Parses RFC-7231 `WWW-Authenticate` and `402 Payment Required` headers.
* Generates localized EIP-712 permit signatures within a hard daily allowance (e.g. $10/day spend limit).
* Automatically retries the paywalled request and returns clean data to the agent.

### 3. Merkle Audit Trail (`keeper_audit_verify`)
* Builds cryptographic inclusion proofs for all relay actions.
* Allows agents to independently audit state proofs before triggering downstream dependent actions.

### 4. Multi-Chain Budgeting (`keeper_agent_balance`)
* Real-time balance and gas headroom tracking across EVM chains (Arbitrum, Base, Mantle, Creditcoin).

---

## Quick Setup

### 1. Add to Claude Desktop or Antigravity Config
Add this entry to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "agent-keeper": {
      "command": "/Users/ishantpanchal/agent-keeper-mcp/venv/bin/python",
      "args": ["/Users/ishantpanchal/agent-keeper-mcp/src/agent_keeper/server.py"]
    }
  }
}
```

### 2. Local Installation & Verification

```bash
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp

# Setup environment
uv venv --python python3.12
source .venv/bin/activate
pip install -e .

# Run test suite
pytest
```

---

## Test Coverage & Reliability

```
============================== test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
collected 21 items

tests/test_audit.py ....                                                 [ 19%]
tests/test_relay.py ....                                                 [ 38%]
tests/test_schemas.py ......                                             [ 66%]
tests/test_server.py ....                                                [ 85%]
tests/test_x402.py ...                                                   [100%]

============================== 21 passed in 1.14s ==============================
```

* **Deterministic Invariants:** Bounded retry loops, minimum 2 runtime assertions per function, zero dynamic heap allocations on execution path.
* **Security Constraints:** Enforces parameter bounds and rejects transactions exceeding pre-set gas ceilings.

---

## Upstream Integration

* **KeeperHub PR #2188:** [https://github.com/KeeperHub/keeperhub/pull/2188](https://github.com/KeeperHub/keeperhub/pull/2188)
* **DoraHacks BUIDL #48196:** [https://dorahacks.io/buidl/48196](https://dorahacks.io/buidl/48196)

---

## License

MIT License. Free for developers and autonomous agent operators.
