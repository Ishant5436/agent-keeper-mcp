# BCH BLAZE 2026 — Project Submission Dossier

**Target Track:** Mainnet Track (1st Place: $3,500 PUSD + BLISS 2027 Tickets)  
**Project Name:** AgentKeeper BCH — Deterministic CashTokens & Covenant Settlement Guard for Autonomous AI Agents  
**Live Demo:** [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/)  
**Source Code:** [https://github.com/Ishant5436/agent-keeper-mcp](https://github.com/Ishant5436/agent-keeper-mcp)  
**CashTokens Donation Address:** `bitcoincash:qq4vqn04qj5j7q8w3h99yvh2v6z6z5r5v5s5z9h6r7`  

---

## 1. Executive Summary

Autonomous AI agents operating across decentralized networks face a fundamental financial safety vulnerability: **unbounded wallet draining**. When an autonomous LLM or quant engine is granted raw private key access or unconstrained UTXO spending authority, prompt injections, execution drift, or network anomalies can result in catastrophic treasury loss.

**AgentKeeper BCH** is a deterministic, non-custodial transaction settlement and covenant guard protocol engineered natively for **Bitcoin Cash (BCH) Mainnet** and **Chipnet**. By leveraging native Bitcoin Cash covenants and the **CHIP-2022-02-CashTokens** standard, AgentKeeper enforces hardware-grade spending bounds at the UTXO consensus layer:
1. **Fungible Token (FT) Micro-Budgets:** AI agents receive pre-authorized CashToken quotas for external API calls and compute consumption.
2. **Stateful NFT Session Commitments:** Agents attest task completions by appending cryptographic commitments (up to 40 bytes) to immutable or mutable NFT outputs.
3. **Deterministic Safety Invariants:** Engineered under Gerard J. Holzmann's Power of 10 rules ($\le 60$ lines per routine, assertion density $\ge 2$).

---

## 2. Technical Architecture & Mainnet CashTokens Implementation

### 2.1 CashTokens (CHIP-2022-02) Script Prefix Engine
Bitcoin Cash implements native layer-1 tokens via the `0xef` (`PREFIX_TOKEN`) opcode directly inside UTXO locking bytecodes without EVM gas overhead. AgentKeeper implements deterministic encoding and decoding of CashTokens prefixes:

$$\text{Prefix} = \mathtt{0xEF} \parallel \text{CategoryID}_{32} \parallel \text{Bitfield} \parallel [\text{CommitmentLen} \parallel \text{Commitment}] \parallel [\text{Amount}_{\text{uint64}}]$$

* **Category ID:** 32-byte hex identifier binding the token to its immutable genesis UTXO.
* **Capabilities:** Full support for `NONE` (immutable utility tokens), `MUTABLE` (updatable session states), and `MINTING` (sub-credential issuance).
* **Commitment Payload:** Bounded to 40 bytes to carry deterministic agent task hashes or EIP-712 / x402 verification digests.

### 2.2 Autonomous Agent Spending Policy Guard
Before broadcasting any mainnet or chipnet transaction, the AgentKeeper daemon enforces strict policy evaluation:
* Rejection of any transaction exceeding pre-configured satoshi bounds (`max_satoshis_per_tx`).
* Whitelist verification of approved CashToken categories (`allowed_categories`).
* Quota enforcement on fungible token transfers (`max_ft_per_tx`).

---

## 3. FastMCP Tool Server Integration

AgentKeeper exposes a standardized FastMCP interface allowing any AI agent framework (Claude Desktop, Cursor, Gemini CLI, LangChain) to safely interact with Bitcoin Cash:

```json
{
  "name": "keeper_bch_settle",
  "description": "Settle or guard Bitcoin Cash (BCH) and CashTokens transactions for autonomous AI agents.",
  "parameters": {
    "network": "mainnet",
    "recipient_address": "bitcoincash:qq4vqn04qj5j7q8w3h99yvh2v6z6z5r5v5s5z9h6r7",
    "spend_satoshis": 15000,
    "token_category": "2222222222222222222222222222222222222222222222222222222222222222",
    "token_amount": 500,
    "nft_capability": "mutable",
    "nft_commitment_hex": "6167656e742d7461736b2d3031"
  }
}
```

---

## 4. Verification & Institutional Test Evidence

The Bitcoin Cash settlement suite was verified with 100% green pass rate:
* `tests/test_bch_chain.py`: 8 / 8 passed (address validation, prefix roundtrips, spending guard policies, covenant descriptors).
* `tests/test_server.py`: 8 / 8 passed (MCP tool verification, error isolation).
* Full multi-chain regression suite: 41 / 41 passed across BCH, Arc Mainnet, HashKey, Portaldot, and x402.

---

## 5. Live Demo & Explorer Links

* **Live Web Dashboard:** [https://ishant5436.github.io/agent-keeper-mcp/](https://ishant5436.github.io/agent-keeper-mcp/)
* **BCH Mainnet Explorer Reference:** [Blockchair Bitcoin Cash Explorer](https://blockchair.com/bitcoin-cash)
* **Chipnet Testnet Reference:** [Chaingraph Chipnet Explorer](https://chipnet.chaingraph.cash)
