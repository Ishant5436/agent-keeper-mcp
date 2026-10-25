"""HashKey Chain network parameters and deterministic RPC client."""

import json
import os
import urllib.error
import urllib.request

HASHKEY_TESTNET_CHAIN_ID = 133
HASHKEY_TESTNET_RPC_URL = "https://testnet.hsk.xyz"
HASHKEY_TESTNET_EXPLORER = "https://testnet-explorer.hsk.xyz"
NATIVE_SYMBOL = "HSK"
NATIVE_DECIMALS = 18


def rpc_url() -> str:
    return os.getenv("HASHKEY_RPC_URL", HASHKEY_TESTNET_RPC_URL).strip() or HASHKEY_TESTNET_RPC_URL


def explorer_url(tx_hash_or_addr: str) -> str:
    assert isinstance(tx_hash_or_addr, str) and tx_hash_or_addr.startswith("0x"), "Must be valid hex"
    base = os.getenv("HASHKEY_EXPLORER_URL", HASHKEY_TESTNET_EXPLORER).rstrip("/")
    if len(tx_hash_or_addr) == 66:
        return f"{base}/tx/{tx_hash_or_addr}"
    return f"{base}/address/{tx_hash_or_addr}"


def rpc_call(method: str, params: list, rpc: str | None = None) -> str:
    assert isinstance(method, str) and len(method) > 0, "Method must be non-empty string"
    assert isinstance(params, list), "Params must be list"
    url = rpc or rpc_url()
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AgentKeeper-HashKey/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"HashKey RPC call failed: {exc}") from exc

    if "error" in data:
        raise RuntimeError(f"HashKey RPC error: {data['error']}")
    return data.get("result", "")


def get_hsk_balance(address: str) -> int:
    assert isinstance(address, str) and address.startswith("0x") and len(address) == 42, "Invalid address"
    res = rpc_call("eth_getBalance", [address, "latest"])
    assert isinstance(res, str) and res.startswith("0x"), "Expected hex balance"
    return int(res, 16)
