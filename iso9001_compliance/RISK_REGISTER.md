# Software Quality Risk Register (FMEA Matrix): Agent Keeper MCP
## Conforming to ISO/DIS 9001:2026 Clause 6 (Risk-Based Thinking)

This document tracks identified operational hazards, security failure modes, and automated mitigations for `agent-keeper-mcp`.

---

## 1. Risk Evaluation Scale
- **Severity (S):** 1 (Negligible) to 5 (Catastrophic capital loss / unauthorized contract execution)
- **Likelihood (L):** 1 (Extremely Rare) to 5 (Frequent without controls)
- **Risk Priority Number (RPN):** $S \times L$ (Scale 1 to 25). RPN $\ge 12$ mandates automated gating.

---

## 2. Failure Modes and Effects Analysis (FMEA)

| Risk ID | Potential Failure Mode | Impact / Effect | Severity (S) | Likelihood (L) | Initial RPN | Automated Mitigation & Quality Control | Residual RPN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-AK-01** | Forged Merkle proof or tampered transaction hash in solver reimbursement | Fraudulent withdrawal of escrowed funds | 5 | 4 | **20** | Rigorous cryptographic Merkle leaf hash verification and dynamic on-chain block oracle anchoring (`verify_attestcoin_proof`, verified in `test_creditcoin.py`) | **2** (S=2, L=1) |
| **RSK-AK-02** | Unbounded loop during Merkle proof verification | CPU exhaustion denial-of-service (DoS) | 4 | 3 | **12** | Hard proof depth cap ($\le 64$ iterations); verified in `test_verify_attestcoin_proof_depth_exceeds_64_fails` | **2** (S=2, L=1) |
| **RSK-AK-03** | Malformed or non-checksummed Ethereum address accepted | Funds routed to blackhole or unrecoverable address | 4 | 4 | **16** | Strict EIP-55 checksum validation via Pydantic validator (`validate_address_checksum`); verified in `test_strict_eip55_checksum_enforcement` | **2** (S=2, L=1) |
| **RSK-AK-04** | Cumulative micropayment runaway spend by rogue AI agent | Complete agent treasury depletion | 5 | 3 | **15** | Cumulative spending cap state machine tracking total debits against hard allowance ceiling; verified in `test_cumulative_safety_budget_exhaustion` | **2** (S=2, L=1) |
| **RSK-AK-05** | Double-spend or replay of transaction relay intent | Duplicate on-chain transactions and double capital debit | 5 | 3 | **15** | In-memory transaction hash idempotency cache with bounded FIFO eviction; verified in `test_idempotent_tx_execution` | **2** (S=2, L=1) |
| **RSK-AK-06** | Calldata buffer overflow or memory ballooning | Memory exhaustion / server crash | 4 | 3 | **12** | Strict 128KB calldata size bound in schemas; verified in `test_calldata_overflow_rejection` | **2** (S=2, L=1) |
| **RSK-AK-07** | Circle Arc Mainnet (Chain ID 5042) 6-decimal USDC miscalculation | 10^12x over-accounting or under-funding | 5 | 3 | **15** | Native USDC 6-decimal divisor handling in `keeper_agent_balance`; verified in `test_x402_settlement_on_arc_mainnet` | **2** (S=2, L=1) |

---

## 3. Review Frequency
Audited on every commit via `make audit-iso9001` and continuous integration (`.github/workflows/ci.yml`).
