# Software Quality Management System (QMS) Manual: Agent Keeper MCP
## Conforming to ISO/DIS 9001:2026 (Draft International Standard)

---

### 1. Scope & Application
This Quality Manual formalizes the Quality Management System (QMS) policies, procedures, and deterministic controls implemented across `agent-keeper-mcp`. It establishes quality assurance standards for autonomous AI agent transaction relaying, Creditcoin 3.0 dynamic oracle settlement, and Circle Arc Mainnet (Chain ID 5042) x402 micropayments under **ISO/DIS 9001:2026**.

---

### 2. Clause 4: Context of the Organization & Digital Infrastructure
- **4.1 Organizational Context & Multi-Chain Architecture:** Operates across EVM-compatible networks, Circle Arc Mainnet (Chain ID 5042, 6-decimal USDC native), Mantle, Creditcoin, and Ethereum testnets. Ensures strict EIP-712 typed signing, EIP-55 checksumming, and FastMCP JSON-RPC transport compatibility.
- **4.2 Stakeholder Expectations:** AI agent developers, DAOs, and hackathon evaluators require zero unhandled transaction reverts, zero key leakage, deterministic Merkle root validation, and verifiable idempotency.
- **4.3 Scope of the QMS:** Applies to all core settlement modules (`creditcoin.py`, `merkle_tree.py`, `relay.py`, `x402.py`), validation schemas (`schemas.py`), and FastMCP tool interfaces (`server.py`).
- **4.4 QMS and Automated Verification:** Quality gates are codified in [`Makefile`](file:///Users/ishantpanchal/agent-keeper-mcp/Makefile), executing 106 automated unit, blackbox, fuzz, and whitebox invariant tests.

---

### 3. Clause 5: Leadership & Quality Culture
- **5.1 Leadership & Commitment:** The engineering team adheres to a strict **Zero Completion Claims Without Verification** mandate. No feature is marked done without 100% green test and lint verification.
- **5.2 Quality Policy:** Dedicated to mathematical cryptographic safety, bounded resource consumption, dynamic on-chain oracle anchoring, and zero-loss idempotent relay execution.
- **5.3 Organizational Roles & Responsibilities:** Automated CI pipelines (`.github/workflows/ci.yml`), static schema validators (Pydantic v2), and Ruff linters act as automated quality gatekeepers.

---

### 4. Clause 6: Planning & Risk-Based Thinking
- **6.1 Actions to Address Risks & Opportunities:** The QMS maintains an active [`RISK_REGISTER.md`](file:///Users/ishantpanchal/agent-keeper-mcp/iso9001_compliance/RISK_REGISTER.md) evaluating risks including Merkle tree spoofing, unanchored oracle roots, transaction replay attacks, and cumulative micropayment budget exhaustion.
- **6.2 Quality Objectives:**
  - *Cryptographic Integrity:* 100% rejection rate for forged Merkle proofs, tampered transaction hashes, or corrupted sibling hashes.
  - *Budget Safety:* Strict non-bypassable cumulative budget caps on x402 micropayments.
  - *Idempotency:* Zero duplicate transaction submissions on retried network requests.
  - *Static Standard:* Zero Ruff lint warnings and 100% type conformance.

---

### 5. Clause 7: Support & Tool Qualification
- **7.1 Resources & Infrastructure:**
  - Python Runtime: Python 3.12/3.14 via `uv`.
  - Quality Tooling: Pytest, Hypothesis property-based fuzzer, Ruff linter.
  - Protocol Standards: EIP-712 domain separation, EIP-55 address checksumming, FastMCP.
- **7.2 Competence & Training:** Full architectural specifications and deployment procedures documented in [`README.md`](file:///Users/ishantpanchal/agent-keeper-mcp/README.md), [`ARC_MICROGRANTS_SUBMISSION.md`](file:///Users/ishantpanchal/agent-keeper-mcp/ARC_MICROGRANTS_SUBMISSION.md), and [`DORAHACKS_SUBMISSION.md`](file:///Users/ishantpanchal/agent-keeper-mcp/DORAHACKS_SUBMISSION.md).
- **7.5 Documented Information:** Test run logs, Merkle proof trees, and schema validation artifacts are systematically preserved.

---

### 6. Clause 8: Operational Planning and Control (Software V&V)
- **8.1 Verification and Validation Protocol:**
  - *Verification (Unit & Whitebox):* Mathematical verification of FlatMerkleTree leaf ordering, tree depth limits ($\le 64$), and cumulative spending accumulators.
  - *Fuzz Testing:* Property-based fuzz testing via Hypothesis (`test_fuzz_merkle.py`) verifying adversarial proof tampering is 100% rejected.
  - *Validation (Relay & RPC):* Blackbox validation of RPC error recovery, dry-run transaction execution, and dynamic oracle block anchoring.
- **8.7 Control of Non-conforming Outputs:** Any malformed address, calldata overflow, or unanchored root triggers an immediate validation exception (`ValidationError` or `AssertionError`).

---

### 7. Clause 9: Performance Evaluation
- **9.1 Monitoring & Measurement:** Continuous verification of test execution time (106 tests in <15s), memory bounded FIFOs, and Merkle tree leaf capacity.
- **9.2 Internal Audit:** Automated QMS audit executed via [`scripts/audit_iso9001_compliance.py`](file:///Users/ishantpanchal/agent-keeper-mcp/scripts/audit_iso9001_compliance.py).

---

### 8. Clause 10: Continual Improvement
- **10.1 Non-conformity and Corrective Action:** Unhandled RPC responses or edge cases are captured, documented with regression test cases, and patched.
- **10.2 Continual Improvement Cycle:** Regular expansion of supported multi-chain ecosystems (e.g. Arc Mainnet Chain ID 5042) and gas optimization.
