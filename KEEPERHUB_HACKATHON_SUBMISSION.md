# KeeperHub - The Agent Economy Hackathon — Technical Submission Dossier

**Hackathon:** KeeperHub - The Agent Economy Hackathon (DoraHacks)  
**Timeline:** September 6 – September 18, 2026  
**Prize Pool:** $5,000 USD  
**Target Bounty:** Best KeeperHub Feature ($1,000 USDC)  
**Project Name:** AgentKeeper-MCP  
**BUIDL Profile:** [#48196](https://dorahacks.io/buidl/48196)  
**Author / Contributor:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu`)  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Upstream Integration:** [KeeperHub PR #2547](https://github.com/KeeperHub/keeperhub/pull/2547) & [Tracking Issue #2310](https://github.com/KeeperHub/keeperhub/issues/2310)  

---

## 1. Executive Summary & Hackathon Theme Alignment

The core challenge of the **Agent Economy** is non-deterministic execution. Because Large Language Models are probabilistic reasoning engines, allowing an AI agent to directly construct and broadcast raw on-chain transactions introduces three catastrophic failure modes:
1. **Reinterpretation & Value Drift:** Agents hallucinate calldata, invert token decimal precision, or misroute transaction outputs during volatile market conditions.
2. **Credential Exfiltration:** Injecting private keys or RPC authentication tokens into the model context window exposes credentials to prompt injection attacks and chat log leaks.
3. **Execution Desynchronization:** Rapid agent re-prompting generates concurrent transactions with nonce collisions, leading to stranded mempool transactions and burned gas.

**AgentKeeper-MCP** solves this by establishing a strictly isolated Model Context Protocol (MCP) gateway adhering to Deterministic Safety Invariants (Gerard J. Holzmann's Power of 10). It enables autonomous agents (Claude, Gemini, Cursor) to compose multi-step execution workflows, perform deterministic pre-flight dry runs, and enforce hard safety ceilings *before* any value transfer reaches the network.

---

## 2. System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    LLM Agent Client (Claude / Cursor / Gemini)                    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ stdio / JSON-RPC 2.0 (FastMCP)
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 AgentKeeper-MCP                                   │
│                                                                                   │
│  ┌───────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐  │
│  │ keeper_plan_workflow  │ │ keeper_execute_tx      │ │ keeper_x402_settle     │  │
│  │ Multi-Step Composer   │ │ MEV-Shield & Gas Relay │ │ EIP-712 Permit Signer  │  │
│  │ & Pre-Flight Dry-Run  │ │ (dry_run=True preview) │ │ HTTP 402 Micro-Gating  │  │
│  └──────────┬────────────┘ └───────────┬────────────┘ └───────────┬────────────┘  │
│             │                          │                          │               │
│             ▼                          ▼                          ▼               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ keeper_audit_verify     │ keeper_agent_balance   │ keeper_creditcoin_settle │  │
│  │ Flat-Array Merkle Proof │ Multi-Chain RPC Budget │ Attestcoin Cross-Chain   │  │
│  │ Verification (O(log N)) │ Inspector & Safeguard  │ Solver Escrow Settlement │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     EVM Networks (Base, OP, Mantle)               KeeperHub Gateway / REST Relay
```

---

## 3. FastMCP Tool Interface Specifications

### 1. Workflow Planning & Dry-Run Composition (`keeper_plan_workflow`)
Composes and simulates multi-step agent execution graphs up to a bounded limit of 16 steps per workflow:
- Validates all step schemas, addresses, and parameters before touching chain state.
- Aggregates total native value (wei), estimated gas units, and USDC micropayments.
- Rejects the entire workflow batch if any step violates safety bounds (`VALIDATION_FAILED`), returning actionable debugging telemetry without gas waste.

### 2. Isolated Execution Gateway (`keeper_execute_tx`)
Transmits on-chain transactions via KeeperHub's MEV-protected relay:
- **Pre-Flight Simulation (`dry_run=True`):** Returns deterministic validation metrics, gas estimation, and parameter verification without broadcasting or state mutation.
- **Strict Invariants:** Enforces EIP-55 address checksums, 128 KB calldata ceiling, and a 0.10 ETH safety cap.
- **Deduplication:** In-memory FIFO idempotency cache (`cap = 1024`, Keccak256 keys) prevents duplicate execution during network spikes.

### 3. Autonomous HTTP 402 Settlement (`keeper_x402_settle`)
Resolves RFC-7231 `402 Payment Required` paywalls for autonomous API resource consumption:
- Derives localized EIP-712 transfer permits signed exclusively inside isolated process memory.
- Enforces a monotonic cumulative spending cap ($5.00 USDC default) to eliminate runaway agent drain.

### 4. Cryptographic State Audit (`keeper_audit_verify`)
Validates execution integrity using a contiguous flat-array Merkle tree (`FlatMerkleTree`):
- Bitwise index arithmetic `((i - 1) >> 1)` guarantees $\mathcal{O}(\log N)$ proof generation and verification.
- Zero recursive call frames, eliminating stack overflow vulnerabilities.

### 5. Multi-Chain Budget Safeguard (`keeper_agent_balance`)
Inspects live on-chain balances across Base, Arbitrum One, Ethereum Mainnet, and Creditcoin:
- Reports live ETH/wei balances alongside consumed and remaining USDC micro-payment allowances.

---

## 4. Power of 10 Deterministic Safety Invariants Audit

| Invariant | Enforced Standard | Verified Implementation |
| :--- | :--- | :--- |
| **Rule 1: Simple Control Flow** | Zero recursion, zero longjmp | Flat array iteration; iterative Merkle proof build without stack recursion. |
| **Rule 2: Bounded Loops** | Fixed upper bounds on all loops | Retry loops bounded at `max_retries=10`; workflow steps bounded at `MAX_WORKFLOW_STEPS=16`; Merkle proof depth capped at `<= 64`. |
| **Rule 3: Deterministic Memory** | Bounded memory structures | `MAX_INTENTS_CAPACITY = 2048`; FIFO eviction limits on caches (`cap = 1024`). |
| **Rule 4: Function Length** | <= 60 lines per routine | Modular helper architecture; zero monolithic procedures. |
| **Rule 5: Assertion Density** | >= 2 assertions per function | Pre-condition and post-condition invariants validated in every routine. |
| **Rule 6: Smallest Scope** | Encapsulated Manager State | State mutation strictly confined to typed manager class instances with bounded capacity; zero raw mutable module-level globals. |
| **Rule 7: Check Returns & Parameters** | Strict input validation | EIP-55 checksum, calldata byte limits (128 KB), wei spending caps. |
| **Rule 8: Minimal Metaprogramming** | Zero dynamic code evaluation | Strict Pydantic schemas; zero `eval()`, `exec()`, or dynamic monkey-patching. |
| **Rule 9: Restrict Pointer Indirection** | Single-level reference traversal | Flat contiguous array indexing `((i-1) >> 1)` rather than deep pointer-node trees. |
| **Rule 10: Static Analysis & Tests** | 100% test pass rate, 0 warnings | 104/104 passing test suite (including 5,000-case Hypothesis property fuzz tests) & 0 flake8 warnings. |

---

## 5. Verification & Testing Matrix

The repository contains an exhaustive test suite covering unit, white-box, property-based fuzzing, and end-to-end integration:

```
tests/test_audit.py .............. [ 12%]
tests/test_blackbox.py ........... [ 21%]
tests/test_creditcoin.py ......... [ 55%]
tests/test_fuzz_merkle.py ........ [ 59%]
tests/test_merkle_tree.py ........ [ 61%]
tests/test_relay.py .............. [ 65%]
tests/test_schemas.py ............ [ 74%]
tests/test_server.py ............. [ 80%]
tests/test_whitebox.py ........... [ 91%]
tests/test_workflow.py ........... [ 97%]
tests/test_x402.py ............... [100%]

============================= 104 passed in 10.39s =============================
```

---

## 6. Quickstart & Verification

```bash
# 1. Clone & Run Complete Test Suite (104/104 Passing)
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp
make test

# 2. Launch Interactive Terminal Demo (Offline Mock Relay)
make demo

# 3. Register with Claude Desktop / Claude Code
# Add to ~/.claude.json or claude_desktop_config.json:
{
  "mcpServers": {
    "agent-keeper": {
      "command": "python3",
      "args": ["-m", "agent_keeper.server"],
      "cwd": "/path/to/agent-keeper-mcp"
    }
  }
}
```
