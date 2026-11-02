"""Portaldot Network V3.0 parameters and deterministic RPC client."""

import json
import os
import urllib.error
import urllib.request

PORTALDOT_V3_TESTNET_CHAIN_ID = 420420777
PORTALDOT_V3_TESTNET_RPC_URL = "https://test-evm-rpc-v3.portaldot.dev"
PORTALDOT_V3_TESTNET_EXPLORER = "https://testnet-explorer.portaldot.dev"
NATIVE_SYMBOL = "POT"
NATIVE_DECIMALS = 14


def rpc_url() -> str:
    url = os.getenv("PORTALDOT_RPC_URL", PORTALDOT_V3_TESTNET_RPC_URL).strip()
    assert isinstance(url, str) and len(url) > 0, "RPC URL must be non-empty"
    assert url.startswith("http://") or url.startswith("https://"), "Invalid scheme"
    return url or PORTALDOT_V3_TESTNET_RPC_URL


def explorer_url(tx_hash_or_addr: str) -> str:
    assert isinstance(tx_hash_or_addr, str) and tx_hash_or_addr.startswith("0x"), "Must be valid hex"
    assert len(tx_hash_or_addr) in (42, 66), "Expected 20-byte address or 32-byte tx hash"
    base = os.getenv("PORTALDOT_EXPLORER_URL", PORTALDOT_V3_TESTNET_EXPLORER).rstrip("/")
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
        headers={"Content-Type": "application/json", "User-Agent": "AgentKeeper-Portaldot/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Portaldot RPC call failed: {exc}") from exc

    if "error" in data:
        raise RuntimeError(f"Portaldot RPC error: {data['error']}")
    return data.get("result", "")


def get_pot_balance(address: str) -> int:
    assert isinstance(address, str) and address.startswith("0x") and len(address) == 42, "Invalid address"
    res = rpc_call("eth_getBalance", [address, "latest"])
    assert isinstance(res, str) and res.startswith("0x"), "Expected hex balance"
    return int(res, 16)
