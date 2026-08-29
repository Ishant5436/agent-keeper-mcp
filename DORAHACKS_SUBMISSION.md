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
Autonomous AI reasoning agents (Claude, Gemini, Antigravity, OpenAI Assistants) generate high-conviction decision trees but fail in real-world onchain execution due to three critical bottlenecks:
1. **Execution Vulnerabilities:** Nonce collisions, dynamic gas fee spikes, and MEV front-running cause high transaction failure rates.
2. **Lack of Native Autonomous Payments:** AI agents cannot autonomously settle HTTP 402 micro-payment challenges for paid data streams and compute resources.
3. **Auditability Deficits:** Decentralized multi-agent economies require cryptographically verifiable receipts and Merkle inclusion proofs.

### 💡 Solution: AgentKeeper-MCP
`AgentKeeper-MCP` is an open-source, high-assurance Model Context Protocol (MCP) gateway that connects any AI agent directly to KeeperHub's onchain reliability and execution infrastructure.

### 🛠️ Core Capabilities
* **`keeper_execute_tx`**: Routes transactions through KeeperHub's MEV-shielded private relay with automated nonce reservation and dynamic gas resubmission.
* **`keeper_x402_settle`**: Autonomously intercepts and settles HTTP 402 Payment Required challenges using authentic EIP-712 structured payment permits.
* **`keeper_audit_verify`**: Maintains an immutable cryptographic state ledger and verifies Merkle inclusion proofs for historical agent actions.
* **`keeper_agent_balance`**: Multi-chain operational treasury tracking across Base, Arbitrum, and Ethereum Mainnet with strict safety budget limits.

### 🛡️ NASA Power of 10 Safety Architecture
Built to the rigorous standards of Gerard J. Holzmann's NASA Power of 10:
* **Bounded Loops:** Deterministic upper bound ($N \le 10$) on all retry loops.
* **Strict EIP-55 Invariants:** Strict mixed-case checksum validation rejecting corrupted addresses.
* **Autonomous Budget Guard:** Strict single-call ($5.00 USDC) and native transfer ceiling (0.10 ETH) to prevent unauthorized treasury drains.
* **Assertion Density:** $\ge 2$ assertions per function enforcing execution invariants.
* **100% Test Coverage:** 23 passing tests with 0 Ruff linter warnings.

---

## 3. Upstream Bounty PR Package (`keeperhub/keeperhub`)

To claim the **$1,000 USDC Best Feature Bounty**, submit the pull request directly from your machine:

```bash
cd /Users/ishantpanchal/agent-keeper-mcp/upstream_pr
# View description and plugin code
cat PR_DESCRIPTION.md
cat keeper_mcp_plugin.py
```

### Upstream PR Title:
`feat: native Model Context Protocol (MCP) server integration for autonomous AI agents`

---

## 4. 2-Minute Demo Video Walkthrough Script

| Time | Visual on Screen | Voiceover / Text |
| :--- | :--- | :--- |
| **0:00 - 0:25** | Terminal running `./demo.py` Step 1 | *"Welcome to AgentKeeper-MCP. Here we inspect our autonomous agent's multi-chain treasury across Base, Arbitrum, and Ethereum with strict spending limits."* |
| **0:25 - 0:55** | Step 2 (x402 Settlement) | *"When an AI agent encounters a paid data API with an HTTP 402 challenge, AgentKeeper constructs an authentic EIP-712 micro-payment permit, signs it, and unlocks the resource in milliseconds."* |
| **0:55 - 1:30** | Step 3 (Onchain Relay) | *"Next, the agent executes an MEV-protected transaction on Base. KeeperHub handles nonce reservation, gas pricing, and transaction confirmation."* |
| **1:30 - 2:00** | Step 4 (Merkle Proof) & Pytest | *"Finally, the agent cryptographically verifies the Merkle inclusion receipt against the state ledger. 23/23 tests pass with NASA Power of 10 safety invariants."* |
