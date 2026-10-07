#!/usr/bin/env python3
"""Broadcast ONE real X402Receipt.settle(...) call on Circle Arc Mainnet.

This is the on-chain evidence step for Arc Microgrants: a signed x402 permit
redeemed against the deployed contracts/X402Receipt.sol verifier. It requires
(1) the verifier already deployed (scripts/deploy_arc_verifier.py --broadcast),
(2) ARC_X402_VERIFIER set to its checksum address, and (3) a wallet holding a
little native USDC for gas.

DEFAULT = DRY RUN: prints the permit and the settle() call it would send. It
never reads a private key and sends nothing.

    export ARC_X402_VERIFIER=0x...                   # deployed address
    python3 scripts/broadcast_live_arc_tx.py         # dry run
    export AGENT_PRIVATE_KEY=0x...                   # your own shell only
    python3 scripts/broadcast_live_arc_tx.py --broadcast

--broadcast reads AGENT_PRIVATE_KEY from the environment only (never a file,
never printed). The same account signs the permit (as payer) and pays gas.
settle() only records a receipt and emits an event; it moves no USDC.
"""

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from eth_utils import to_checksum_address

from agent_keeper.arc_chain import (
    ARC_CHAIN_ID,
    ARC_TESTNET_CHAIN_ID,
    encode_settle_calldata,
    explorer_url,
    get_arc_chain_id,
    rpc_call,
    rpc_url,
    wait_for_receipt,
)
from agent_keeper.x402 import VerifierNotConfiguredError, build_permit_typed_data, resolve_verifier

PERMIT_TTL_SECONDS = 600


def build_permit(verifier: str, payer: str, payee: str, amount: int, chain_id: int | None = None) -> dict:
    cid = chain_id or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive integer"
    assert isinstance(amount, int) and amount > 0, "amount must be positive integer"
    return build_permit_typed_data(
        cid, verifier, payer, payee, amount, secrets.randbits(256), int(time.time()) + PERMIT_TTL_SECONDS
    )


def dry_run(verifier: str, args, chain_id: int | None = None) -> int:
    cid = chain_id or getattr(args, "chain_id", None) or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive"
    assert isinstance(verifier, str) and verifier.startswith("0x"), "verifier must be hex address"
    payer = args.payer or "<AGENT address, derived from AGENT_PRIVATE_KEY at --broadcast>"
    payee = args.payee or payer
    permit = build_permit(verifier, payer, payee, args.amount, cid)
    print("== DRY RUN (no key read, nothing signed or sent) ==")
    print(f"Chain ID: {cid}   RPC: {rpc_url()}   verifier: {verifier}")
    print("EIP-712 permit that would be signed by the payer:\n" + json.dumps(permit["message"], indent=2))
    print(f"Domain: {json.dumps(permit['domain'])}")
    print("Call: settle(payer, payee, amount, nonce, deadline, signature) on the verifier, value 0.")
    print("To send: export AGENT_PRIVATE_KEY in your own shell, then re-run with --broadcast.")
    return 0


def preflight(verifier: str, sender: str, calldata: bytes, chain_id: int | None = None) -> tuple[int, int, int]:
    """Read-only checks; returns (nonce, gas, gas_price) or raises SystemExit."""
    cid = chain_id or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive"
    assert isinstance(calldata, bytes) and len(calldata) > 0, "calldata must be non-empty bytes"
    if int(rpc_call("eth_chainId", []), 16) != cid:
        raise SystemExit(f"[ABORTED] RPC is not chain {cid}.")
    if rpc_call("eth_getCode", [verifier, "latest"]) in (None, "0x"):
        raise SystemExit(f"[ABORTED] No contract code at {verifier}; deploy X402Receipt first.")
    call = {"from": sender, "to": verifier, "data": "0x" + calldata.hex()}
    try:
        rpc_call("eth_call", [call, "latest"])  # read-only simulation; reverts raise
        gas = int(rpc_call("eth_estimateGas", [call]), 16)
    except RuntimeError as exc:
        raise SystemExit(f"[ABORTED] settle() simulation failed: {exc}") from exc
    nonce = int(rpc_call("eth_getTransactionCount", [sender, "pending"]), 16)
    gas_price = int(rpc_call("eth_gasPrice", []), 16)
    return nonce, int(gas * 1.2), gas_price


def broadcast(verifier: str, args, chain_id: int | None = None) -> int:
    from eth_account import Account  # imported late: the dry-run path never touches keys
    from eth_account.messages import encode_typed_data

    cid = chain_id or getattr(args, "chain_id", None) or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive"
    assert isinstance(verifier, str) and verifier.startswith("0x"), "verifier must be hex"
    key = os.environ.get("AGENT_PRIVATE_KEY", "")
    if not key:
        print("[ABORTED] --broadcast requires AGENT_PRIVATE_KEY in the environment.")
        return 1
    account = Account.from_key(key)
    payee = args.payee or account.address
    permit = build_permit(verifier, account.address, payee, args.amount, cid)
    signed_permit = Account.sign_message(encode_typed_data(full_message=permit), private_key=key)
    m = permit["message"]
    calldata = encode_settle_calldata(
        m["payer"], m["payee"], m["amount"], m["nonce"], m["deadline"], bytes(signed_permit.signature)
    )
    nonce, gas, gas_price = preflight(verifier, account.address, calldata, cid)
    tx = {"chainId": cid, "nonce": nonce, "to": verifier, "value": 0, "gas": gas,
          "gasPrice": gas_price, "data": calldata}
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = rpc_call("eth_sendRawTransaction", ["0x" + bytes(raw).hex()])
    print(f"Submitted settle(). tx_hash = {tx_hash}\nExplorer: {explorer_url()}/tx/{tx_hash}")
    receipt = wait_for_receipt(tx_hash)
    if receipt is None:
        print("[PENDING] Not confirmed within the wait window; check the explorer link above.")
        return 0
    if receipt.get("status") != "0x1":
        print("[REVERTED] Transaction reverted; do not cite it as evidence.")
        return 1
    print(json.dumps({k: receipt.get(k) for k in ("transactionHash", "blockNumber", "gasUsed", "status")}, indent=2))
    record_settle_receipt(cid, tx_hash, receipt)
    print(f"[CONFIRMED] Paste tx_hash {tx_hash} and the verifier address {verifier} into ARC_MICROGRANTS_SUBMISSION.md.")
    return 0


def record_settle_receipt(cid: int, tx_hash: str, receipt: dict) -> None:
    assert isinstance(cid, int) and cid > 0, "cid must be positive"
    assert isinstance(tx_hash, str) and tx_hash.startswith("0x"), "tx_hash must be hex"
    filename = "arc_testnet_receipt.json" if cid == ARC_TESTNET_CHAIN_ID else "arc_mainnet_receipt.json"
    receipt_file = Path(__file__).resolve().parents[1] / filename
    if receipt_file.exists():
        try:
            with open(receipt_file, "r") as f:
                data = json.load(f)
            data["settle_transaction_hash"] = tx_hash
            data["settle_explorer_url"] = f"{explorer_url()}/tx/{tx_hash}"
            data["settle_block_number"] = int(receipt.get("blockNumber", "0x0"), 16)
            with open(receipt_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Recorded settle transaction in {filename}")
        except Exception as exc:
            print(f"Warning: could not update {filename}: {exc}")


def resolve_or_load_verifier(chain_id: int) -> str:
    assert isinstance(chain_id, int) and chain_id > 0, "chain_id must be positive"
    try:
        return resolve_verifier(chain_id)
    except VerifierNotConfiguredError as exc:
        filename = "arc_testnet_receipt.json" if chain_id == ARC_TESTNET_CHAIN_ID else "arc_mainnet_receipt.json"
        receipt_file = Path(__file__).resolve().parents[1] / filename
        if receipt_file.exists():
            with open(receipt_file, "r") as f:
                data = json.load(f)
            addr = to_checksum_address(data["contract_address"])
            print(f"[AUTO-RESOLVED] Loaded verifier {addr} from {filename}")
            return addr
        raise exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--broadcast", action="store_true", help="sign with AGENT_PRIVATE_KEY (env) and send")
    parser.add_argument("--testnet", action="store_true", help="target Arc Testnet (Chain ID 5042002)")
    parser.add_argument("--payer", help="dry-run display only; --broadcast derives it from the key")
    parser.add_argument("--payee", help="receipt payee (default: the payer itself)")
    parser.add_argument("--amount", type=int, default=1000,
                        help="receipt amount in USDC base units, 6 decimals (default 1000 = 0.001); no funds move")
    args = parser.parse_args()
    if args.testnet:
        os.environ["ARC_CHAIN_ID"] = "5042002"
    for name in ("payer", "payee"):
        if getattr(args, name):
            setattr(args, name, to_checksum_address(getattr(args, name)))
    chain_id = get_arc_chain_id()
    assert chain_id in (ARC_CHAIN_ID, ARC_TESTNET_CHAIN_ID), f"Invalid chain ID: {chain_id}"
    assert isinstance(args.amount, int), "Amount must be integer"
    try:
        verifier = resolve_or_load_verifier(chain_id)
    except VerifierNotConfiguredError as exc:
        print(f"[ABORTED] {exc}")
        return 1
    return broadcast(verifier, args, chain_id) if args.broadcast else dry_run(verifier, args, chain_id)


if __name__ == "__main__":
    sys.exit(main())
