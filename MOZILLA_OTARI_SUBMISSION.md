# Mozilla Otari Hackathon — Turnkey Submission Dossier

**Competition Portal:** Mozilla Otari Hackathon — Devs Wilding Online! on DoraHacks  
**Prize Pool:** $1,200 USD + Direct Mentorship with Mozilla.ai Engineers  
- 1st Place: **$1,000 USD** + 3 hours Mozilla.ai mentorship  
- 2nd Place: **$200 USD** + 2 hours Mozilla.ai mentorship  
- 3rd Place: 1 hour Mozilla.ai mentorship  
**Submission Deadline:** **November 11, 2026**  
**Author / Developer:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu`)  
**Project Name:** `Agent-Keeper: Deterministic Spend Governance & Guard Gateway for Otari`  
**GitHub Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Live Interactive Documentation:** [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/)  

---

## 1. Executive Summary & Problem Space

As autonomous AI agents leverage multi-model gateways like Mozilla’s **Otari** to call external APIs, generate smart contracts, and execute transactions, systems face severe unconstrained execution risks:
1. **Unbounded Financial Drains:** An autonomous agent caught in an automated loop or hallucinating high-frequency calls can exhaust API allowances and treasury balances in minutes.
2. **Missing Invariant Verification:** Current LLM tool gateways execute tool outputs blindly without verifying preconditions, function bounds, or cryptographic signatures before broadcasting transactions.
3. **Vendor Lock-in & Centralized Bottlenecks:** Traditional agent middleware relies on proprietary APIs that expose API keys and credentials to third-party cloud aggregators.

`Agent-Keeper` provides a local, zero-leakage **Deterministic Safety & Spend Governance Layer** that pairs seamlessly with Mozilla Otari’s multi-model routing gateway:
- Enforces strict deterministic budget allowances and automated spend ceilings per agent session.
- Intercepts and cryptographically audits transaction calldata against Gerard J. Holzmann's **Power of 10 Safety Invariants** before dispatch.
- Implements HTTP `402 Payment Required` (x402) micropayment protocol settlement, enabling agents to pay for inference services per request on-chain without sharing API secrets.

---

## 2. Technical Architecture & Otari Integration

```
  ┌──────────────────────────────────────────────────────────────┐
  │                 Mozilla Otari AI Gateway                     │
  │     (Multi-Model Routing: Open-Weight & Frontier LLMs)       │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ Prompt & Tool Invocation
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │         Agent-Keeper MCP Governance & Budget Engine          │
  │                                                              │
  │  1. Spend & Budget Tracker: Per-session financial limits     │
  │  2. Invariant Auditor: AST and bytecode safety checks        │
  │  3. Merkle Guard: Cryptographic calldata validation          │
  │  4. x402 Micropayment Engine: Onchain autonomous settlement  │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ Verified Tool Dispatch
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │     Execution Target (Local POSIX / EVM / Multi-Chain)       │
  └──────────────────────────────────────────────────────────────┘
```

### Key Technical Capabilities:
1. **Zero-Heap Invariant Validation:**
   Every tool dispatch passes through deterministic safety assertions: routines $\le 60$ lines, zero dynamic memory allocations on the hot path, and strict parameter validation.
2. **Deterministic Spending Caps:**
   Session budgets are enforced at the transport layer. Any attempt to exceed the allocated spend limit immediately triggers an atomic circuit-breaker.
3. **Multi-Chain x402 Protocol Settlement:**
   Native support for instant settlement on Portaldot, HashKey Chain, and EVM chains using EIP-712 typed data signatures.

---

## 3. Verification & Reproduction Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Ishant5436/agent-keeper-mcp.git
   cd agent-keeper-mcp
   ```

2. **Run Automated Test Suite (25/25 Tests Passing):**
   ```bash
   source venv/bin/activate
   pytest tests/test_portaldot_chain.py tests/test_hashkey_chain.py tests/test_arc_mainnet.py tests/test_x402.py
   ```

3. **Explore Live Documentation & Interactive Demo:**
   Visit the production GitHub Pages deployment:  
   👉 [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/)
