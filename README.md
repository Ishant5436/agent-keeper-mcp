<p align="center">
  <img src="assets/logo.jpg" alt="AgentKeeper-MCP Arc Mainnet Logo" width="160" height="160" style="border-radius: 24px;" />
</p>

# AgentKeeper-MCP

> A deterministic, non-custodial Model Context Protocol (MCP) execution gateway for autonomous AI agents on Arc Mainnet with native USDC gas settlement and HTTP 402 micro-payments.

[![Tests](https://img.shields.io/badge/tests-139%2F139%20passing-brightgreen)](https://github.com/Ishant5436/agent-keeper-mcp)
[![CI](https://github.com/Ishant5436/agent-keeper-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Ishant5436/agent-keeper-mcp/actions)
[![Arc Mainnet](https://img.shields.io/badge/Arc%20Mainnet-Native%20USDC%20(5042)-teal)](https://explorer.arc.io)
[![Creditcoin](https://img.shields.io/badge/Creditcoin%203.0-Attestcoin%20Settlement-blue)](src/agent_keeper/creditcoin.py)
[![Safety Checklist](https://img.shields.io/badge/Internal%20Safety%20Checklist-7%2F7%20areas-success)](iso9001_compliance/QUALITY_MANUAL.md)
[![Safety Standard](https://img.shields.io/badge/Safety%20Standard-Deterministic%20Invariants-purple)](src/agent_keeper/audit.py)
[![Upstream Merged](https://img.shields.io/badge/KeeperHub-PR%20%232547%20%26%20%232640%20(Merged)-brightgreen)](https://github.com/KeeperHub/keeperhub/pull/2547)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

> **Arc Mainnet Workflow Walkthrough (local, no broadcast):** `python3 scripts/demo_arc_mainnet.py` | **Instant MCP Demo:** `make demo` | **Arc verifier:** [`contracts/X402Receipt.sol`](contracts/X402Receipt.sol) (see "Arc x402 Receipt Verifier" below; not yet deployed)

![AgentKeeper MCP Demo](assets/agent_keeper_demo.gif)

---

## The Problem: Why Agents Break Onchain

If you give an autonomous agent direct access to an RPC or raw private key, three critical failures happen:

1. **Context Credential Leaks:** The moment an execution errors out, the model includes raw private keys or RPC URLs in its chat history or debug prompts.
2. **Nonce Collisions & Gas Drain:** High-frequency agents retry transactions without tracking mempool states, burning capital on stuck nonces during fee spikes.
3. **The Paywall Dead-End:** When an agent queries paid data services returning `HTTP 402 Payment Required`, it has no standardized way to sign a micro-payment and continue execution. On Arc Mainnet, where USDC is the native gas asset, agents need a native settlement mechanism that manages USDC spending ceilings deterministically.

---

## The Solution: Guarded Gateway Architecture

AgentKeeper sits as a local middleware between the agent runtime and blockchain networks. Private keys stay isolated in local memory, while the agent interacts solely through typed, bounded tools:

```
┌────────────────────────────────────────────────────────┐
│      Autonomous Agent Client (Host / IDE / Daemon)     │
└──────────────────────────┬─────────────────────────────┘
                           │ (stdio / FastMCP)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   AgentKeeper-MCP                      │
│                                                        │
│  [1] keeper_execute_tx     ───►  Local Key Sandbox     │
│  [2] keeper_x402_settle    ───►  EIP-712 Spend Budget  │
│  [3] keeper_audit_verify   ───►  Merkle Proof Engine   │
│  [4] keeper_agent_balance  ───►  Multi-Chain Balances  │
│  [5] keeper_creditcoin_settle ►  Attestcoin L1 Escrow  │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
       Circle Arc Mainnet          x402 Paywalled APIs
   (Chain ID 5042 / Native USDC)   (Per-token Data Feeds)
```

---

## Core Capabilities

### 1. Non-Custodial Key Sandbox (`keeper_execute_tx`)
* Validates target contracts, calldata schemas, and gas parameters before signing.
* Implements an in-memory FIFO idempotency cache (`cap = 1024`, Keccak256 deduplication) to prevent duplicate execution during network latency.
* Supports deterministic pre-flight simulation (`dry_run=True`) without state mutation or network broadcast.
* Never passes raw cryptographic keys to the LLM context.

### 2. Workflow Planning & Dry-Run Composition (`keeper_plan_workflow`)
* Composes multi-step agent workflows across execution, micropayments, and settlements into a single verified plan.
* Pre-flight validates all step schemas and calculates aggregate gas, native value, and USDC budget requirements.
* Bounded to a maximum of 16 steps per workflow to eliminate non-deterministic loop reinterpretation.

### 3. Autonomous HTTP 402 Micropayments (`keeper_x402_settle`)
* Signs an EIP-712 `Permit(payer, payee, amount, nonce, deadline)` under a per-permit random 256-bit nonce, capped by a cumulative spend limit (`MAX_AUTONOMOUS_PAYMENT_USDC`).
* The permit is bound to a verifying contract you deploy: [`contracts/X402Receipt.sol`](contracts/X402Receipt.sol). The address comes from `ARC_X402_VERIFIER` (EIP-55 checksum). **If it is unset or invalid the tool fails closed** and returns an error; there is no default address.
* The response includes a `permit` object (payer, payee, amount, nonce as a decimal string, deadline, chainId, verifyingContract). Together with `signature` it is exactly what `X402Receipt.settle(...)` needs, so the output is redeemable on-chain by anyone (a test does this end to end on an in-memory EVM). Both demos (`make demo`, `scripts/demo_arc_mainnet.py`) need `ARC_X402_VERIFIER` set for their x402 step; without it they print the fail-closed error.
* Defaults to Arc Mainnet (chain 5042). Other tools' chain defaults are unchanged; `keeper_x402_settle` requests for any other chain currently fail closed because no verifier is configured for them.

#### Arc x402 Receipt Verifier

`contracts/X402Receipt.sol` is a small (68 lines, Solidity ^0.8.20, no dependencies) non-custodial receipt registry. `settle(payer, payee, amount, nonce, deadline, signature)` verifies the payer's EIP-712 signature (domain: name, version, chainId, `verifyingContract = address(this)`), rejects expired deadlines and reused `(payer, nonce)` pairs, rejects non-canonical (high-s) signatures, records the nonce and emits `Settled(payer, payee, amount, nonce)`.

* It holds no funds and moves none: nothing is payable, it makes no token calls, and it has no owner, admin or upgrade path. It is a signed-receipt registry, not a payment rail. Only EOA signers are supported (`ecrecover`, no EIP-1271).
* Compiled with `--evm-version paris` (no `PUSH0`) because Arc's opcode support has not been verified here.
* Tested in-process (solc + eth-tester): valid signature accepted; wrong signer, tampered fields, expired deadline, replayed nonce, wrong chainId, wrong verifying contract, high-s twin and malformed signatures rejected. These tests do not exercise Arc itself.

```bash
# 1. Dry run (default): compile, print the unsigned deployment tx, gas and USDC cost estimate. No key is read.
python3 scripts/deploy_arc_verifier.py

# 2. Deploy (operator, funded wallet, own shell). Reads AGENT_PRIVATE_KEY from the environment only.
export AGENT_PRIVATE_KEY=0x...
python3 scripts/deploy_arc_verifier.py --broadcast
export ARC_X402_VERIFIER=<deployed address>   # placeholder: set to the address the script prints

# 3. One live settle() call against the deployed verifier (dry run by default; --broadcast sends).
python3 scripts/broadcast_live_arc_tx.py
python3 scripts/broadcast_live_arc_tx.py --broadcast
```

Status: contract, tests and scripts are done. **Not yet done:** deployment on Arc Mainnet and the live `settle()` transaction, which need a wallet funded with a little native USDC. Deployed address: _pending_. Transaction hash: _pending_.

### 4. Merkle Audit Trail (`keeper_audit_verify`)
* Builds cryptographic inclusion proofs for all relay actions using a flat array Merkle heap.
* Allows agents to independently audit state proofs before triggering downstream dependent actions.

### 5. Multi-Chain Budgeting (`keeper_agent_balance`)
* Real-time multi-chain RPC balance queries across Base, Arbitrum, Ethereum, and Creditcoin.

### 6. Creditcoin 3.0 Attestcoin Intent Settlement (`keeper_creditcoin_settle`)

Creditcoin 3.0 is a decentralized Layer 1 EVM consensus network designed for real-world asset (RWA) lending and cross-chain settlement. Under the **Attestcoin Protocol**, cross-chain data and transaction receipts are attested without relying on centralized oracles or vulnerable multi-sig bridges.

`AgentKeeper-MCP` implements an autonomous **Attestcoin Cross-Chain Solver Escrow Gateway**:
1. **Collateral Escrow on Creditcoin L1:** The agent locks CTC escrow collateral for a target intent ID with an authorized solver address via `register_escrow(intent_id, solver_address, amount_ctc)`.
2. **Off-Chain / Cross-Chain Execution:** An external solver executes the requested task (e.g. token swap, liquidity provisioning, or paywalled data query) on an external EVM chain (Arbitrum, Base, Mantle, or Arc).
3. **Dynamic Oracle Root Anchoring:** The Attestcoin protocol validates the transaction's block header against on-chain consensus. `CreditcoinSettlementManager` queries the source-chain JSON-RPC to confirm that the candidate Merkle root matches the mined block's `receiptsRoot`, `stateRoot`, or `transactionsRoot` under a deny-by-default security policy.
4. **Flat Merkle Tree Inclusion Proof ($\mathcal{O}(\log N)$):** The solver generates an Attestcoin inclusion proof constructed via `FlatMerkleTree`. The tree validates that the leaf payload (`intent_id:source_chain:source_tx_hash:expected_recipient`) is mathematically contained in the attested Merkle root without recursive stack overhead. Proof depth is strictly bounded to $\le 64$.
5. **Atomic CTC Escrow Reimbursement:** Upon cryptographic proof validity and solver address verification, the locked CTC collateral is immediately released to the solver. Bounded ring-buffer state storage (`MAX_INTENTS_CAPACITY = 2048`) prevents memory leaks and state exhaustion attacks.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Autonomous Agent│       │  AgentKeeper    │       │  Creditcoin 3.0 │
│   (LLM Client)  │       │   MCP Gateway   │       │   EVM L1 Escrow │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         │  1. Request Solver Task │                         │
         │────────────────────────►│  2. Lock CTC Collateral │
         │                         │────────────────────────►│
         │                         │                         │
         │                         │                         │ ──┐
         │                         │                         │   │ External Solver
         │                         │                         │   │ executes on Base/Arb
         │                         │                         │ ◄─┘
         │                         │                         │
         │                         │  3. Attestcoin Proof    │
         │                         │     (Receipt + Branch)  │
         │                         │◄────────────────────────│
         │                         │                         │
         │                         │  4. FlatMerkleTree      │
         │                         │     O(log N) Verify     │
         │                         │ ──┐                     │
         │                         │   │ Deny-by-default     │
         │                         │ ◄─┘ Oracle Check        │
         │                         │                         │
         │                         │  5. Release CTC Escrow  │
         │                         │────────────────────────►│
         │                         │                         │
         │  6. Validated Receipt   │                         │
         │◄────────────────────────│                         │
```

---

## Internal Safety & Static-Analysis Checklist

AgentKeeper-MCP maintains an internal engineering checklist, organized loosely along the section structure of the ISO 9001 quality-management standard for convenience, but this is a self-administered script, not a third-party or accredited certification. The checklist covers:

| Checklist Area (internal script label) | Metric & Standard Enforced | Verification Status |
| :--- | :--- | :--- |
| **Area 4: Context & Infrastructure** | Multi-chain config (Arc, Base, Arb, Mantle, CTC), FastMCP stdio server | `[PASS] 100%` |
| **Area 5: Leadership & Quality** | Internal quality notes ([`QUALITY_MANUAL.md`](iso9001_compliance/QUALITY_MANUAL.md)), zero-defect policy | `[PASS] 100%` |
| **Area 6: Planning & Risk** | Internal risk register ([`RISK_REGISTER.md`](iso9001_compliance/RISK_REGISTER.md)), Merkle depth bounds ($\le 64$), EIP-55 checksum | `[PASS] 100%` |
| **Area 7: Support & Qualification** | Typed Pydantic schemas, Ruff static analysis, Python 3.12 pinned runtime | `[PASS] 100%` |
| **Area 8: Operation & V&V** | Traceability notes ([`TRACEABILITY_MATRIX.md`](iso9001_compliance/TRACEABILITY_MATRIX.md)), 137 automated tests, FastMCP integration | `[PASS] 100%` |
| **Area 9: Performance Evaluation** | Dynamic oracle anchoring verification, Arc Mainnet live query, GitHub Actions CI | `[PASS] 100%` |
| **Area 10: Continual Improvement** | Hypothesis property fuzz engine (5,000 iterations), automated checklist script | `[PASS] 100%` |

Run the internal checklist script locally (its own console output still prints "ISO/DIS 9001:2026" and "Clause" labels internally; that is the script's own legacy naming, not a claim of certification):
```bash
make audit-iso9001
```

---

## Quick Setup

### 1. Add to Claude Desktop or Antigravity Config
Add this entry to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "agent-keeper": {
      "command": "python3",
      "args": ["-m", "agent_keeper.server"]
    }
  }
}
```

### 2. Local Installation & Verification

```bash
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp

# Setup environment
uv venv --python python3.12
source .venv/bin/activate
pip install -e . pytest hypothesis "web3[tester]" py-solc-x

# Run test suite (contract tests compile with solc from PATH, or download 0.8.20 via py-solc-x)
pytest
```

---

## Test Coverage & Reliability

`make test` (or `pytest`) runs 137 tests at this commit, all passing. That includes the x402 fail-closed tests and the `X402Receipt.sol` contract tests, which compile the contract and run it on an in-memory EVM. The contract tests need `web3[tester]` and `py-solc-x` (dev dependencies; `contracts` extra in `pyproject.toml`).

* **Deterministic Invariants:** Bounded retry loops, minimum 2 runtime assertions per function, zero dynamic heap allocations on execution path.
* **Security Constraints:** Enforces parameter bounds and rejects transactions exceeding pre-set gas ceilings.

---

## Upstream Production Integration

AgentKeeper-MCP is designed as the canonical agent execution layer for **KeeperHub** (the open-source workflow automation platform for autonomous agents):

* **KeeperHub PR #2547:** [`feat(plugins): #2310 add Agent Gateway plugin`](https://github.com/KeeperHub/keeperhub/pull/2547)
  * Implements `AgentGatewayPlugin` (`src/plugins/agent-gateway.ts`) providing native KeeperHub action nodes for EVM transaction execution, HTTP 402 micro-payment settlement, and Creditcoin Attestcoin solver claims.
  * KeeperHub core maintainer (`suisuss`) confirmed the issue reference and PR linkage are correct, and that an unrelated CI check failure on their side is not attributable to this contribution:
    > *"check-issue-link is red on our side. #2310 is filed correctly and your reference is right... not a defect in your work, and there is nothing to refile or chase. I will come back here once the issue has a verdict."*
    This is a maintainer acknowledgment that the submission is filed correctly and awaiting a merge verdict, not a statement that the plugin itself has been reviewed or approved.
  * Byte-identical plugin discovery (`pnpm discover-plugins`) and clean TypeScript compilation (`tsc --noEmit`).
* **DoraHacks BUIDL Profile #48196:** [https://dorahacks.io/buidl/48196](https://dorahacks.io/buidl/48196)

---

## License

MIT License. Free for developers and autonomous agent operators.
