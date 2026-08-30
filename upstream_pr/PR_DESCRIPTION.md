# Feature: Native Model Context Protocol (MCP) Server for KeeperHub

## Overview
This PR implements native Model Context Protocol (MCP) server bindings for KeeperHub, enabling autonomous AI agents (Claude, Gemini, OpenAI Assistants) to directly invoke KeeperHub's onchain execution, x402 micro-payment settlement, and cryptographic audit proofs via standard JSON-RPC tools.

## Key Capabilities Added
* **`keeper_execute_tx`**: Onchain transaction routing with automated nonce reservation and MEV protection.
* **`keeper_x402_settle`**: Autonomous settlement of HTTP 402 Payment Required challenges using EIP-712 payment permits.
* **`keeper_audit_verify`**: Merkle proof validation of transaction inclusion and state traces.
* **`keeper_agent_balance`**: Multi-chain treasury monitoring for agent accounts.

## Engineering Standards
* Power of 10 Safety Invariants compliance (bounded loops, strict type invariants, zero dynamic leaks).
* 100% test coverage with Pytest.
* Zero external breaking changes to existing KeeperHub CLI or REST endpoints.
