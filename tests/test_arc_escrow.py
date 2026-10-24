"""Compile contracts/ArcAgentEscrow.sol and exercise it on an in-memory EVM (eth-tester)."""

import hashlib
import pytest

pytest.importorskip("eth_tester")
pytest.importorskip("web3")

from web3 import Web3  # noqa: E402
from web3.providers.eth_tester import EthereumTesterProvider  # noqa: E402
from agent_keeper.verifier_build import compile_contract  # noqa: E402


@pytest.fixture(scope="module")
def escrow_env():
    w3 = Web3(EthereumTesterProvider())
    abi, bytecode = compile_contract("ArcAgentEscrow")
    deployer = w3.eth.accounts[0]
    tx = w3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact({"from": deployer})
    addr = w3.eth.wait_for_transaction_receipt(tx)["contractAddress"]
    return w3, w3.eth.contract(address=addr, abi=abi), deployer


def _now(w3):
    return w3.eth.get_block("latest")["timestamp"]


def test_escrow_deposit_and_release(escrow_env):
    w3, contract, _ = escrow_env
    payer = w3.eth.accounts[1]
    provider = w3.eth.accounts[2]
    task_id = hashlib.sha256(b"task-test-deposit-and-release").digest()
    amount = w3.to_wei(0.5, "ether")  # 0.5 USDC on Arc

    init_provider_bal = w3.eth.get_balance(provider)

    # Deposit
    tx1 = contract.functions.depositEscrow(task_id, provider, 3600).transact({
        "from": payer,
        "value": amount
    })
    rcpt1 = w3.eth.wait_for_transaction_receipt(tx1)
    assert rcpt1["status"] == 1

    esc = contract.functions.getEscrow(task_id).call()
    assert esc[0] == payer
    assert esc[1] == provider
    assert esc[2] == amount
    assert esc[4] == 1  # ACTIVE

    # Release
    tx2 = contract.functions.releaseEscrow(task_id).transact({"from": payer})
    rcpt2 = w3.eth.wait_for_transaction_receipt(tx2)
    assert rcpt2["status"] == 1

    post_provider_bal = w3.eth.get_balance(provider)
    assert post_provider_bal - init_provider_bal == amount

    esc_after = contract.functions.getEscrow(task_id).call()
    assert esc_after[4] == 2  # RELEASED


def test_escrow_emergency_refund_after_timeout(escrow_env):
    w3, contract, _ = escrow_env
    payer = w3.eth.accounts[3]
    provider = w3.eth.accounts[4]
    task_id = hashlib.sha256(b"task-test-refund-timeout").digest()
    amount = w3.to_wei(1.0, "ether")
    timeout = 100  # 100 seconds

    # Deposit
    contract.functions.depositEscrow(task_id, provider, timeout).transact({
        "from": payer,
        "value": amount
    })

    # Attempt premature refund -> must fail
    with pytest.raises(Exception) as exc:
        contract.functions.refundEscrow(task_id).transact({"from": payer})
    assert "TimeoutNotReached" in str(exc.value) or "revert" in str(exc.value)

    # Time-warp past timeout on eth-tester
    w3.provider.ethereum_tester.time_travel(_now(w3) + 200)

    # Now refund must succeed
    tx = contract.functions.refundEscrow(task_id).transact({"from": payer})
    rcpt = w3.eth.wait_for_transaction_receipt(tx)
    assert rcpt["status"] == 1

    esc_after = contract.functions.getEscrow(task_id).call()
    assert esc_after[4] == 3  # REFUNDED


def test_escrow_unauthorized_release_blocked(escrow_env):
    w3, contract, _ = escrow_env
    payer = w3.eth.accounts[1]
    provider = w3.eth.accounts[2]
    attacker = w3.eth.accounts[5]
    task_id = hashlib.sha256(b"task-test-unauthorized-release").digest()
    amount = w3.to_wei(0.2, "ether")

    contract.functions.depositEscrow(task_id, provider, 3600).transact({
        "from": payer,
        "value": amount
    })

    # Attacker tries to release
    with pytest.raises(Exception):
        contract.functions.releaseEscrow(task_id).transact({"from": attacker})


def test_direct_micropayment(escrow_env):
    w3, contract, _ = escrow_env
    sender = w3.eth.accounts[6]
    recipient = w3.eth.accounts[7]
    amount = w3.to_wei(0.05, "ether")
    metadata = hashlib.sha256(b"micropayment-job-note").digest()

    init_bal = w3.eth.get_balance(recipient)

    tx = contract.functions.directMicropayment(recipient, metadata).transact({
        "from": sender,
        "value": amount
    })
    rcpt = w3.eth.wait_for_transaction_receipt(tx)
    assert rcpt["status"] == 1

    post_bal = w3.eth.get_balance(recipient)
    assert post_bal - init_bal == amount
