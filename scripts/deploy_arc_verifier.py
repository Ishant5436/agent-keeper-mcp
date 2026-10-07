#!/usr/bin/env python3
"""Build (and optionally broadcast) the deployment of contracts/X402Receipt.sol on Arc Mainnet.

DEFAULT = DRY RUN. It compiles the contract, prints the unsigned deployment
transaction, a gas estimate and a cost estimate in USDC. It never reads or
touches any private key and sends nothing. Its only network traffic is optional
read-only JSON-RPC (eth_chainId / eth_estimateGas / eth_gasPrice /
eth_getTransactionCount); if the RPC is unreachable it falls back to an offline
gas estimate.

    python3 scripts/deploy_arc_verifier.py                       # dry run
    python3 scripts/deploy_arc_verifier.py --from 0xYourAddress  # dry run, exact nonce/gas
    export AGENT_PRIVATE_KEY=0x...   # your own shell only
    python3 scripts/deploy_arc_verifier.py --broadcast           # signs and sends ONE tx

--broadcast reads AGENT_PRIVATE_KEY from the process environment only (never a
file, never printed, never logged). The deployer needs a little native USDC
(Arc's gas token) for gas. Environment: ARC_RPC_URL (default is UNVERIFIED, see
src/agent_keeper/arc_chain.py).
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
from agent_keeper.verifier_build import EVM_VERSION, SOLC_VERSION, compile_contract, solc_version

ZERO_ADDRESS = "0x" + "00" * 20
NATIVE_DECIMALS = 18


def offline_gas_estimate(initcode: bytes) -> int:
    """Rough upper-bound-ish gas for CREATE: intrinsic + create + calldata + init-code + deposit."""
    assert isinstance(initcode, bytes) and len(initcode) > 0, "Initcode must be non-empty bytes"
    calldata = sum(4 if b == 0 else 16 for b in initcode)
    initcode_words = 2 * ((len(initcode) + 31) // 32)
    deposit = 200 * int(len(initcode) * 0.9)
    res = int((21_000 + 32_000 + calldata + initcode_words + deposit) * 1.1)
    assert res > 0, "Gas estimate must be positive"
    return res


def usdc_cost(gas: int, gas_price_wei: int) -> float:
    assert gas > 0, "Gas must be positive"
    assert gas_price_wei >= 0, "Gas price must be non-negative"
    return gas * gas_price_wei / 10**NATIVE_DECIMALS


def predicted_address(sender: str, nonce: int) -> str:
    assert isinstance(sender, str) and sender.startswith("0x"), "Sender must be hex address"
    assert nonce >= 0, "Nonce must be non-negative"
    return to_checksum_address(keccak(rlp.encode([bytes.fromhex(sender[2:]), nonce]))[12:])


def try_rpc(method: str, params: list):
    """Read-only RPC call; returns None when the endpoint is unreachable/unsupported."""
    assert isinstance(method, str) and len(method) > 0, "Method must be non-empty string"
    assert isinstance(params, list), "Params must be list"
    try:
        return rpc_call(method, params)
    except RuntimeError as exc:
        print(f"  [rpc unavailable] {method}: {str(exc)[:120]}")
        return None


def gather_chain_info(sender: str | None, initcode_hex: str, gas_price_gwei: float | None, chain_id: int | None = None):
    """Return (gas, gas_price_wei|None, nonce|None, source) using read-only RPC where possible."""
    cid = chain_id or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "Chain ID must be positive"
    assert isinstance(initcode_hex, str) and initcode_hex.startswith("0x"), "Initcode must be hex"
    chain_hex = try_rpc("eth_chainId", [])
    if chain_hex is not None and int(chain_hex, 16) != cid:
        raise SystemExit(f"[ABORTED] RPC reports chain {int(chain_hex, 16)}, expected {cid}.")
    gas = try_rpc("eth_estimateGas", [{"from": sender or ZERO_ADDRESS, "data": initcode_hex}])
    price = try_rpc("eth_gasPrice", [])
    nonce = try_rpc("eth_getTransactionCount", [sender, "pending"]) if sender else None
    source = "rpc" if gas is not None else "offline"
    gas_i = int(gas, 16) if gas is not None else offline_gas_estimate(bytes.fromhex(initcode_hex[2:]))
    price_i = int(price, 16) if price is not None else None
    if price_i is None and gas_price_gwei is not None:
        price_i = int(gas_price_gwei * 10**9)
    return gas_i, price_i, int(nonce, 16) if nonce is not None else None, source


def dry_run(args, chain_id: int | None = None) -> int:
    cid = chain_id or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive"
    _abi, initcode = compile_contract()
    data_bytes = bytes.fromhex(initcode[2:])
    assert len(data_bytes) > 0, "Initcode bytes must not be empty"
    print(f"== DRY RUN (no key read, nothing sent) ==\nChain ID: {cid}\nRPC: {rpc_url()}")
    print(f"{solc_version()} (pragma ^0.8.20, wanted {SOLC_VERSION}) / evm {EVM_VERSION}; initcode {len(data_bytes)} bytes, "
          f"keccak {'0x' + keccak(data_bytes).hex()}")
    gas, price, nonce, source = gather_chain_info(args.sender, initcode, args.gas_price_gwei, cid)
    data_shown = initcode if args.print_data else f"{initcode[:18]}...({len(data_bytes)} bytes; use --print-data)"
    tx = {
        "chainId": cid,
        "from": args.sender or "<deployer, known only at --broadcast>",
        "to": None,
        "value": 0,
        "nonce": nonce if nonce is not None else "<fetched at --broadcast>",
        "gas": gas,
        "gasPrice": price if price is not None else "<fetched at --broadcast>",
        "data": data_shown,
    }
    print("Unsigned deployment tx:\n" + json.dumps(tx, indent=2))
    print(f"Gas estimate: {gas} ({'RPC eth_estimateGas' if source == 'rpc' else 'OFFLINE rough estimate'})")
    if price is None:
        print("Cost estimate: unavailable (no gas price; pass --gas-price-gwei or reach the RPC)")
    else:
        print(f"Cost estimate: ~{usdc_cost(gas, price):.6f} USDC "
              f"(gas {gas} x {price} wei; assumes 18-decimal native USDC)")
    if nonce is not None and args.sender:
        print(f"Predicted contract address: {predicted_address(args.sender, nonce)}")
    print("To deploy: export AGENT_PRIVATE_KEY in your own shell, then re-run with --broadcast.")
    return 0


def save_deployment_receipt(cid: int, addr: str, deployer: str, tx_hash: str, receipt: dict) -> Path:
    assert isinstance(cid, int) and cid > 0, "cid must be positive"
    assert isinstance(addr, str) and addr.startswith("0x"), "addr must be hex"
    receipt_data = {
        "network": "Arc Testnet" if cid == ARC_TESTNET_CHAIN_ID else "Arc Mainnet",
        "chain_id": cid,
        "contract_name": "X402Receipt",
        "contract_address": addr,
        "deployer_address": deployer,
        "transaction_hash": tx_hash,
        "block_number": int(receipt.get("blockNumber", "0x0"), 16),
        "gas_used": int(receipt.get("gasUsed", "0x0"), 16),
        "status": receipt.get("status"),
        "explorer_url": f"{explorer_url()}/tx/{tx_hash}",
    }
    filename = "arc_testnet_receipt.json" if cid == ARC_TESTNET_CHAIN_ID else "arc_mainnet_receipt.json"
    receipt_file = Path(__file__).resolve().parents[1] / filename
    with open(receipt_file, "w") as f:
        json.dump(receipt_data, f, indent=2)
    return receipt_file


def broadcast(chain_id: int | None = None) -> int:
    from eth_account import Account  # imported late: the dry-run path never touches keys

    cid = chain_id or get_arc_chain_id()
    assert isinstance(cid, int) and cid > 0, "chain_id must be positive"
    key = os.environ.get("AGENT_PRIVATE_KEY", "")
    if not key:
        print("[ABORTED] --broadcast requires AGENT_PRIVATE_KEY in the environment.")
        return 1
    account = Account.from_key(key)
    _abi, initcode = compile_contract()
    assert len(initcode) > 2, "Compiled contract initcode must be valid hex"
    gas, price, nonce, source = gather_chain_info(account.address, initcode, None, cid)
    if source != "rpc" or price is None or nonce is None:
        print("[ABORTED] Need a reachable RPC for nonce, gas and gas price before broadcasting.")
        return 1
    gas = int(gas * 1.2)
    balance = int(rpc_call("eth_getBalance", [account.address, "latest"]), 16)
    cost = gas * price
    print(f"Deployer {account.address} nonce {nonce}; max cost ~{usdc_cost(gas, price):.6f} USDC")
    if balance < cost:
        print(f"[ABORTED] Balance {balance} wei is below the max gas cost {cost} wei.")
        return 1
    print(f"Predicted contract address: {predicted_address(account.address, nonce)}")
    tx = {"chainId": cid, "nonce": nonce, "value": 0, "gas": gas, "gasPrice": price, "data": initcode}
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = rpc_call("eth_sendRawTransaction", ["0x" + bytes(raw).hex()])
    print(f"Submitted deployment. tx_hash = {tx_hash}\nExplorer: {explorer_url()}/tx/{tx_hash}")
    receipt = wait_for_receipt(tx_hash)
    if receipt is None:
        print("[PENDING] Not confirmed within the wait window; check the explorer.")
        return 0
    if receipt.get("status") != "0x1":
        print("[REVERTED] Deployment reverted; do not cite it.")
        return 1
    addr = to_checksum_address(receipt["contractAddress"])
    env_var = "ARC_TESTNET_X402_VERIFIER" if cid == ARC_TESTNET_CHAIN_ID else "ARC_X402_VERIFIER"
    r_path = save_deployment_receipt(cid, addr, account.address, tx_hash, receipt)
    print(f"[CONFIRMED] X402Receipt deployed at {addr}\nReceipt saved to: {r_path.name}\nNext: export {env_var}={addr}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--broadcast", action="store_true", help="sign with AGENT_PRIVATE_KEY (env) and send")
    parser.add_argument("--testnet", action="store_true", help="target Arc Testnet (Chain ID 5042002)")
    parser.add_argument("--from", dest="sender", help="public deployer address for exact dry-run nonce/gas")
    parser.add_argument("--gas-price-gwei", type=float, help="dry-run fallback if the RPC is unreachable")
    parser.add_argument("--print-data", action="store_true", help="print full init code in the dry run")
    args = parser.parse_args()
    if args.sender:
        args.sender = to_checksum_address(args.sender)
    if args.testnet:
        os.environ["ARC_CHAIN_ID"] = "5042002"
    chain_id = get_arc_chain_id()
    assert chain_id in (ARC_CHAIN_ID, ARC_TESTNET_CHAIN_ID), f"Invalid chain ID: {chain_id}"
    assert isinstance(args.broadcast, bool), "args.broadcast must be boolean"
    return broadcast(chain_id) if args.broadcast else dry_run(args, chain_id)


if __name__ == "__main__":
    sys.exit(main())
