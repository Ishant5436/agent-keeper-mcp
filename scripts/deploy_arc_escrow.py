#!/usr/bin/env python3
"""Build and deploy contracts/ArcAgentEscrow.sol on Circle Arc (Mainnet or Testnet).

DEFAULT = DRY RUN. It compiles the contract, prints the unsigned deployment transaction,
gas estimate, and estimated cost in native USDC.

Usage:
    python3 scripts/deploy_arc_escrow.py --testnet                  # Dry run testnet
    export AGENT_PRIVATE_KEY=0x...
    python3 scripts/deploy_arc_escrow.py --testnet --broadcast     # Deploy to Arc Testnet
    python3 scripts/deploy_arc_escrow.py --broadcast               # Deploy to Arc Mainnet
"""

import argparse
import json
import os
import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import rlp
from eth_utils import keccak, to_checksum_address

from agent_keeper.arc_chain import (
    ARC_CHAIN_ID,
    ARC_TESTNET_CHAIN_ID,
    explorer_url,
    get_arc_chain_id,
    rpc_call,
    rpc_url,
    wait_for_receipt,
)
from agent_keeper.verifier_build import compile_contract, solc_version

ZERO_ADDRESS = "0x" + "00" * 20
NATIVE_DECIMALS = 18


def offline_gas_estimate(initcode: bytes) -> int:
    assert isinstance(initcode, bytes) and len(initcode) > 0, "Initcode must be non-empty"
    calldata = sum(4 if b == 0 else 16 for b in initcode)
    initcode_words = 2 * ((len(initcode) + 31) // 32)
    deposit = 200 * int(len(initcode) * 0.9)
    res = int((21_000 + 32_000 + calldata + initcode_words + deposit) * 1.1)
    assert res > 0, "Gas estimate must be positive"
    return res


def compute_contract_address(sender: str, nonce: int) -> str:
    assert isinstance(sender, str) and sender.startswith("0x"), "Sender must be hex address"
    assert isinstance(nonce, int) and nonce >= 0, "Nonce must be non-negative"
    sender_bytes = bytes.fromhex(sender[2:] if sender.startswith("0x") else sender)
    encoded = rlp.encode([sender_bytes, nonce])
    return to_checksum_address("0x" + keccak(encoded)[12:].hex())


def dry_run(args, chain_id: int) -> int:
    abi, bytecode = compile_contract("ArcAgentEscrow")
    initcode = bytes.fromhex(bytecode[2:] if bytecode.startswith("0x") else bytecode)
    gas = offline_gas_estimate(initcode)
    print("== DRY RUN: ArcAgentEscrow Deployment ==")
    print(f"Chain ID: {chain_id} | RPC: {rpc_url()}")
    print(f"Bytecode length: {len(initcode)} bytes | Offline gas estimate: {gas}")
    print(f"Estimated fee at 20 Gwei: ~{(gas * 20 * 10**9) / 10**NATIVE_DECIMALS:.6f} USDC")
    print("ABI entries:", len(abi))
    print("To broadcast, export AGENT_PRIVATE_KEY and run with --broadcast.")
    return 0


def broadcast(args, chain_id: int) -> int:
    key_hex = os.getenv("AGENT_PRIVATE_KEY", "").strip()
    if not key_hex:
        print("[ABORTED] AGENT_PRIVATE_KEY environment variable is not set.", file=sys.stderr)
        return 1

    from eth_account import Account

    account = Account.from_key(key_hex)
    sender = account.address
    abi, bytecode = compile_contract("ArcAgentEscrow")
    initcode = bytes.fromhex(bytecode[2:] if bytecode.startswith("0x") else bytecode)

    nonce = int(rpc_call("eth_getTransactionCount", [sender, "pending"]), 16)
    gas_price = int(rpc_call("eth_gasPrice", []), 16)
    call_obj = {"from": sender, "data": "0x" + initcode.hex()}
    try:
        gas = int(rpc_call("eth_estimateGas", [call_obj]), 16)
    except Exception:
        gas = offline_gas_estimate(initcode)

    tx = {
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": int(gas * 1.2),
        "to": "",
        "value": 0,
        "data": "0x" + initcode.hex(),
        "chainId": chain_id,
    }
    signed = Account.sign_transaction(tx, key_hex)
    tx_hash = rpc_call("eth_sendRawTransaction", [signed.raw_transaction.hex()])
    computed_addr = compute_contract_address(sender, nonce)

    print("== BROADCAST SUBMITTED ==")
    print(f"Tx Hash: {tx_hash}")
    print(f"Predicted Contract Address: {computed_addr}")
    print(f"Explorer URL: {explorer_url(tx_hash, chain_id)}")

    receipt = wait_for_receipt(tx_hash, chain_id=chain_id)
    print("== DEPLOYMENT CONFIRMED ==")
    print(f"Status: {receipt.get('status')}")
    print(f"Contract Address: {receipt.get('contractAddress') or computed_addr}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy ArcAgentEscrow to Arc Mainnet / Testnet")
    parser.add_argument("--testnet", action="store_true", help="Target Arc Testnet (Chain ID 5042002)")
    parser.add_argument("--broadcast", action="store_true", help="Sign and send transaction using AGENT_PRIVATE_KEY")
    args = parser.parse_args()

    chain_id = ARC_TESTNET_CHAIN_ID if args.testnet else ARC_CHAIN_ID
    if args.broadcast:
        return broadcast(args, chain_id)
    return dry_run(args, chain_id)


if __name__ == "__main__":
    sys.exit(main())
