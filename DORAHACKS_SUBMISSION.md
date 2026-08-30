# AgentKeeper-MCP — BUIDL CTC 2026 Fall Submission Package

**Hackathon:** BUIDL CTC 2026 Fall  
**Prize Pool:** $15,000 USD  
**Track:** AI  
**BUIDL URL:** [https://dorahacks.io/buidl/48196](https://dorahacks.io/buidl/48196)  
**Repository:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**Upstream PR:** [KeeperHub/keeperhub #2188](https://github.com/KeeperHub/keeperhub/pull/2188)  

---

## 1. Project Overview

* **Project Name:** AgentKeeper-MCP
* **Tagline:** Non-custodial onchain transaction relay, HTTP 402 micro-payments, and Merkle state verification for autonomous AI agents across EVM networks.
* **Supported Chains:** Ethereum, Base, Arbitrum, Optimism, Mantle, Creditcoin, and Sepolia Testnet.
* **Test Coverage:** 23/23 Automated Pytest Suite Passing (100% Invariant Validation).

---

## 2. Architecture & Deliverables

1. **Non-Custodial Transaction Gateway:** Sanitizes calldata, enforces EIP-55 checksums, and caps value transfers before execution.
2. **HTTP 402 Micropayments:** EIP-712 typed data signing for AI-to-AI data queries with automated budget enforcement.
3. **Merkle Audit State Proofs:** Cryptographic execution integrity verified against tamper-proof root hashes.
4. **Deterministic Safety Invariants:** Strict bounded loops, zero dynamic heap recursion, and assertion density >= 2 across all tools.

---

## 3. Verification Command

```bash
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp
python3 -m pytest -v
```
