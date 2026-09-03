# AgentKeeper-MCP — KeeperHub Agent Economy Hackathon Submission

**Hackathon:** KeeperHub - The Agent Economy Hackathon  
**Prize Pool:** $5,000 USD  
**Track:** AI Agents / Autonomous Web3 Infrastructure / MCP  
**GitHub Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Demo Video:** [https://github.com/Ishant5436/agent-keeper-mcp/raw/main/assets/agent_keeper_demo.mp4](https://github.com/Ishant5436/agent-keeper-mcp/raw/main/assets/agent_keeper_demo.mp4)  
**Upstream Pull Request:** [KeeperHub/keeperhub #2188](https://github.com/KeeperHub/keeperhub/pull/2188)  
**BUIDL Profile:** [https://dorahacks.io/buidl/48196](https://dorahacks.io/buidl/48196)  

---

## 1. Project Overview & Problem Statement

### The Problem
AI agents are probabilistic by design. They interpret natural language with varying degrees of certainty. However, onchain state machines and value transfers are completely deterministic and unforgiving. When an autonomous agent is instructed to move funds or execute a contract call, standard probabilistic LLM generation risks hallucinated parameters, reinterpretation of transaction payloads, unprotected mempool exposure, or budget draining.

### The Solution: AgentKeeper-MCP
AgentKeeper-MCP provides an enterprise-grade Model Context Protocol (MCP) gateway that connects frontier AI reasoning engines (Claude, Gemini, local Ollama models) directly into KeeperHub's execution infrastructure. 

By enforcing Deterministic Safety Invariants across all client tools, AgentKeeper-MCP guarantees that:
* Private keys are never passed into LLM prompt contexts or agent memory.
* Transaction execution is constrained by deterministic parameter validation and spending caps.
* Every onchain state change generates a verifiable cryptographic receipt.

---

## 2. FastMCP Tool Architecture

AgentKeeper-MCP exposes four production-hardened FastMCP tools:

### 1. `keeper_execute_tx` (MEV-Protected Onchain Execution)
* Sanitizes calldata, enforces EIP-55 address checksums, and restricts value transfers to pre-approved maximum thresholds.
* Routes transactions through KeeperHub private relay endpoints when `KEEPERHUB_API_KEY` is configured; otherwise executes deterministic local simulation with full EIP-1559 gas calculation for offline judging.
* Supports automatic nonce reconciliation, smart gas estimation, and idempotency tracking (`idempotency_key`) to eliminate double-spend race conditions.

### 2. `keeper_x402_settle` (Autonomous HTTP 402 Gateway)
* Implements the emerging agent-to-agent HTTP 402 Payment Required specification.
* Evaluates incoming micro-payment challenges against local agent policy limits (per-transaction caps and daily spending budgets).
* Constructs and signs EIP-712 typed structured data, returning standardized bearer authorization tokens without granting the agent raw private key custody.

### 3. `keeper_audit_verify` (Flat Array Merkle Proof Verifier)
* Verifies transaction execution integrity against onchain Merkle roots using a zero-heap `FlatMerkleTree` implementation.
* Computes inclusion proofs with logarithmic complexity ($\mathcal{O}(\log N)$) to prove that a task was executed at a specific block number without tampering.

### 4. `keeper_agent_balance` (Multi-Chain Treasury Inspector)
* Aggregates real-time native and token balances across 8 EVM networks: Base (8453), Arbitrum (42161), Optimism (10), Creditcoin (1024 / 102031), Mantle (5000), Ethereum (1), and Sepolia (11155111).
* Enforces isolated budget accounting so autonomous agents cannot exhaust multi-chain operational gas.

---

## 3. Engineering Rigor & Safety Invariants

AgentKeeper-MCP adheres strictly to Deterministic Safety Invariants (Power of 10):
* **Deterministic Control Flow:** Bounded loops with explicit upper bounds; zero unbounded `while` loops or recursion.
* **Zero Dynamic Heap Allocations on the Hot Path:** Fixed-capacity data structures and flat array indexing for Merkle proofs.
* **High Assertion Density:** Minimum 2 explicit parameter and invariant assertions per function.
* **Smallest Scope:** Strictly localized variable scopes and immutable schemas.
* **Full Test Coverage:** 67/67 automated tests passing across unit, white-box invariant, and 5,000-case Hypothesis property-based fuzz test suites.

---

## 4. Verification & Live Execution Commands

### Run the Full Automated Test Suite (67/67 Passing)
```bash
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp
python3 -m pytest -v
```

### Run the Interactive Autonomous Live Demo
```bash
python3 demo.py
```

### Upstream Open Source Contribution
Inspect the upstream integration submitted to the official KeeperHub core repository:
* Pull Request: [KeeperHub/keeperhub #2188](https://github.com/KeeperHub/keeperhub/pull/2188)
