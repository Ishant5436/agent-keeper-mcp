"""Deploy/broadcast script behaviour: dry-run by default, no key handling, calldata really settles."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from agent_keeper.arc_chain import encode_settle_calldata

ROOT = Path(__file__).resolve().parents[1]
CANARY = "CANARY-NOT-A-KEY-7f3e91"  # sentinel string, not a key: must never appear in any output
VERIFIER = "0xABaBaBaBABabABabAbAbABAbABabababaBaBABaB"


def _run(script, *args, env_extra=None, drop=()):
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env.update({"PYTHONPATH": str(ROOT / "src"), "ARC_RPC_URL": "http://127.0.0.1:9", "ARC_RPC_TIMEOUT": "0.3"})
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        env=env, capture_output=True, text=True, timeout=180,
    )


def test_deploy_dry_run_is_default_and_ignores_key():
    r = _run("deploy_arc_verifier.py", "--gas-price-gwei", "1", env_extra={"AGENT_PRIVATE_KEY": CANARY})
    assert r.returncode == 0, r.stderr
    assert "DRY RUN" in r.stdout and "Unsigned deployment tx" in r.stdout and "USDC" in r.stdout
    assert CANARY not in r.stdout + r.stderr


def test_deploy_broadcast_requires_key_in_env():
    r = _run("deploy_arc_verifier.py", "--broadcast", drop=("AGENT_PRIVATE_KEY",))
    assert r.returncode == 1 and "AGENT_PRIVATE_KEY" in r.stdout


def test_settle_script_fails_closed_without_verifier():
    r = _run("broadcast_live_arc_tx.py", drop=("ARC_X402_VERIFIER", "AGENT_PRIVATE_KEY"))
    assert r.returncode == 1 and "ARC_X402_VERIFIER" in r.stdout


def test_settle_script_dry_run_ignores_key_and_broadcast_needs_it():
    env = {"ARC_X402_VERIFIER": VERIFIER, "AGENT_PRIVATE_KEY": CANARY}
    r = _run("broadcast_live_arc_tx.py", env_extra=env)
    assert r.returncode == 0 and "DRY RUN" in r.stdout
    assert CANARY not in r.stdout + r.stderr
    r = _run("broadcast_live_arc_tx.py", "--broadcast", env_extra={"ARC_X402_VERIFIER": VERIFIER},
             drop=("AGENT_PRIVATE_KEY",))
    assert r.returncode == 1 and "AGENT_PRIVATE_KEY" in r.stdout


def test_settle_broadcast_signs_and_sends_with_mocked_rpc(monkeypatch):
    """--broadcast path with a mocked RPC: signs a real tx to the verifier carrying settle() calldata."""
    from eth_account import Account

    from agent_keeper.arc_chain import SETTLE_SIGNATURE
    from eth_utils import keccak

    sys.path.insert(0, str(ROOT / "scripts"))
    import broadcast_live_arc_tx as bcast

    sent = {}

    def fake_rpc(method, params, *a, **kw):
        if method == "eth_chainId":
            return hex(5042)
        if method == "eth_getCode":
            return "0x6080"
        if method in ("eth_call", "eth_getTransactionReceipt"):
            return {"status": "0x1", "blockNumber": "0x1", "gasUsed": "0x1", "transactionHash": "0x" + "a" * 64} \
                if method == "eth_getTransactionReceipt" else "0x"
        if method == "eth_estimateGas":
            return hex(60_000)
        if method == "eth_getTransactionCount":
            return "0x3"
        if method == "eth_gasPrice":
            return hex(10**10)
        if method == "eth_sendRawTransaction":
            sent["raw"] = params[0]
            return "0x" + "a" * 64
        raise AssertionError(method)

    monkeypatch.setattr(bcast, "rpc_call", fake_rpc)
    monkeypatch.setattr(bcast, "wait_for_receipt", lambda h: fake_rpc("eth_getTransactionReceipt", [h]))
    acct = Account.create()
    monkeypatch.setenv("AGENT_PRIVATE_KEY", acct.key.hex())
    args = type("A", (), {"payee": None, "amount": 1000, "payer": None})()
    assert bcast.broadcast(VERIFIER, args) == 0
    tx = Account.recover_transaction(sent["raw"])
    assert tx == acct.address
    from eth_account._utils.legacy_transactions import (  # decode to inspect `to` and calldata
        Transaction,
    )
    decoded = Transaction.from_bytes(bytes.fromhex(sent["raw"][2:]))
    assert decoded.to.hex().lower() == VERIFIER[2:].lower() and decoded.value == 0
    assert decoded.data[:4] == keccak(text=SETTLE_SIGNATURE)[:4]


def test_script_calldata_is_accepted_by_compiled_contract():
    pytest.importorskip("eth_tester")
    from eth_account import Account
    from eth_account.messages import encode_typed_data
    from web3 import Web3
    from web3.providers.eth_tester import EthereumTesterProvider

    from agent_keeper.verifier_build import compile_contract
    from agent_keeper.x402 import build_permit_typed_data

    w3 = Web3(EthereumTesterProvider())
    abi, bytecode = compile_contract()
    sender = w3.eth.accounts[0]
    tx = w3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact({"from": sender})
    addr = w3.eth.wait_for_transaction_receipt(tx)["contractAddress"]

    key = Account.create()
    payee = Account.create().address
    nonce, deadline = secrets.randbits(256), w3.eth.get_block("latest")["timestamp"] + 600
    permit = build_permit_typed_data(w3.eth.chain_id, addr, key.address, payee, 1000, nonce, deadline)
    sig = Account.sign_message(encode_typed_data(full_message=permit), private_key=key.key).signature
    data = encode_settle_calldata(key.address, payee, 1000, nonce, deadline, bytes(sig))

    receipt = w3.eth.wait_for_transaction_receipt(
        w3.eth.send_transaction({"from": sender, "to": addr, "data": data})
    )
    assert receipt["status"] == 1
    contract = w3.eth.contract(address=addr, abi=abi)
    assert contract.functions.used(key.address, nonce).call() is True
