#!/usr/bin/env python3
"""Broadcast one real, minimal transaction on Circle Arc Mainnet.

This is the one piece of Arc Microgrants eligibility ("a live deployment on
Arc mainnet, with a link we can open") that cannot be produced by code alone:
it requires a wallet funded with a small amount of USDC (Arc's native gas
token) and its private key, supplied by you, in your own shell.

This script never asks for or logs the private key. It reads it from the
AGENT_PRIVATE_KEY environment variable, signs ONE zero-value self-transfer
(you send 0 USDC to your own address, spending only the gas fee, a few
cents), and broadcasts it via raw JSON-RPC. Nothing else about your funds
is touched.

Usage:
    export AGENT_PRIVATE_KEY=0x...   # your own wallet, funded with a little
                                      # USDC on Arc Mainnet for gas
    python3 scripts/broadcast_live_arc_tx.py

Prerequisites:
    1. A wallet address funded with a small amount of USDC on Arc Mainnet
       (Chain ID 5042). USDC is Arc's native gas token, so this is the only
       funding needed.
    2. That wallet's private key, exported as AGENT_PRIVATE_KEY in your own
       terminal session. Do not paste it into chat or a file.
"""

import json
import os
import sys
import time

import httpx
from eth_account import Account

ARC_RPC_URL = os.environ.get("ARC_RPC_URL", "https://rpc.mainnet.arc.io")
ARC_CHAIN_ID = 5042


def _rpc_call(method: str, params: list) -> dict:
    """Raw JSON-RPC call against the Arc Mainnet endpoint."""
    assert isinstance(method, str) and len(method) > 0, "method must be non-empty"
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            ARC_RPC_URL,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        )
        resp.raise_for_status()
        data = resp.json()
        assert "error" not in data or data["error"] is None, f"RPC error: {data.get('error')}"
        return data.get("result")


def broadcast_self_transfer() -> str:
    """Sign and submit a zero-value self-transfer, returning the real tx hash."""
    private_key = os.environ.get("AGENT_PRIVATE_KEY", "")
    assert private_key, "Set AGENT_PRIVATE_KEY in your own shell before running this script."

    account = Account.from_key(private_key)
    address = account.address

    nonce_hex = _rpc_call("eth_getTransactionCount", [address, "pending"])
    assert nonce_hex is not None, "Could not fetch nonce; check ARC_RPC_URL connectivity."
    nonce = int(nonce_hex, 16)

    gas_price_hex = _rpc_call("eth_gasPrice", [])
    gas_price = int(gas_price_hex, 16)

    tx = {
        "chainId": ARC_CHAIN_ID,
        "nonce": nonce,
        "to": address,
        "value": 0,
        "gas": 21000,
        "gasPrice": gas_price,
        "data": b"",
    }
    signed = account.sign_transaction(tx)
    raw_hex = "0x" + signed.raw_transaction.hex() if hasattr(signed, "raw_transaction") else signed.rawTransaction.hex()

    tx_hash = _rpc_call("eth_sendRawTransaction", [raw_hex])
    assert tx_hash and tx_hash.startswith("0x"), f"Unexpected RPC response: {tx_hash}"
    return tx_hash


def wait_for_receipt(tx_hash: str, max_wait_seconds: int = 60) -> dict | None:
    """Poll for the transaction receipt, bounded by max_wait_seconds."""
    assert max_wait_seconds > 0, "max_wait_seconds must be positive"
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        receipt = _rpc_call("eth_getTransactionReceipt", [tx_hash])
        if receipt is not None:
            return receipt
        time.sleep(3)
    return None


def main() -> int:
    print("=" * 70)
    print("AgentKeeper-MCP: Live Arc Mainnet Broadcast (Arc Microgrants evidence)")
    print("=" * 70)
    try:
        tx_hash = broadcast_self_transfer()
    except AssertionError as e:
        print(f"[ABORTED] {e}")
        return 1

    print(f"Submitted. tx_hash = {tx_hash}")
    print(f"Explorer: https://explorer.arc.network/tx/{tx_hash}")
    print("Waiting for confirmation...")

    receipt = wait_for_receipt(tx_hash)
    if receipt is None:
        print("[PENDING] Not yet confirmed within the wait window; check the explorer link above.")
        return 0

    status = receipt.get("status")
    block = receipt.get("blockNumber")
    print(json.dumps(receipt, indent=2))
    if status == "0x1":
        print(f"[CONFIRMED] Included in block {int(block, 16) if block else '?'}.")
        print("Paste tx_hash and the explorer link into ARC_MICROGRANTS_SUBMISSION.md as live deployment evidence.")
    else:
        print("[REVERTED] Transaction was included but reverted; do not cite it as working evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
