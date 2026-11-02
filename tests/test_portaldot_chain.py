"""Tests for Portaldot Network V3.0 parameters, RPC helper, and offline contract deployment."""

import pytest
from agent_keeper.portaldot_chain import (
    PORTALDOT_V3_TESTNET_CHAIN_ID,
    PORTALDOT_V3_TESTNET_EXPLORER,
    PORTALDOT_V3_TESTNET_RPC_URL,
    NATIVE_SYMBOL,
    NATIVE_DECIMALS,
    explorer_url,
    rpc_url,
)
from agent_keeper.verifier_build import compile_contract


def test_portaldot_v3_constants():
    assert PORTALDOT_V3_TESTNET_CHAIN_ID == 420420777
    assert PORTALDOT_V3_TESTNET_RPC_URL == "https://test-evm-rpc-v3.portaldot.dev"
    assert "portaldot" in PORTALDOT_V3_TESTNET_EXPLORER
    assert NATIVE_SYMBOL == "POT"
    assert NATIVE_DECIMALS == 14


def test_portaldot_v3_explorer_formatting():
    tx = "0x" + "aa" * 32
    addr = "0x" + "bb" * 20
    assert explorer_url(tx) == f"{PORTALDOT_V3_TESTNET_EXPLORER}/tx/{tx}"
    assert explorer_url(addr) == f"{PORTALDOT_V3_TESTNET_EXPLORER}/address/{addr}"


def test_portaldot_escrow_bytecode_compile():
    abi, bytecode = compile_contract("ArcAgentEscrow")
    assert len(abi) >= 10
    assert bytecode.startswith("0x")
    assert len(bytecode) > 1000


def test_portaldot_x402_receipt_bytecode_compile():
    abi, bytecode = compile_contract("X402Receipt")
    assert len(abi) >= 4
    assert bytecode.startswith("0x")
    assert len(bytecode) > 1000
