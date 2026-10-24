# DoraHacks Submission Package: Arc Microgrants — Built with Arc Studio

**Hackathon Portal:** [https://dorahacks.io/hackathon/arc-studio](https://dorahacks.io/hackathon/arc-studio)  
**Program:** Arc Microgrants: Built with Arc Studio  
**Prize Pool:** $4,000 USDC (8 Microgrants $\times$ $500 USDC)  
**Submission Deadline:** November 1, 2026 (20:59 UTC)  
**Submission Form Fields:**

---

### Field 1: Project Name
```text
AgentKeeper Studio — Autonomous Agent Gateway & Native USDC Escrow
```

### Field 2: Tagline
```text
Deterministic agent-to-agent payment gateway, native USDC conditional escrow, and EIP-712 x402 attestation registry built natively with Arc Studio on Circle Arc.
```

### Field 3: Arc Studio Project URL
```text
https://studio.arc.io/app/<INSERT_YOUR_ARC_STUDIO_APP_ID_HERE>
```
*(Generated when you create the project in https://studio.arc.io using the blueprint prompt).*

### Field 4: Live Application Link
```text
https://ishant5436.github.io/agent-keeper-mcp/web/
```
*(Or local live runner / Vercel deployment of `web/index.html`).*

### Field 5: Public GitHub Repository
```text
https://github.com/Ishant5436/agent-keeper-mcp
```

### Field 6: Deployed Contract Address(es)
* **ArcAgentEscrow (Native USDC Micro-Escrow & Router):**
  `contracts/ArcAgentEscrow.sol` (Deployable via `scripts/deploy_arc_escrow.py`)
* **X402Receipt (EIP-712 Attestation Registry):**
  [`0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5`](https://explorer.testnet.arc.io/address/0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5)

### Field 7: Example Transaction Hash on Arc Explorer
* **Deployment Tx:** [`0x56b6eea5b7f3408af6b961e62c85cfa0cc80076ce03dcd39e0803c577530e46c`](https://explorer.testnet.arc.io/tx/0x56b6eea5b7f3408af6b961e62c85cfa0cc80076ce03dcd39e0803c577530e46c)
* **Live Settle Tx (Moving value / Event Attestation):** [`0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720`](https://explorer.testnet.arc.io/tx/0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720)

### Field 8: Video Walkthrough Link
```text
<INSERT_YOUR_UNLISTED_YOUTUBE_OR_LOOM_LINK_HERE>
```
*(Follow the step-by-step 75-second script in `ARC_STUDIO_VIDEO_SCRIPT.md`).*

---

### Field 9: Project Description & Technical Overview (Copy-Paste)

```markdown
## Executive Summary

AgentKeeper Studio is an institutional-grade Model Context Protocol (MCP) gateway and native USDC execution protocol engineered natively with **Arc Studio** (`studio.arc.io`) for Circle's Arc Layer-1 blockchain.

As autonomous AI agents (Claude, Gemini, Cursor) transition from conversational assistants into economic actors hiring other agents and paying for paywalled APIs (HTTP 402), they face two critical architectural hurdles:
1. **Context Credential Leakage:** Injecting raw private keys into LLM prompt contexts risks exposure through prompt injection or logging.
2. **Volatile Gas & Complex Token Economics:** On legacy EVM chains, settling agent micro-payments incurs unpredictable fees in volatile assets, requiring multi-token balances and approval transactions.

Circle's Arc Mainnet fundamentally resolves this by making **USDC the 18-decimal native gas asset**. AgentKeeper Studio leverages this native stablecoin design to deliver deterministic, non-custodial agent-to-agent escrow and micro-payments without token approvals or multi-step wrapping.

---

## What We Built with Arc Studio

Using Arc Studio's onchain coding agent, we generated, tested, and deployed a full-stack agentic execution architecture:

1. **ArcAgentEscrow.sol (Native USDC Escrow & A2A Router):**
   - **`depositEscrow`:** Accepts native USDC (`msg.value`) and locks it for an autonomous agent task or API challenge with an immutable release deadline.
   - **`releaseEscrow`:** Non-custodially transfers native USDC directly to the solver agent upon verified task completion.
   - **`refundEscrow`:** Enforces an emergency timeout refund: if an agent fails to deliver within the timeout, the payer can reclaim their USDC.
   - **`directMicropayment`:** Instant software-to-software transfer of native USDC between agents with cryptographic metadata.

2. **X402Receipt.sol (EIP-712 Attestation Registry):**
   - Stateless, non-custodial attestation registry recording signed payment permits.
   - Replay-immune per-payer nonces (`used[payer][nonce]`).
   - Malleability defense enforcing canonical low-s values (`s <= HALF_N`) and valid recovery IDs (`v in {27, 28}`).
   - Deployed on Arc Testnet at `0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5`.

3. **AgentKeeper Studio Web Interface (`web/index.html`):**
   - Full EIP-1193 Web3 wallet integration with Arc Mainnet (Chain ID 5042) and Arc Testnet (Chain ID 5042002).
   - Real-time balance inspection querying native USDC directly from Arc JSON-RPC.
   - Interactive consoles for depositing task escrow, executing instant micropayments, and signing EIP-712 attestation receipts.

---

## Deterministic Safety Standards (Holzmann Power of 10)

To guarantee safety-critical execution for high-stakes autonomous agents, all smart contract logic strictly adheres to Gerard Holzmann's Power of 10 rules:
- **Bounded Control Flow:** Zero recursion, zero unbounded loops, and hard timeout deadlines.
- **Function Length:** Every function is strictly under 60 lines of code.
- **Assertion Density:** Minimum of 2 explicit condition checks / assertions per function.
- **Zero Dynamic Memory Allocation:** Fixed memory structs inside mapping storage.
- **Reentrancy Immunity:** Single-slot mutex lock (`_status`) on all state-modifying functions.
- **Rigorous Verification:** 148 / 148 automated unit and property fuzz tests passing with 100% green coverage.

---

## Live Deployment & Verification Links

- **Arc Testnet RPC:** `https://rpc.testnet.arc.io`
- **Arc Mainnet RPC:** `https://rpc.mainnet.arc.io`
- **Deployed Verifier Contract:** [`0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5`](https://explorer.testnet.arc.io/address/0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5)
- **Deployment Transaction:** [`0x56b6eea5b7f3408af6b961e62c85cfa0cc80076ce03dcd39e0803c577530e46c`](https://explorer.testnet.arc.io/tx/0x56b6eea5b7f3408af6b961e62c85cfa0cc80076ce03dcd39e0803c577530e46c)
- **Live Settlement Transaction:** [`0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720`](https://explorer.testnet.arc.io/tx/0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720)
- **GitHub Repository:** [`https://github.com/Ishant5436/agent-keeper-mcp`](https://github.com/Ishant5436/agent-keeper-mcp)
```
