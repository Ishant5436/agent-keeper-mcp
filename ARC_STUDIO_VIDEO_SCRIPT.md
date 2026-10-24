# Arc Studio Hackathon Video Walkthrough Script (60–90 Seconds)

**Target Hackathon:** Arc Microgrants: Built with Arc Studio (DoraHacks)  
**Submission Requirement:** A short video demonstrating the build process inside Arc Studio as well as the live mainnet transaction.  
**Tools to Record:** macOS QuickTime Screen Recording (`Cmd + Shift + 5`) or Loom.

---

## Video Breakdown & Timestamped Action Guide

### [00:00 – 00:15] Section 1: Arc Studio Prompt & Workspace Setup
* **On Screen:** Browser tab open to `https://studio.arc.io/app/...`.
* **Action:** Show the Arc Studio coding agent interface with the prompt inputted and generated files visible in the project tree (`ArcAgentEscrow.sol`, `X402Receipt.sol`, frontend).
* **Voiceover / Spoken Script:**
  > "Hello. This is AgentKeeper Studio, an autonomous agent execution gateway and native USDC escrow protocol engineered natively for Circle's Arc Layer-1 blockchain using Arc Studio. In Arc Studio, we prompted the coding agent to build a non-custodial A2A payment router and conditional escrow contract enforcing Holzmann Power of 10 deterministic safety invariants."

### [00:15 – 00:35] Section 2: Smart Contract Architecture & Verification
* **On Screen:** Click into `ArcAgentEscrow.sol` and show the compilation/testing status in Arc Studio or terminal (`148 passed`).
* **Action:** Scroll briefly through the non-reentrant mutex, `depositEscrow`, `releaseEscrow`, and `refundEscrow`.
* **Voiceover / Spoken Script:**
  > "On Arc Mainnet, USDC functions as the 18-decimal native gas asset. Our contract manages software-to-software micro-escrow and instant agent payments without token allowances. It features single-slot non-reentrancy locks, strict function bounds under 60 lines, and verified EIP-712 permit replay protection. All 148 automated unit and fuzz tests pass with 100% green status."

### [00:35 – 01:05] Section 3: Live Application Walkthrough & On-Chain Settlement
* **On Screen:** Switch to the live web interface (`web/index.html` or deployed URL).
* **Action:**
  1. Show connected wallet with native USDC balance.
  2. Enter Task ID (`agent-task-001`), Provider Address, and Amount (`0.01 USDC`).
  3. Click **Deposit Escrow on Arc** and show transaction prompt.
  4. Show the EIP-712 permit tab and click **Broadcast settle(...) on Arc**.
* **Voiceover / Spoken Script:**
  > "Here in the AgentKeeper Studio interface, an autonomous agent or human operator connects via Arc Testnet or Mainnet. We can deposit native USDC into a time-locked task escrow for an AI solver, or execute an instant micropayment. Upon task verification, the funds are released non-custodially to the solver."

### [01:05 – 01:25] Section 4: Block Explorer Proof & Wrap-up
* **On Screen:** Switch to Circle Arc Block Explorer (`https://explorer.testnet.arc.io` / `https://explorer.arc.io`).
* **Action:** Show verified deployment at `0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5` and the live settlement transaction hash `0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720`.
* **Voiceover / Spoken Script:**
  > "Here is our verified deployment on Arc at address 0x589fE... and the live on-chain settlement transaction moving value in block 66163775. The entire codebase is open-source under the MIT license on GitHub. Thank you to Circle and DoraHacks."

---

## Checklist Before Submitting Video Link:
1. Upload video to YouTube (as Unlisted) or Loom / Google Drive (set to "Anyone with link can view").
2. Ensure audio is clear with zero background noise.
3. Paste the public link into the Video Walkthrough field on the DoraHacks submission form.
