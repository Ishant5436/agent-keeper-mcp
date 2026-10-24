# HashKey Chain Horizon Hackathon (Mumbai Edition) — Submission Dossier

**Hackathon Portal:** HashKey Chain Horizon Hackathon (Mumbai Edition) on DoraHacks  
**Prize Pool:** 10,000 USDT (5,000 USDT per track)  
**Target Track:** **Track 2: Agent Payments & A2A Settlement (5,000 USDT Prize Pool)**  
**Submission Deadline:** November 1, 2026 at 21:30 IST (UTC+5:30)  
**Demo Day / Winners Announcement:** November 4–5, 2026  
**Author / Team:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu` / Mumbai, India)  
**Project Name:** `AgentKeeper-MCP` — Deterministic Agent-to-Agent Payment & Settlement Gateway  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  

---

## 1. Project Title & Tagline
* **Project Name:** `AgentKeeper-MCP`
* **Tagline:** `Non-custodial Model Context Protocol gateway, x402 micro-payment router, and deterministic agent-to-agent settlement protocol.`

---

## 2. Track Alignment: Agent Payments & A2A Settlement

In the emerging agentic economy, autonomous AI systems must pay each other for compute, specialized model inference, real-time data oracles, and task execution. Existing Web3 infrastructure forces agents into fragile setups: injecting private keys directly into prompt contexts, incurring high gas volatility, and suffering from unhandled transaction reverts.

`AgentKeeper-MCP` is purpose-built to solve A2A settlement through three core pillars:
1. **Model Context Protocol (MCP) Isolation:** Private keys never touch LLM conversational memory. Agents interact strictly via typed JSON-RPC tools with bounded inputs and spending limits.
2. **x402 Micropayment Protocol:** Instant HTTP 402 "Payment Required" challenge negotiation with EIP-712 cryptographic permit signing.
3. **Deterministic Escrow & Settlement Contract:** Non-reentrant task-based escrow with emergency timeout refunds and verifiable on-chain event receipts.

---

## 3. Technical Architecture & Invariants

```
+-----------------------------------------------------------------------------------+
|               Autonomous Agent (Claude / Gemini / Local Ollama)                   |
+-----------------------------------------+-----------------------------------------+
                                          | JSON-RPC 2.0 (FastMCP)
                                          v
+-----------------------------------------------------------------------------------+
|                            AgentKeeper-MCP Gateway                                |
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
|  | - Non-reentrant single-slot mutex                                           |  |
|  | - All routines <= 60 lines, assertion density >= 2 (Holzmann Power of 10)  |  |
|  | - Immutable settlement receipts and time-locked emergency refunds           |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 4. Verification Evidence & Test Status

- **Automated Test Suite:** 148 / 148 passing unit and property fuzz tests.
- **Contract Code:** `contracts/ArcAgentEscrow.sol` and `contracts/X402Receipt.sol`.
- **EIP-712 Receipt Proof:** Block 66163775 (`0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720`).
- **License:** Permissive open-source MIT License.
