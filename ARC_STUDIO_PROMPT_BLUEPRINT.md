# Arc Studio Prompt Blueprint & Architecture Specification

Use this exact intent prompt inside **Arc Studio** (`https://studio.arc.io`) to generate or replicate the on-chain application for the **Arc Microgrants: Built with Arc Studio** track.

---

## 1. Primary Natural Language Intent (Copy-Paste into studio.arc.io)

```text
Build a non-custodial agent-to-agent payment gateway and conditional escrow smart contract on Circle Arc Mainnet where USDC is the 18-decimal native gas asset.

Requirements:
1. Smart Contract Architecture (ArcAgentEscrow.sol):
   - Escrow State Machine: NONEXISTENT, ACTIVE, RELEASED, REFUNDED.
   - depositEscrow(bytes32 taskId, address payable provider, uint256 timeoutSeconds): accepts native USDC (msg.value), validates provider address and timeout, and locks funds for an autonomous agent task.
   - releaseEscrow(bytes32 taskId): only original payer can release; transfers native USDC to the provider using non-reentrant execution.
   - refundEscrow(bytes32 taskId): allows payer to reclaim native USDC if block.timestamp exceeds releaseDeadline.
   - directMicropayment(address payable recipient, bytes32 metadata): instant software-to-software transfer of native USDC between agents.
   - Non-Reentrancy Guard: single-slot mutex lock (_status = 1 for unlocked, 2 for locked).
   - Deterministic Safety Standards (Gerard Holzmann Power of 10): all functions <= 60 lines, minimum 2 assertion checks per function, zero unbounded loops, zero dynamic heap memory.

2. Verifier & Receipt Registry Integration (X402Receipt.sol):
   - EIP-712 typed payment permit verification with domain separator tracking block.chainid.
   - Replay-immune per-payer nonces (used[payer][nonce]).
   - Signature malleability prevention (s <= secp256k1n / 2 and v in {27, 28}).

3. Web Interface (AgentKeeper Studio):
   - Modern dark UI supporting Circle Arc Mainnet (Chain ID 5042) and Arc Testnet (Chain ID 5042002).
   - Real-time native USDC balance telemetry via eth_getBalance.
   - Interactive forms to deposit escrow, release funds, trigger emergency refunds, and sign EIP-712 x402 payment permits.
   - Direct transaction explorer links to explorer.arc.io.
```

---

## 2. Step-by-Step Arc Studio Workflow

1. Navigate to **[https://studio.arc.io](https://studio.arc.io)** in your browser.
2. Click **Create New App** or start a new workspace.
3. Paste the intent prompt above into the coding agent input box.
4. Let the Arc Studio agent:
   - Generate `ArcAgentEscrow.sol` and `X402Receipt.sol`.
   - Run the built-in contract unit tests.
   - Scaffold the frontend interface.
5. In the Arc Studio environment, connect your test wallet and deploy the contracts to **Arc Testnet (5042002)** or **Arc Mainnet (5042)**.
6. Note your generated Arc Studio project URL from the browser address bar:
   `https://studio.arc.io/app/<PROJECT_UUID>`
   *(This URL is a mandatory field for the DoraHacks submission form).*

---

## 3. On-Chain Verification Artifacts

* **Deployed Verifier Contract (Arc Testnet):** [`0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5`](https://explorer.testnet.arc.io/address/0x589fE98EDB63F3e158DdE791C5144369fAeC4cE5)
* **Live EIP-712 Settlement Proof:** [`0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720`](https://explorer.testnet.arc.io/tx/0x04ce874ecd72e5918f93d84d09f3484704c5345580620ce300914292b6f12720)
* **Automated Test Suite Parity:** 148 / 148 automated unit & fuzz tests passing in `agent-keeper-mcp`.
