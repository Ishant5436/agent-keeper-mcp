# DoraHacks BUIDL Submission Package: AgentKeeper-MCP

**Hackathon:** [KeeperHub - The Agent Economy Hackathon](https://dorahacks.io/)  
**Submission Window:** September 6 – September 18, 2026  
**Total Target Prize Pool:** $5,000 USD (Main Track + $1,000 USDC Bounty)  
**Public Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)

---

## 1. Portal Form Field Inputs (Copy-Paste Ready)

### Project Name
`AgentKeeper-MCP`

### Tagline (Elevator Pitch - 120 Chars)
`Autonomous Onchain Execution Gateway & x402 Micro-Payment Protocol Suite for AI Agents via MCP.`

### Category & Tracks
* **Primary Track:** *The Agent Economy (Main Track - $4,000 Pool)*
* **Bounty Track:** *Best KeeperHub Feature ($1,000 USDC)*

### GitHub Repository URL
`https://github.com/Ishant5436/agent-keeper-mcp`

---

## 2. Project Description (Portal Markdown Body)

### 📌 Problem Space
Autonomous AI reasoning agents (Claude, Gemini, Antigravity, OpenAI Assistants) generate high-conviction decision trees but struggle with onchain execution due to three key hurdles:
1. **Execution Reliability:** Nonce collisions, dynamic gas fee volatility, and MEV exposure increase failure rates for automated agents.
2. **Autonomous Monetization & Micro-Payments:** AI agents lack standard mechanisms to autonomously negotiate and settle HTTP 402 payment challenges for pay-per-call data and model APIs.
3. **Auditability & Trace Verification:** Autonomous multi-agent workflows require verifiable cryptographic logs and Merkle inclusion proofs to establish accountability.

### 💡 Solution: AgentKeeper-MCP
`AgentKeeper-MCP` is an open-source, high-assurance Model Context Protocol (MCP) gateway that interfaces AI agents with KeeperHub's execution infrastructure.

### 🛠️ Core Capabilities
* **`keeper_execute_tx`**: Executes transactions with automated nonce reservation and idempotent hashing. Supports live HTTP REST forwarding when configured with `KEEPERHUB_API_KEY` and deterministic local state execution for sandbox verification.
* **`keeper_x402_settle`**: Autonomously intercepts and settles HTTP 402 Payment Required challenges using authentic 65-byte EIP-712 structured payment permits.
* **`keeper_audit_verify`**: Maintains an immutable cryptographic state ledger and verifies Merkle inclusion proofs for executed tasks.
* **`keeper_agent_balance`**: Inspects operational agent spending limits and multi-chain test/live treasury allocations across Base, Arbitrum, and Ethereum.

### 🛡️ NASA Power of 10 Safety Architecture
Built to the rigorous standards of Gerard J. Holzmann's NASA Power of 10:
* **Bounded Loops:** Deterministic upper bound ($N \le 10$) on all retry loops.
* **Strict EIP-55 Invariants:** Strict mixed-case checksum validation rejecting corrupted addresses.
* **Autonomous Budget Guard:** Strict single-call ($5.00 USDC) and native transfer ceiling (0.10 ETH) to prevent balance drains.
* **Assertion Density:** $\ge 2$ assertions per function enforcing execution invariants.
* **100% Test Coverage:** 23 passing tests with 0 Ruff linter warnings.

---

## 3. Upstream Bounty PR Package (`KeeperHub/keeperhub`)

* **Upstream Pull Request:** [https://github.com/KeeperHub/keeperhub/pull/2188](https://github.com/KeeperHub/keeperhub/pull/2188)
* **Status:** Open & Verified (8/8 Vitest tests passing, 0 TypeScript errors)
* **Plugin Implementation:** Native `agent-gateway` plugin supporting `check-credit` and `sign-payment` actions for workflow graphs.
* **Standalone FastMCP Package:** Available in [`upstream_pr/`](https://github.com/Ishant5436/agent-keeper-mcp/tree/main/upstream_pr).


---

## 4. 2-Minute Demo Video Walkthrough Script

| Time | Visual on Screen | Voiceover / Text |
| :--- | :--- | :--- |
| **0:00 - 0:25** | Terminal running `./demo.py` Step 1 | *"Welcome to AgentKeeper-MCP. Here we inspect our autonomous agent's multi-chain treasury and spending limits."* |
| **0:25 - 0:55** | Step 2 (x402 Settlement) | *"When an AI agent encounters a paid data API with an HTTP 402 challenge, AgentKeeper constructs an authentic EIP-712 micro-payment permit, signs it, and unlocks the resource."* |
| **0:55 - 1:30** | Step 3 (Onchain Relay) | *"Next, the agent executes a transaction payload on Base. The relay manages nonce assignment, idempotency tracking, and transaction confirmation."* |
| **1:30 - 2:00** | Step 4 (Merkle Proof) & Pytest | *"Finally, the agent cryptographically verifies the Merkle inclusion receipt against the state ledger. 23/23 tests pass with NASA Power of 10 safety invariants."* |
