"""Compile contracts/X402Receipt.sol and exercise it on an in-memory EVM (eth-tester)."""

import ast
import re
import secrets

import pytest

pytest.importorskip("eth_tester")
pytest.importorskip("web3")

from eth_account import Account  # noqa: E402
from eth_account.messages import encode_typed_data  # noqa: E402
from web3 import Web3  # noqa: E402
from web3.providers.eth_tester import EthereumTesterProvider  # noqa: E402

from agent_keeper.verifier_build import compile_contract  # noqa: E402
from agent_keeper.x402 import build_permit_typed_data  # noqa: E402

SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
PAYER = Account.create()
PAYEE = Account.create().address


@pytest.fixture(scope="module")
def env():
    w3 = Web3(EthereumTesterProvider())
    abi, bytecode = compile_contract()
    deployer = w3.eth.accounts[0]
    tx = w3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact({"from": deployer})
    addr = w3.eth.wait_for_transaction_receipt(tx)["contractAddress"]
    return w3, w3.eth.contract(address=addr, abi=abi), deployer


def _now(w3):
    return w3.eth.get_block("latest")["timestamp"]


def _sign(w3, chain_id, contract_addr, *, key=PAYER, payer=None, payee=PAYEE, amount=250_000,
          nonce=None, deadline=None):
    nonce = secrets.randbits(256) if nonce is None else nonce
    deadline = _now(w3) + 3600 if deadline is None else deadline
    payer = key.address if payer is None else payer
    data = build_permit_typed_data(chain_id, contract_addr, payer, payee, amount, nonce, deadline)
    sig = Account.sign_message(encode_typed_data(full_message=data), private_key=key.key).signature
    return (payer, payee, amount, nonce, deadline, bytes(sig))


def _revert_name(contract, args):
    """Simulate the call; return the custom error name it reverts with (or None)."""
    try:
        contract.functions.settle(*args).call()
    except Exception as exc:  # web3/eth-tester raise different types per version
        text = str(exc)
        match = re.search(r"(b'.*'|b\".*\")\s*$", text)
        data = ast.literal_eval(match.group(1)) if match else b""
        for name in ("Expired", "NonceUsed", "BadSignature"):
            if name in text or data[:4] == bytes(Web3.keccak(text=f"{name}()")[:4]):
                return name
        raise
    return None


def test_valid_signature_accepted_and_event_emitted(env):
    w3, c, sender = env
    args = _sign(w3, w3.eth.chain_id, c.address)
    tx = c.functions.settle(*args).transact({"from": sender})
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    assert receipt["status"] == 1
    logs = c.events.Settled().process_receipt(receipt)
    assert len(logs) == 1
    ev = logs[0]["args"]
    assert (ev["payer"], ev["payee"], ev["amount"], ev["nonce"]) == (args[0], args[1], args[2], args[3])
    assert c.functions.used(args[0], args[3]).call() is True


def test_wrong_signer_rejected(env):
    w3, c, _ = env
    attacker = Account.create()
    args = _sign(w3, w3.eth.chain_id, c.address, key=attacker, payer=PAYER.address)
    assert _revert_name(c, args) == "BadSignature"


def test_tampered_fields_rejected(env):
    w3, c, _ = env
    payer, payee, amount, nonce, deadline, sig = _sign(w3, w3.eth.chain_id, c.address)
    assert _revert_name(c, (payer, payee, amount + 1, nonce, deadline, sig)) == "BadSignature"
    assert _revert_name(c, (payer, Account.create().address, amount, nonce, deadline, sig)) == "BadSignature"


def test_expired_deadline_rejected(env):
    w3, c, _ = env
    args = _sign(w3, w3.eth.chain_id, c.address, deadline=_now(w3) - 1)
    assert _revert_name(c, args) == "Expired"


def test_replayed_nonce_rejected(env):
    w3, c, sender = env
    args = _sign(w3, w3.eth.chain_id, c.address)
    w3.eth.wait_for_transaction_receipt(c.functions.settle(*args).transact({"from": sender}))
    assert _revert_name(c, args) == "NonceUsed"
    # Same nonce, fresh valid signature over different fields: still burned.
    again = _sign(w3, w3.eth.chain_id, c.address, nonce=args[3], amount=1)
    assert _revert_name(c, again) == "NonceUsed"


def test_nonce_is_scoped_per_payer(env):
    w3, c, sender = env
    other = Account.create()
    nonce = secrets.randbits(256)
    for key in (PAYER, other):
        args = _sign(w3, w3.eth.chain_id, c.address, key=key, nonce=nonce)
        receipt = w3.eth.wait_for_transaction_receipt(c.functions.settle(*args).transact({"from": sender}))
        assert receipt["status"] == 1


def test_wrong_chain_id_rejected(env):
    w3, c, _ = env
    args = _sign(w3, w3.eth.chain_id + 1, c.address)
    assert _revert_name(c, args) == "BadSignature"


def test_wrong_verifying_contract_rejected(env):
    w3, c, _ = env
    other_contract = Account.create().address
    args = _sign(w3, w3.eth.chain_id, other_contract)
    assert _revert_name(c, args) == "BadSignature"


def test_high_s_malleable_signature_rejected(env):
    w3, c, _ = env
    payer, payee, amount, nonce, deadline, sig = _sign(w3, w3.eth.chain_id, c.address)
    r, s, v = sig[:32], int.from_bytes(sig[32:64], "big"), sig[64]
    assert s <= SECP256K1_N // 2  # eth_account emits canonical low-s
    twin = r + (SECP256K1_N - s).to_bytes(32, "big") + bytes([55 - v])  # flips 27<->28
    assert _revert_name(c, (payer, payee, amount, nonce, deadline, twin)) == "BadSignature"


def test_malformed_signature_length_and_zero_payer_rejected(env):
    w3, c, _ = env
    payer, payee, amount, nonce, deadline, sig = _sign(w3, w3.eth.chain_id, c.address)
    assert _revert_name(c, (payer, payee, amount, nonce, deadline, sig[:64])) == "BadSignature"
    zero = "0x" + "00" * 20
    assert _revert_name(c, (zero, payee, amount, nonce, deadline, b"\x00" * 65)) == "BadSignature"


def test_contract_is_non_custodial_no_payable_or_admin_surface(env):
    _, c, _ = env
    for item in c.abi:
        if item["type"] in ("function", "constructor", "receive", "fallback"):
            assert item.get("stateMutability") != "payable", item
        if item["type"] in ("receive", "fallback"):
            pytest.fail("contract must not accept plain ETH/USDC transfers")
    names = {i["name"] for i in c.abi if i["type"] == "function"}
    assert names == {"settle", "used", "domainSeparator", "NAME", "VERSION"}


def test_deployed_bytecode_holds_no_funds_by_default(env):
    w3, c, _ = env
    assert w3.eth.get_balance(c.address) == 0


def test_end_to_end_manager_output_is_redeemable_on_chain(env, monkeypatch):
    """keeper_x402_settle's own response (signature + permit) settles on the deployed contract."""
    from agent_keeper import x402
    from agent_keeper.arc_chain import encode_settle_calldata
    from agent_keeper.schemas import X402PaymentRequest

    w3, c, sender = env
    # eth-tester's chain id is not 5042: point the manager's Arc id at it for this test only.
    monkeypatch.setattr(x402, "ARC_CHAIN_ID", w3.eth.chain_id)
    monkeypatch.setenv("ARC_X402_VERIFIER", c.address)
    req = X402PaymentRequest.model_construct(
        resource_url="https://api.arc.quant/v1/feed", amount_usdc=0.25, recipient_address=PAYEE,
        token_address=None, chain_id=w3.eth.chain_id,
    )
    mgr = x402.X402PaymentManager(private_key=Account.create().key.hex())
    res = mgr.settle_payment(req)
    assert res.success is True and res.permit is not None
    p = res.permit
    assert p["verifyingContract"] == c.address and p["payer"] == mgr.signer_address
    data = encode_settle_calldata(
        p["payer"], p["payee"], p["amount"], int(p["nonce"]), p["deadline"], bytes.fromhex(res.signature[2:])
    )
    receipt = w3.eth.wait_for_transaction_receipt(
        w3.eth.send_transaction({"from": sender, "to": c.address, "data": data})
    )
    assert receipt["status"] == 1
    assert c.functions.used(p["payer"], int(p["nonce"])).call() is True
