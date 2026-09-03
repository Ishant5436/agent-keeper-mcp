# BUIDL CTC Fall 2026 Technical Submission Dossier

**Project Name:** AgentKeeper-MCP  
**BUIDL Profile:** [#48196](https://dorahacks.io/buidl/48196)  
**Track:** Creditcoin 3.0 Cross-Chain Interoperability & Multi-Chain Autonomous Agent Infrastructure  
**Prize Pool:** $15,000 USD  
**Author:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu`)  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Upstream Integration:** [KeeperHub PR #2188](https://github.com/KeeperHub/keeperhub/pull/2188)  

---

## 1. Abstract & System Architecture

Autonomous Large Language Model (LLM) agents operating onchain face a fundamental trilemma: **context credential exposure**, **state desynchronization (nonce collisions)**, and **unhandled HTTP 402 resource gating**. When private keys or RPC URLs are injected into an LLM's conversational context, any unhandled revert or stack trace risks leaking keys into chat logs, prompt caches, or fine-tuning datasets.

`AgentKeeper-MCP` resolves this through a strictly isolated Model Context Protocol (MCP) gateway adhering to Deterministic Safety Invariants (Power of 10). Private keys remain isolated in local non-swappable process memory, while the agent interacts strictly via typed JSON-RPC tools with bounded inputs, EIP-712 structured permits, and cryptographic audit proofs.

For the **Creditcoin 3.0 ecosystem**, AgentKeeper implements an autonomous **Attestcoin Cross-Chain Solver Escrow Manager**, allowing AI agents on EVM chains (Arbitrum, Base, Mantle, Ethereum) to request cross-chain computational resources and settle solver reimbursements via cryptographic Merkle inclusion proofs.

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    LLM Agent Client (Claude / Cursor / Custom)                    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ stdio / JSON-RPC 2.0 (FastMCP)
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 AgentKeeper-MCP                                   │
│                                                                                   │
│  ┌───────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐  │
│  │ keeper_execute_tx     │ │ keeper_x402_settle     │ │ keeper_audit_verify    │  │
│  │ Non-Custodial Key     │ │ EIP-712 Permit Signer  │ │ Flat Array Merkle Heap │  │
│  │ Sandbox & Idempotency │ │ Micro-Payment Gating   │ │ Cryptographic Audit    │  │
│  └──────────┬────────────┘ └───────────┬────────────┘ └───────────┬────────────┘  │
│             │                          │                          │               │
│             ▼                          ▼                          ▼               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ Creditcoin 3.0 Attestcoin Solver & Multi-Chain Relay (Chain ID 1024/102031) │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     EVM Networks (Base, OP, Mantle)               HTTP 402 Paywalled Resources
   (Onchain Contract Execution)                     (Per-Token Data Feeds)
```

---

## 2. Formal Algorithmic Complexity & Data Structures

Every core data structure in `AgentKeeper-MCP` is engineered with explicit time and space invariants:

```
┌────────────────────────────┬─────────────────────────────┬──────────────────────────┬────────────────────────────────────────────────────────┐
│ Algorithmic Component      │ Time Complexity             │ Space Complexity         │ Operational & Invariant Guarantee                      │
├────────────────────────────┼─────────────────────────────┼──────────────────────────┼────────────────────────────────────────────────────────┤
│ 1. `FlatMerkleTree`        │ Construction: O(N)          │ Auxiliary: O(N)          │ Complete binary tree in flat contiguous array;          │
│                            │ Proof Generation: O(log N)  │ Proof Size: O(log N)     │ Bitwise parent/sibling traversal ((i-1)>>1);           │
│                            │ Verification: O(log N)      │                          │ Zero recursive call stack frame allocations.           │
├────────────────────────────┼─────────────────────────────┼──────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. `CreditcoinSolver`      │ Intent Registration: O(1)   │ Bounded Capacity:        │ Ring-buffer circular eviction cap (2,048 intents);     │
│                            │ Settlement Lookup: O(1)     │ O(MAX_CAPACITY)          │ Double-spend prevention via terminal state machine.    │
├────────────────────────────┼─────────────────────────────┼──────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. `RelayIdempotencyCache` │ Key Hash Lookup: O(1)       │ Bounded Entry Cap:       │ SHA-256 seed hashing; prevents duplicate broadcasts   │
│                            │ Expiration Eviction: O(1)   │ O(K)                     │ during RPC timeouts or fee spikes (TTL = 300s).        │
├────────────────────────────┼─────────────────────────────┼──────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. `X402PaymentManager`    │ EIP-712 Signing: O(1)       │ Fixed State: O(1)        │ Monotonic cumulative budget invariant:                 │
│                            │ Budget Verification: O(1)   │                          │ S_{t} = S_{t-1} + Delta <= S_{max}.                    │
└────────────────────────────┴─────────────────────────────┴──────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Power of 10 Deterministic Safety Invariants Audit

The implementation strictly satisfies the Power of 10 Safety Invariants:

```
INVARIANT                          | STANDARD ENFORCED                  | IMPLEMENTATION EVIDENCE
-----------------------------------|------------------------------------|-------------------------------------------------------
Rule 1: Simple Control Flow        | Zero recursion, zero longjmp       | Flat array iteration; iterative Merkle proof build.
Rule 2: Bounded Loops              | Fixed upper bounds on all loops    | Retry loops bounded at max_retries=3; Merkle depth <= 64.
Rule 3: Deterministic Memory       | Bounded memory structures          | MAX_INTENTS_CAPACITY = 2048; FIFO eviction limits.
Rule 4: Function Length            | <= 60 lines per routine            | Modular helpers; zero monolithic routines.
Rule 5: Assertion Density          | >= 2 assertions per function       | Pre-condition & post-condition validation in every unit.
Rule 7: Check Returns & Parameters | Strict input validation            | EIP-55 checksum, calldata byte limits (128KB), wei caps.
Rule 10: Static Analysis & Tests   | 100% test pass rate, 0 warnings   | 67/67 passing test suite (including 5,000-case Hypothesis property-based fuzz tests).
```

---

## 4. Creditcoin 3.0 Track Alignment

`AgentKeeper-MCP` natively supports both **Creditcoin Mainnet (Chain ID 1024)** and **Creditcoin Testnet (Chain ID 102031)**:
* **Attestcoin Proof Settlement:** Validates that cross-chain solver tasks initiated on L2s (Arbitrum, Base, Mantle) are cryptographically matched to valid transaction hashes before releasing escrowed funds.
* **Non-Custodial Architecture:** Solvers receive programmatic EIP-712 payment promises that can be verified and claimed onchain without human coordinator intervention.
* **Deterministic Accounting:** Bounded state tracking guarantees that solver balances and fees remain fully solvent under high-throughput request loads.

---

## 5. Judge Reproduction & Verification Guide

```bash
# 1. Clone & Enter Repository
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp

# 2. Execute Automated Test Suite (67 Tests Passing in <2.0s)
make test

# 3. Run Interactive Demonstrator
python3 demo.py
```

### Verification Telemetry Output:
```
============================== 67 passed in 1.95s ==============================
[SUCCESS] FlatMerkleTree: O(log N) inclusion proofs verified
[SUCCESS] Creditcoin 3.0: Attestcoin solver escrow & reimbursement confirmed
[SUCCESS] EIP-712: MicroPaymentPermit signed within daily allowance ($10.00)
[SUCCESS] FastMCP: 4 tool interfaces active with Power of 10 safety invariants
```
