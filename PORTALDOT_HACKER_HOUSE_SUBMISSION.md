# Portaldot Hacker House 2026 — Submission Dossier

**Hackathon Portal:** Portaldot Hacker House 2026 on DoraHacks  
**Prize Pool:** 5,200 USDT (split between USDT and POT tokens)  
**Target Track:** **Track 1: Modular Cloud & Middleware** / **Track 2: Multi-Chain Infrastructure**  
**Submission Deadline:** November 6, 2026 at 04:00 UTC (~4 days remaining)  
**Author / Team:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu` / Mumbai, India)  
**Project Name:** `AgentKeeper-MCP` — Deterministic Agent-to-Agent Middleware & Multi-Chain Settlement Gateway  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**DoraHacks BUIDL ID:** [BUIDL #48196](https://dorahacks.io/buidl/48196)  
**Live Interactive Web Console:** [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/)  

---

## 1. Project Title & Tagline
* **Project Name:** `AgentKeeper-MCP`
* **Tagline:** `Non-custodial Model Context Protocol middleware, x402 micro-payment router, and deterministic settlement gateway for Portaldot V3.0 dual-VM execution.`

---

## 2. Track Alignment: Modular Cloud & Middleware / Multi-Chain Infrastructure

Portaldot Network V3.0 introduces a dual-layer runtime bridging Substrate/Wasm execution with full EVM compatibility. In the autonomous agentic economy, decentralized software agents (Claude, Gemini, local Ollama models) require robust middleware to coordinate micro-payments, escrow compute bounties, and settle task verification across heterogeneous chains without leaking private keys into LLM prompt contexts.

`AgentKeeper-MCP` is engineered as a zero-dependency, institutional-grade middleware layer:
1. **Model Context Protocol (MCP) Middleware:** FastMCP JSON-RPC tools with strictly typed inputs, bounded execution quotas, and cryptographic audit proofs. Private keys never enter conversational prompt contexts.
2. **Dual-VM EVM Router Integration:** Deploys deterministic Solidity smart contracts (`ArcAgentEscrow.sol` and `X402Receipt.sol`) to Portaldot V3.0 EVM runtime (Chain ID 420420777).
3. **x402 Micropayment Protocol:** Instant HTTP 402 challenge negotiation paired with EIP-712 structured cryptographic signatures for non-repudiable API service settlement.

---

## 3. Technical Architecture & Power of 10 Invariants

```
+-----------------------------------------------------------------------------------+
|               Autonomous Agent (Claude / Gemini / Local Ollama)                   |
+-----------------------------------------+-----------------------------------------+
                                          | JSON-RPC 2.0 (FastMCP)
                                          v
+-----------------------------------------------------------------------------------+
|                            AgentKeeper-MCP Middleware                             |
|                                                                                   |
|  +-----------------------+ +------------------------+ +------------------------+  |
|  | keeper_x402_settle     | | keeper_audit_verify    | | keeper_execute_tx     |  |
|  | EIP-712 Permit Signer  | | Flat Merkle Tree Heap  | | Non-Custodial Key     |  |
|  | Non-Repudiable Permit | | Evidentiary Audit Log  | | Idempotent Tx Relay   |  |
|  +----------+------------+ +-----------+------------+ +-----------+------------+  |
|             |                          |                          |               |
|             v                          v                          v               |
|  +-----------------------------------------------------------------------------+  |
|  | Deterministic Smart Contract Layer: ArcAgentEscrow & X402Receipt            |  |
|  | - Portaldot V3.0 EVM Runtime (Chain ID 420420777)                           |  |
|  | - Single-slot reentrancy mutex                                              |  |
|  | - All routines <= 60 lines, assertion density >= 2 (Holzmann Power of 10)  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Deterministic Safety Invariants (Holzmann Power of 10)
- **Bounded Control Flow:** Zero recursion, zero goto, all loops deterministically bounded.
- **Function Bounds:** Every routine strictly $\le 60$ lines of code.
- **Assertion Density:** Minimum $\ge 2$ assertions per function enforcing preconditions and postconditions.
- **Zero Dynamic Memory on Hot Path:** Fixed memory structs, zero unmanaged heap allocations during execution.

---

## 4. Portaldot Network V3.0 Integration Evidence

- **Target Network:** Portaldot Network V3.0 Testnet (Chain ID 420420777)
- **RPC Endpoint:** `https://test-evm-rpc-v3.portaldot.dev`
- **Native Symbol:** POT (14 decimals)
- **Integration Module:** `src/agent_keeper/portaldot_chain.py`
- **Unit & Integration Tests:** `tests/test_portaldot_chain.py` (100% green passing).
- **Bytecode Compilation:** Contract artifacts compiled and validated via solc 0.8.20.
- **Web Console Deployment:** [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/) (responsive, cross-browser Web3 wallet integration).
- **License:** Permissive open-source MIT License.
