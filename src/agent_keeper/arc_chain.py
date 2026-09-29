"""Minimal raw JSON-RPC helpers for Circle Arc Mainnet (used by the deploy/broadcast scripts)."""

import os
import time

import httpx
from eth_abi import encode
from eth_utils import keccak

ARC_CHAIN_ID = 5042

# UNVERIFIED: this default RPC URL is carried over from src/agent_keeper/config.py and has
# not been confirmed against Circle's official Arc documentation. (A read-only eth_chainId
# call to it returned 5042 on 2026-09-30, which is not an endorsement.) Set ARC_RPC_URL explicitly.
DEFAULT_ARC_RPC_URL = "https://rpc.mainnet.arc.io"
# UNVERIFIED: explorer base URL, used only to print a convenience link.
DEFAULT_ARC_EXPLORER_URL = "https://explorer.arc.network"

SETTLE_SIGNATURE = "settle(address,address,uint256,uint256,uint256,bytes)"


def rpc_url() -> str:
    return os.environ.get("ARC_RPC_URL", DEFAULT_ARC_RPC_URL)


def explorer_url() -> str:
    return os.environ.get("ARC_EXPLORER_URL", DEFAULT_ARC_EXPLORER_URL).rstrip("/")


def rpc_call(method: str, params: list, url: str | None = None, timeout: float = 15.0):
    """Raw JSON-RPC call; raises RuntimeError on transport or RPC errors."""
    assert method, "method must be non-empty"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url or rpc_url(),
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError(f"RPC transport error calling {method}: {exc}") from exc
    if data.get("error"):
        raise RuntimeError(f"RPC error from {method}: {data['error']}")
    return data.get("result")


def wait_for_receipt(tx_hash: str, max_wait_seconds: int = 90) -> dict | None:
    """Poll for a receipt, bounded by max_wait_seconds."""
    assert max_wait_seconds > 0, "max_wait_seconds must be positive"
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        receipt = rpc_call("eth_getTransactionReceipt", [tx_hash])
        if receipt is not None:
            return receipt
        time.sleep(3)
    return None


def encode_settle_calldata(
    payer: str, payee: str, amount: int, nonce: int, deadline: int, signature: bytes
) -> bytes:
    """ABI-encode a call to X402Receipt.settle(...)."""
    selector = keccak(text=SETTLE_SIGNATURE)[:4]
    return selector + encode(
        ["address", "address", "uint256", "uint256", "uint256", "bytes"],
        [payer, payee, amount, nonce, deadline, signature],
    )
