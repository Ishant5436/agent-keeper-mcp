"""Tests for HashKey Chain parameters, RPC helper, and offline contract deployment."""

import pytest
from agent_keeper.hashkey_chain import (
    HASHKEY_TESTNET_CHAIN_ID,
    HASHKEY_TESTNET_EXPLORER,
    HASHKEY_TESTNET_RPC_URL,
    explorer_url,
    rpc_url,
)
from agent_keeper.verifier_build import compile_contract


def test_hashkey_constants():
    assert HASHKEY_TESTNET_CHAIN_ID == 133
    assert HASHKEY_TESTNET_RPC_URL == "https://testnet.hsk.xyz"
    assert "hsk.xyz" in HASHKEY_TESTNET_EXPLORER


def test_hashkey_explorer_formatting():
    tx = "0x" + "aa" * 32
    addr = "0x" + "bb" * 20
    assert explorer_url(tx) == f"{HASHKEY_TESTNET_EXPLORER}/tx/{tx}"
    assert explorer_url(addr) == f"{HASHKEY_TESTNET_EXPLORER}/address/{addr}"


def test_hashkey_escrow_bytecode_compile():
    abi, bytecode = compile_contract("ArcAgentEscrow")
    assert len(abi) >= 10
    assert bytecode.startswith("0x")
    assert len(bytecode) > 1000
