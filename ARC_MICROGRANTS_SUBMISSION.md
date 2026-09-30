# Circle Arc Microgrants Technical Submission Dossier

## Portal Metadata (DoraHacks Arc Microgrants)
- **Program:** Arc Microgrants (Circle)
- **Portal Link:** https://dorahacks.io/hackathon/arc-microgrants/detail
- **Project Name:** AgentKeeper-MCP
- **Tagline:** Deterministic MCP Gateway for Autonomous AI Agents on Arc Mainnet with Native USDC Settlement
- **Applicant / Author:** Ishant Panchal (@Ishant5436 / ishant.p@somaiya.edu)
- **Target Network:** Arc Mainnet (Chain ID 5042)
- **Primary Repository:** https://github.com/Ishant5436/agent-keeper-mcp
- **Funding Track:** Arc Mainnet Builders (500 USDC Microgrant)

---

## Live Deployment Status (Arc Mainnet)

**Not yet deployed.** This section says exactly what is done and what is not.

Done (in this repository, verifiable by running the tests):
- `contracts/X402Receipt.sol`: a non-custodial EIP-712 receipt registry (no funds, no owner/admin/upgrade path, canonical low-s signature checks, per-payer nonce replay protection, deadline check). It records that a payer signed a permit; it does not move USDC.
- In-process tests (solc + eth-tester) for: valid signature accepted, wrong signer, expired, replayed nonce, wrong chainId, wrong verifying contract, high-s twin. These do not run against Arc.
- `keeper_x402_settle` signs permits against a verifier address read from `ARC_X402_VERIFIER`, and fails closed if it is unset or invalid. The earlier hardcoded placeholder address, which had no contract behind it, is removed and rejected.
- `scripts/deploy_arc_verifier.py`: dry run by default (unsigned deployment tx, gas estimate, USDC cost estimate; touches no key). `--broadcast` signs with `AGENT_PRIVATE_KEY` read from the environment only.
- `scripts/broadcast_live_arc_tx.py`: dry run by default; `--broadcast` sends one real `settle(...)` call to the deployed verifier.
- `keeper_agent_balance` performs read-only JSON-RPC balance queries against the configured Arc RPC (default UNVERIFIED against Circle docs, override with `ARC_RPC_URL`).

Still needs the operator's funded wallet (not done, not claimed):
1. Fund a wallet with a small amount of native USDC on Arc Mainnet (chain 5042) for gas.
2. `export AGENT_PRIVATE_KEY=0x...` in your own shell, run `python3 scripts/deploy_arc_verifier.py --broadcast`.
3. `export ARC_X402_VERIFIER=<address printed by step 2>`, run `python3 scripts/broadcast_live_arc_tx.py --broadcast`.
4. Paste the results below, check both on the explorer, then submit on DoraHacks.

- **Deployed X402Receipt address:** _PLACEHOLDER, pending deployment_
- **Deployment Transaction Hash:** _PLACEHOLDER, pending deployment_
- **Live settle() Transaction Hash:** _PLACEHOLDER, pending broadcast_
- **Explorer Links:** _PLACEHOLDER_

---

## Form Submission Narrative

I am an independent systems software developer building deterministic infrastructure in Python, Rust, and C++ for autonomous onchain execution. I am submitting AgentKeeper-MCP to the Circle Arc Microgrants program to provide an open-source, non-custodial Model Context Protocol gateway specifically tailored for AI agents operating on Circle's newly launched Arc Mainnet.

Autonomous software agents interacting with blockchains face significant security challenges when handling credentials, gas tokens, and HTTP 402 resource challenges. Injecting raw private keys or RPC endpoints directly into an automated agent context risks prompt injection attacks, memory leakage into conversation logs, and non-deterministic transaction execution. On Arc Mainnet, where USDC functions as the native gas asset, agents require a specialized execution runtime that safely handles native USDC balances, enforces strict spending ceilings, and signs cryptographic permits without human coordinator latency.

AgentKeeper-MCP resolves this by placing a hardened FastMCP middleware between autonomous AI agents and Arc Mainnet. The gateway keeps key handling inside local process memory and exposes typed JSON-RPC tools over the Model Context Protocol. For this submission, the scope is strictly Arc Mainnet (Chain ID 5042).

Why this architecture is specifically tailored for Circle Arc Mainnet:
1. Native USDC Gas Economics: On legacy EVM networks, attesting or settling micro-payments onchain costs $0.50-$5.00 in volatile gas tokens, making onchain attestation of HTTP 402 AI micro-payments economically prohibitive. On Arc Mainnet, USDC is the native gas asset. An onchain verification call (`settle()`) consumes ~60,000 gas, which at the 20 Gwei baseline costs ~0.0012 USDC. This sub-cent cost structure makes Arc the viable settlement layer for autonomous AI agents paying for per-call APIs, model inferences, or real-time data streams.
2. Separation of Custody and Attestation: The `X402Receipt` contract (`contracts/X402Receipt.sol`) is deliberately non-custodial and stateless regarding treasury assets. It holds zero funds, has no admin keys, no owner, and no upgrade proxy. Instead, it serves as an immutable, non-repudiable attestation registry: when an agent pays an off-chain resource provider, the EIP-712 permit is recorded onchain via `settle()`, permanently preventing duplicate redemption through per-payer nonces (`used[payer][nonce]`) while validating canonical low-s ECDSA signatures against `block.chainid`.
3. Fail-Closed Agent Safety: Autonomous agents must never have unrestricted access to raw keys. Through `keeper_x402_settle`, an agent evaluates an HTTP 402 challenge and signs an EIP-712 permit bound to Chain ID 5042 and the configured `ARC_X402_VERIFIER`. If no verifier is configured, the tool fails closed and refuses to sign. Through `keeper_agent_balance`, agents inspect their native USDC balance directly on Arc Mainnet. Other gateway tools and multi-chain features are documented in README.md.

The entire codebase is engineered under strict Deterministic Safety Invariants. All execution routines avoid dynamic code evaluation, loops are strictly bounded to prevent denial of service vulnerabilities, functions remain under sixty lines of code, and assertion density exceeds two invariants per routine. An in-memory idempotency cache prevents duplicate transaction execution during network congestion or RPC latency, while a monotonic spending accumulator ensures cumulative micro-payments never exceed operator-configured risk limits.

As a solo developer I aim for lean, reproducible software. The repository has a 139-test suite (unit, white-box, black-box, property fuzz, and in-process contract tests) that passes at this commit. The contract tests run against an in-memory EVM, not against Arc. Read-only balance queries use the configured Arc RPC (default UNVERIFIED against Circle docs). The Arc deployment and the live settle() transaction are pending an operator-funded wallet; see Live Deployment Status above.

---

## Architecture & Tool Specifications (Arc scope)

```
Autonomous agent (MCP client)
        |  stdio / JSON-RPC 2.0 (FastMCP)
        v
AgentKeeper-MCP
  +- keeper_x402_settle    signs EIP-712 Permit(payer, payee, amount, nonce, deadline)
  |                        for verifyingContract = $ARC_X402_VERIFIER, chainId 5042; fails closed if unset
  +- keeper_agent_balance  read-only native USDC balance on Arc (5042)
        |
        v
Circle Arc Mainnet (5042)
  +- X402Receipt.sol   settle(...) verifies the signature, burns the (payer, nonce), emits Settled
                       (no funds held, no owner/admin/upgrade path)   [deployment: PENDING]
```

---

## Deterministic Safety Invariants Audit

| Invariant | Standard Enforced | Implementation Evidence |
| :--- | :--- | :--- |
| **Rule 1: Simple Control Flow** | Zero recursion, flat iterations | Flat array iteration; iterative Merkle proof build without stack recursion. |
| **Rule 2: Bounded Loops** | Fixed upper bounds on all loops | Retry loops bounded at `max_retries=10`; Merkle proof depth capped at `<= 64`. |
| **Rule 3: Deterministic Memory** | Bounded containers & caches | FIFO eviction limits on caches (`cap = 1024`); fixed array limits. |
| **Rule 4: Function Length** | <= 60 lines per routine | All functions verified under 60 lines of code. |
| **Rule 5: Assertion Density** | >= 2 assertions per function | Pre-condition and post-condition invariants validated in every routine. |
| **Rule 6: Smallest Scope** | Encapsulated Manager State | State mutation strictly confined to typed manager class instances. |
| **Rule 7: Check Parameters** | Strict input validation | EIP-55 checksum, 128KB calldata limits, USDC spending ceiling. |
| **Rule 8: Zero Metaprogramming** | Zero dynamic code evaluation | Strict Pydantic schemas; zero `eval()` or `exec()`. |
| **Rule 9: Restrict Indirection** | Single-level reference traversal | Flat array indexing `((i-1) >> 1)` rather than deep pointer-node trees. |
| **Rule 10: Static Analysis** | 100% test pass rate, 0 warnings | 139/139 tests passing & 0 ruff lint warnings at this commit. |

---

## Judge Reproduction Guide

```bash
# 1. Clone repository
git clone https://github.com/Ishant5436/agent-keeper-mcp.git
cd agent-keeper-mcp

# 2. Run the test suite (139 tests at this commit; includes the X402Receipt contract tests,
#    which compile the contract with solc 0.8.20 and run it on an in-memory EVM)
make test

# 3. Dry-run the deployment (compiles, prints unsigned tx + gas + USDC cost estimate; no key is read)
python3 scripts/deploy_arc_verifier.py

# 4. Operator only, needs a funded wallet. Once deployed, record the results under
#    "Live Deployment Status" above.
export AGENT_PRIVATE_KEY=0x...            # your own shell only
python3 scripts/deploy_arc_verifier.py --broadcast
export ARC_X402_VERIFIER=<deployed address>
python3 scripts/broadcast_live_arc_tx.py --broadcast

# 5. Static lint
make lint
```
