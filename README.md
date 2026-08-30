# AgentKeeper-MCP

I built AgentKeeper because I was tired of how fragile it is to let autonomous coding agents touch onchain workflows. If you give an LLM direct access to a private key or raw RPC, it will either leak credentials in the context window, burn through gas retrying stuck nonces, or crash the moment a paid API returns HTTP 402 Payment Required.

AgentKeeper is a lightweight Python MCP server and KeeperHub plugin that sits between your agent runtime (Claude, Gemini, Cursor) and EVM networks. Instead of handing the model raw private keys or unlimited RPC access, the server exposes four bounded tools over stdio and SSE:

- `keeper_execute_tx`: Sends raw transactions through an idempotency cache with capped gas limits and automatic nonce management.
- `keeper_x402_settle`: Catches HTTP 402 payment headers from paywalled APIs, signs a localized EIP-712 permit within a hard daily allowance, and retries the request without pausing the agent.
- `keeper_audit_verify`: Lets the agent verify Merkle proofs against the local transaction log to confirm state changes before taking follow-up actions.
- `keeper_agent_balance`: Returns real-time multi-chain balances so the agent can budget its operations.

## Architecture

I wrote the entire core using Python 3.12 and FastMCP with strict type assertions, bounded retry loops, and zero dynamic memory leaks. The test suite has 21 unit tests covering relay timeouts, replay attacks, x402 header parsing, and balance budgeting, all running in about one second on pytest.

```
AI Agent (Claude / Gemini / Cursor)
         │
         ▼  (stdio / SSE)
┌──────────────────────────────────────────────┐
│            AgentKeeper MCP Server            │
│                                              │
│  • keeper_execute_tx     • keeper_x402_settle │
│  • keeper_audit_verify   • keeper_agent_balance │
└──────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
  EVM Network RPC         x402 Paywalled APIs
```

## Tools Reference

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `keeper_execute_tx` | `to`, `value`, `data`, `chain_id` | Validates calldata, checks gas limits, signs locally, and broadcasts transaction. |
| `keeper_x402_settle` | `resource_url`, `amount_usdc` | Catches 402 payment requirements, validates daily budget, generates signature. |
| `keeper_audit_verify` | `tx_hash`, `merkle_root`, `proof` | Validates Merkle inclusion proof for on-chain state verification. |
| `keeper_agent_balance` | `chain_id`, `tokens` | Queries multi-token balances across EVM chains. |

## Quick Start

```bash
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp
uv venv --python python3.12
source .venv/bin/activate
pip install -e .

# Run test suite
pytest
```

## Upstream Integration

This project is submitted to the [KeeperHub Ecosystem](https://github.com/KeeperHub/keeperhub) under [Pull Request #2188](https://github.com/KeeperHub/keeperhub/pull/2188).

## License

MIT License. Free for developers and autonomous agent operators.
