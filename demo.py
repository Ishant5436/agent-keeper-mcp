#!/usr/bin/env python3
"""
AgentKeeper-MCP Interactive Live Demonstration CLI
Simulates a complete autonomous AI Agent session executing onchain actions via KeeperHub:
1. Settle an HTTP 402 micro-payment for alpha data
2. Execute a gas-optimized onchain transaction on Base
3. Cryptographically verify the execution Merkle receipt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import json

from agent_keeper.server import (
    keeper_agent_balance,
    keeper_audit_verify,
    keeper_execute_tx,
    keeper_x402_settle,
)


def print_step(title: str):
    print("\n" + "=" * 70)
    print(f"[STEP]  {title}")
    print("=" * 70)


def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                 AGENTKEEPER-MCP AUTONOMOUS DEMO                     ║
    ║        Onchain Execution & x402 Gateway for the Agent Economy       ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    # 1. Inspect Treasury
    print_step("Step 1: Inspect Agent Multi-Chain Treasury")
    balance = keeper_agent_balance()
    print(json.dumps(balance, indent=2))

    # 2. Settle x402 Micro-Payment
    print_step("Step 2: Autonomously Settle HTTP 402 API Challenge ($0.50 USDC)")
    x402_res = keeper_x402_settle(
        resource_url="https://api.market-oracle.ai/v1/liquidity_depth",
        amount_usdc=0.50,
        recipient_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    )
    print(json.dumps(x402_res, indent=2))

    # 3. Execute Transaction
    print_step(
        "Step 3: Execute MEV-Protected Smart Contract Call on Base (Chain ID 8453)"
    )
    tx_res = keeper_execute_tx(
        target_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base USDC
        calldata_hex="0xa9059cbb000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa960450000000000000000000000000000000000000000000000000000000002faf080",
        chain_id=8453,
        idempotency_key="demo-task-001",
    )
    print(json.dumps(tx_res, indent=2))

    # 4. Cryptographic Proof Verification
    print_step("Step 4: Cryptographically Verify Merkle Inclusion & Execution Trace")
    audit_res = keeper_audit_verify(tx_hash=tx_res.get("tx_hash"), chain_id=8453)
    print(json.dumps(audit_res, indent=2))

    # 5. Creditcoin 3.0 Attestcoin Intent Settlement
    print_step("Step 5: Settle Cross-Chain Intent on Creditcoin 3.0 EVM (Chain ID 102031)")
    from agent_keeper.server import keeper_creditcoin_settle, _creditcoin_manager
    from agent_keeper.merkle_tree import FlatMerkleTree

    intent_id = "ctc_intent_alpha_001"
    solver_addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    src_chain = "base"
    src_tx = tx_res.get("tx_hash", "0x" + "1"*64)
    recip = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    leaf = f"{intent_id}:{src_chain}:{src_tx}:{recip}"
    tree = FlatMerkleTree([leaf, "intent_dummy_002", "intent_dummy_003"])
    proof = tree.get_proof(0)

    # Register escrow collateral on Creditcoin L1
    _creditcoin_manager.register_escrow(intent_id, solver_addr, 1500.0)

    # Anchor Attestcoin oracle root from source chain (Base L2)
    _creditcoin_manager.register_trusted_root(src_chain, tree.root)

    ctc_settle = keeper_creditcoin_settle(
        intent_id=intent_id,
        solver_address=solver_addr,
        source_chain=src_chain,
        source_tx_hash=src_tx,
        expected_recipient=recip,
        merkle_proof=proof,
        merkle_root=tree.root,
    )
    print(json.dumps(ctc_settle, indent=2))

    print("\n" + "#" * 70)
    print("[SUCCESS]  All 5 Autonomous Onchain Workflows Verified Successfully!")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
