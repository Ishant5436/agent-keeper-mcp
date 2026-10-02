# Circle Arc Microgrants Technical Submission Dossier

**Project Name:** AgentKeeper-MCP  
**BUIDL Profile:** [#48196](https://dorahacks.io/buidl/48196)  
**Track:** Arc Mainnet Builders (500 USDC Microgrant Pool)  
**Prize Pool:** 500 USDC Microgrant  
**Target Network:** Arc Mainnet (Chain ID 5042)  
**Author:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu`)  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Upstream Integration:** [KeeperHub PR #2547](https://github.com/KeeperHub/keeperhub/pull/2547) (Merged into `staging`)  

---

**Live deployment status:** `keeper_agent_balance` performs real, read-only
JSON-RPC balance queries against Arc Mainnet today. `keeper_execute_tx`
without a configured relay reports `status: SIMULATED_LOCAL`, not a broadcast
confirmation. `scripts/broadcast_live_arc_tx.py` submits one real, minimal
transaction once a wallet is funded; see the repository README for the
resulting transaction hash and explorer link.

---

## 1. Abstract & System Architecture

Autonomous onchain execution agents face a fundamental trilemma: **context credential exposure**, **state desynchronization (nonce collisions)**, and **unhandled HTTP 402 resource gating**. When private keys or RPC URLs are injected into an agent's conversational context, any unhandled revert or stack trace risks leaking keys into chat logs, prompt caches, or model fine-tuning sets.

`AgentKeeper-MCP` resolves this through a Model Context Protocol (MCP) gateway with bounded memory structures and local key isolation. Private keys remain in local process memory, while the agent interacts strictly via typed JSON-RPC tools with bounded inputs, EIP-712 structured permits, and cryptographic audit proofs.

For the **Creditcoin 3.0 ecosystem**, AgentKeeper implements an autonomous **Attestcoin Cross-Chain Solver Escrow Manager**, allowing AI agents on EVM chains (Arbitrum, Base, Mantle, Ethereum) to request cross-chain computational resources and settle solver reimbursements via cryptographic Merkle inclusion proofs.

```
+-----------------------------------------------------------------------------------+
|               Agent Client Runner (IDE / Autonomous CLI / Host)                   |
+-----------------------------------------+-----------------------------------------+
                                          | stdio / JSON-RPC 2.0 (FastMCP)
                                          v
+-----------------------------------------------------------------------------------+
|                                 AgentKeeper-MCP                                   |
|                                                                                   |
|  +-----------------------+ +------------------------+ +------------------------+  |
|  | keeper_execute_tx     | | keeper_x402_settle     | | keeper_audit_verify    |  |
|  | Non-Custodial Key     | | EIP-712 Permit Signer  | | Flat Array Merkle Heap |  |
|  | Sandbox & Idempotency | | Micro-Payment Gating   | | Cryptographic Audit    |  |
|  +----------+------------+ +-----------+------------+ +-----------+------------+  |
|             |                          |                          |               |
|             v                          v                          v               |
|  +-----------------------------------------------------------------------------+  |
|  | [4] keeper_agent_balance    | [5] keeper_creditcoin_settle                  |  |
|  | Multi-Chain RPC Budget      | Attestcoin Merkle O(log N) Solver Settlement  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------+-----------------------------------------+
                                          |
                   +----------------------+-----------------------+
                   v                                              v
      EVM Networks (Base, OP, Mantle)               Creditcoin 3.0 L1 / x402 APIs
    (Onchain Contract Execution)                     (Attestcoin Solver Settlement)
```

---

## 2. Formal Algorithmic Complexity & Data Structures

Every core data structure in `AgentKeeper-MCP` is engineered with explicit time and space invariants:

| Algorithmic Component | Time Complexity | Space Complexity | Operational & Invariant Guarantee |
| :--- | :--- | :--- | :--- |
| **1. `FlatMerkleTree`** | Construction: O(N)<br>Proof Gen: O(log N)<br>Verification: O(log N) | Auxiliary: O(N)<br>Proof Size: O(log N) | Complete binary tree in flat contiguous array; bitwise parent/sibling traversal `((i-1)>>1)`; zero recursive stack frames. |
| **2. `CreditcoinSolver`** | Registration: O(1)<br>Verification: O(log N)<br>Settlement: O(1) | Bounded Capacity:<br>O(MAX_CAPACITY) | Ring-buffer circular eviction cap (2,048 intents); Merkle inclusion proof traversal; terminal double-spend prevention. |
| **3. `RelayIdempotencyCache`** | Lookup: O(1)<br>Eviction: O(1) | Bounded Entry Cap:<br>O(K) | Keccak256 seed hashing; FIFO capacity eviction (cap = 1024); prevents duplicate broadcasts during RPC timeouts or fee spikes. |
| **4. `X402PaymentManager`** | Signing: O(1)<br>Verification: O(1) | Fixed State: O(1) | Monotonic cumulative budget invariant: S_t = S_{t-1} + Delta <= S_{max}. |

---

## 3. Code Quality Invariants & Safety Constraints

The implementation enforces strict software constraints:

| Invariant | Standard Enforced | Implementation Evidence |
| :--- | :--- | :--- |
| **Rule 1: Simple Control Flow** | Zero recursion, zero longjmp | Flat array iteration; iterative Merkle proof build without stack recursion. |
| **Rule 2: Bounded Loops** | Fixed upper bounds on all loops | Retry loops bounded at `max_retries=10`; workflow composition bounded at `MAX_WORKFLOW_STEPS=16`; Merkle proof depth capped at `<= 64` in schema & tree. |
| **Rule 3: Deterministic Memory** | Bounded memory structures | `MAX_INTENTS_CAPACITY = 2048`; FIFO eviction limits on caches (`cap = 1024`). |
| **Rule 4: Function Length** | <= 60 lines per routine | Modular helper architecture; zero monolithic procedures. |
| **Rule 5: Assertion Density** | >= 2 assertions per function | Pre-condition and post-condition invariants validated in every routine. |
| **Rule 6: Smallest Scope** | Encapsulated Manager State | State mutation strictly confined to typed manager class instances with bounded capacity; zero raw mutable module-level globals. |
| **Rule 7: Check Returns & Parameters** | Strict input validation | EIP-55 checksum, calldata byte limits (128KB), wei spending caps. |
| **Rule 8: Minimal Metaprogramming** | Zero dynamic code evaluation | Strict Pydantic schemas; zero `eval()`, `exec()`, or dynamic monkey-patching. |
| **Rule 9: Restrict Pointer Indirection** | Single-level reference traversal | Flat contiguous array indexing `((i-1) >> 1)` rather than deep pointer-node trees. |
| **Rule 10: Static Analysis & Tests** | 100% test pass rate, 0 warnings | 112/112 passing test suite (including 5,000-case Hypothesis property fuzz tests) & 0 ruff warnings. |

---

## 4. Internal Safety & Static-Analysis Checklist

AgentKeeper-MCP maintains an internal engineering checklist, organized loosely along the section structure of the ISO 9001 quality-management standard for convenience. This is a self-administered script, not a third-party or accredited certification:

| Checklist Area (internal script label) | Metric & Standard Enforced | Status |
| :--- | :--- | :--- |
| **Area 4: Context & Infrastructure** | Multi-chain config (Arc, Base, Arb, Mantle, CTC), FastMCP stdio server | `[PASS] 100%` |
| **Area 5: Leadership & Quality** | Internal quality notes (`QUALITY_MANUAL.md`), zero-defect policy | `[PASS] 100%` |
| **Area 6: Planning & Risk** | Internal risk register (`RISK_REGISTER.md`), Merkle depth bounds ($\le 64$), EIP-55 checksum | `[PASS] 100%` |
| **Area 7: Support & Qualification** | Typed Pydantic schemas, Ruff static analysis, Python 3.12 pinned runtime | `[PASS] 100%` |
| **Area 8: Operation & V&V** | Traceability notes (`TRACEABILITY_MATRIX.md`), 112 automated tests, FastMCP integration | `[PASS] 100%` |
| **Area 9: Performance Evaluation** | Dynamic oracle anchoring verification, Arc Mainnet live query, GitHub Actions CI | `[PASS] 100%` |
| **Area 10: Continual Improvement** | Hypothesis property fuzz engine (5,000 iterations), automated checklist script | `[PASS] 100%` |

---

## 5. Creditcoin 3.0 Track Alignment

`AgentKeeper-MCP` natively supports both **Creditcoin Mainnet (Chain ID 1024)** and **Creditcoin Testnet (Chain ID 102031)**:
* **Attestcoin Proof Settlement (`keeper_creditcoin_settle`):** Validates that cross-chain solver tasks initiated on L2s (Arbitrum, Base, Mantle, Arc) are cryptographically matched to valid transaction hashes via real Merkle branch proofs before releasing escrowed CTC funds. Enforces registered solver addresses and on-chain oracle root anchoring.
* **Non-Custodial Architecture:** Solvers receive programmatic EIP-712 payment promises that can be verified and claimed onchain without human coordinator intervention.
* **Deterministic Accounting:** Bounded state tracking guarantees that solver balances and fees remain fully solvent under high-throughput request loads.

---

## 6. Judge Reproduction & Verification Guide

```bash
# 1. Clone & Enter Repository
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp

# 2. Execute Automated Test Suite (112 Tests Passing)
make test

# 3. Run internal safety/static-analysis checklist (7/7 areas; script output
#    still prints legacy "ISO/DIS 9001:2026" / "Clause" labels internally)
make audit-iso9001

# 4. Run Interactive Demonstrator (All 5 Onchain Workflows)
make demo
```

### Verification Telemetry Output:
```
============================= 112 passed in 13.72s =============================
[PASS] Clause 4: Context & Digital Infrastructure (4/4 requirements)
[PASS] Clause 5: Leadership & Quality Culture (3/3 requirements)
[PASS] Clause 6: Planning & Risk-Based Thinking (4/4 requirements)
[PASS] Clause 7: Support & Tool Qualification (3/3 requirements)
[PASS] Clause 8: Operation & Software V&V (4/4 requirements)
[PASS] Clause 9: Performance Evaluation & Audit Trails (3/3 requirements)
[PASS] Clause 10: Continual Improvement & Defect Containment (2/2 requirements)
Final Compliance Score: 100.0% (7/7 Clauses Compliant)

[SUCCESS] FlatMerkleTree: O(log N) inclusion proofs verified
[SUCCESS] Creditcoin 3.0: Attestcoin solver escrow & reimbursement confirmed
[SUCCESS] EIP-712: MicroPaymentPermit signed within daily allowance ($5.00)
[SUCCESS] FastMCP: 5 tool interfaces active with bounded schema validation
[SUCCESS] All 5 Autonomous Onchain Workflows Verified Successfully!
```
