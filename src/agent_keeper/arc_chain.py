"""Minimal raw JSON-RPC helpers for Circle Arc Mainnet (used by the deploy/broadcast scripts)."""

import os
import time

import httpx
from eth_abi import encode
from eth_utils import keccak

ARC_CHAIN_ID = 5042
ARC_TESTNET_CHAIN_ID = 5042002

DEFAULT_ARC_RPC_URL = "https://rpc.mainnet.arc.io"
DEFAULT_ARC_EXPLORER_URL = "https://explorer.arc.io"
DEFAULT_ARC_TESTNET_RPC_URL = "https://rpc.testnet.arc.io"
DEFAULT_ARC_TESTNET_EXPLORER_URL = "https://explorer.testnet.arc.io"

SETTLE_SIGNATURE = "settle(address,address,uint256,uint256,uint256,bytes)"


def get_arc_chain_id() -> int:
    """Return active Arc chain ID (5042 Mainnet or 5042002 Testnet)."""
    raw = os.environ.get("ARC_CHAIN_ID", "").strip().lower()
    assert isinstance(raw, str), "ARC_CHAIN_ID must be string"
    if raw in ("5042002", "testnet"):
        return ARC_TESTNET_CHAIN_ID
    assert ARC_CHAIN_ID == 5042, "Default Arc chain ID must be 5042"
    return ARC_CHAIN_ID


def rpc_url() -> str:
    """Return target Arc JSON-RPC endpoint for active chain."""
    override = os.environ.get("ARC_RPC_URL")
    if override:
        assert isinstance(override, str) and len(override) > 0
        return override
    cid = get_arc_chain_id()
    assert cid in (ARC_CHAIN_ID, ARC_TESTNET_CHAIN_ID)
    if cid == ARC_TESTNET_CHAIN_ID:
        return DEFAULT_ARC_TESTNET_RPC_URL
    return DEFAULT_ARC_RPC_URL


def explorer_url() -> str:
    """Return block explorer base URL for active chain."""
    override = os.environ.get("ARC_EXPLORER_URL")
    if override:
        assert isinstance(override, str) and len(override) > 0
        return override.rstrip("/")
    cid = get_arc_chain_id()
    assert cid in (ARC_CHAIN_ID, ARC_TESTNET_CHAIN_ID)
    if cid == ARC_TESTNET_CHAIN_ID:
        return DEFAULT_ARC_TESTNET_EXPLORER_URL
    return DEFAULT_ARC_EXPLORER_URL


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
