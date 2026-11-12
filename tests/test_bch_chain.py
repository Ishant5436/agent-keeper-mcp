"""
Tests for Bitcoin Cash (BCH) and CashTokens settlement engine in AgentKeeper.
Adheres strictly to Gerard J. Holzmann's Power of 10 Deterministic Safety Invariants.
"""

import pytest
from agent_keeper.bch_chain import (
    BCH_MAINNET_EXPLORER,
    BCH_CHIPNET_EXPLORER,
    CashTokenCapability,
    CashTokenOutput,
    encode_cashtoken_prefix,
    decode_cashtoken_prefix,
    verify_bch_address,
    verify_agent_spending_guard,
    format_bch_explorer_url,
    construct_cashtoken_covenant_descriptor,
)


def test_bch_address_validation():
    """Verify CashAddr format checks for mainnet and chipnet."""
    # Mainnet CashAddr
    valid_mainnet = "bitcoincash:qq4vqn04qj5j7q8w3h99yvh2v6z6z5r5v5s5z9h6r7"
    assert verify_bch_address(valid_mainnet, network="mainnet") is True
    assert verify_bch_address("invalid_address", network="mainnet") is False

    # Chipnet CashAddr
    valid_chipnet = "bchtest:qq4vqn04qj5j7q8w3h99yvh2v6z6z5r5v5s5z9h6r7"
    assert verify_bch_address(valid_chipnet, network="chipnet") is True
    assert verify_bch_address(valid_mainnet, network="chipnet") is False


def test_cashtoken_prefix_encoding_and_decoding_roundtrip():
    """Verify CashTokens CHIP-2022-02 prefix encoding and decoding."""
    category_id = "a" * 64
    token = CashTokenOutput(
        category_id=category_id,
        ft_amount=5000,
        capability=CashTokenCapability.MUTABLE,
        commitment=b"agent-task-session-01",
    )
    
    encoded = encode_cashtoken_prefix(token)
    assert len(encoded) > 0
    assert encoded[0] == 0xef  # PREFIX_TOKEN opcode

    decoded = decode_cashtoken_prefix(encoded)
    assert decoded.category_id == category_id
    assert decoded.ft_amount == 5000
    assert decoded.capability == CashTokenCapability.MUTABLE
    assert decoded.commitment == b"agent-task-session-01"


def test_cashtoken_prefix_without_nft():
    """Verify CashTokens prefix with only Fungible Tokens."""
    category_id = "b" * 64
    token = CashTokenOutput(
        category_id=category_id,
        ft_amount=1000000,
        capability=None,
        commitment=b"",
    )
    encoded = encode_cashtoken_prefix(token)
    assert encoded[0] == 0xef
    
    decoded = decode_cashtoken_prefix(encoded)
    assert decoded.category_id == category_id
    assert decoded.ft_amount == 1000000
    assert decoded.capability is None
    assert decoded.commitment == b""


def test_cashtoken_prefix_without_ft():
    """Verify CashTokens prefix with only NFT commitment and capability."""
    category_id = "c" * 64
    token = CashTokenOutput(
        category_id=category_id,
        ft_amount=0,
        capability=CashTokenCapability.MINTING,
        commitment=b"genesis-authority",
    )
    encoded = encode_cashtoken_prefix(token)
    decoded = decode_cashtoken_prefix(encoded)
    assert decoded.category_id == category_id
    assert decoded.ft_amount == 0
    assert decoded.capability == CashTokenCapability.MINTING
    assert decoded.commitment == b"genesis-authority"


def test_cashtoken_invalid_inputs():
    """Ensure invalid inputs fail fast with assertions."""
    # Invalid category length (must be 32 bytes / 64 hex chars)
    with pytest.raises(AssertionError):
        CashTokenOutput(
            category_id="tooshort",
            ft_amount=10,
            capability=None,
            commitment=b"",
        )

    # Commitment exceeding 40 bytes consensus limit
    with pytest.raises(AssertionError):
        CashTokenOutput(
            category_id="d" * 64,
            ft_amount=0,
            capability=CashTokenCapability.NONE,
            commitment=b"x" * 41,
        )

    # Negative FT amount
    with pytest.raises(AssertionError):
        CashTokenOutput(
            category_id="e" * 64,
            ft_amount=-1,
            capability=None,
            commitment=b"",
        )


def test_agent_spending_guard():
    """Verify AI Agent deterministic spending invariants."""
    policy = {
        "max_satoshis_per_tx": 50000,
        "allowed_categories": ["f" * 64],
        "max_ft_per_tx": 1000,
    }
    
    # Valid spend within policy limits
    valid_tx = {
        "spend_satoshis": 15000,
        "token_category": "f" * 64,
        "token_amount": 500,
    }
    allowed, reason = verify_agent_spending_guard(valid_tx, policy)
    assert allowed is True
    assert reason == "APPROVED"

    # Exceeding BCH satoshis limit
    excess_bch_tx = {
        "spend_satoshis": 60000,
        "token_category": "f" * 64,
        "token_amount": 500,
    }
    allowed, reason = verify_agent_spending_guard(excess_bch_tx, policy)
    assert allowed is False
    assert "Exceeds max satoshis" in reason

    # Disallowed token category
    unauth_category_tx = {
        "spend_satoshis": 1000,
        "token_category": "0" * 64,
        "token_amount": 10,
    }
    allowed, reason = verify_agent_spending_guard(unauth_category_tx, policy)
    assert allowed is False
    assert "Unauthorized token category" in reason

    # Exceeding token amount
    excess_ft_tx = {
        "spend_satoshis": 1000,
        "token_category": "f" * 64,
        "token_amount": 2000,
    }
    allowed, reason = verify_agent_spending_guard(excess_ft_tx, policy)
    assert allowed is False
    assert "Exceeds max FT amount" in reason


def test_bch_explorer_urls():
    """Verify deterministic explorer URL resolution."""
    txid = "1" * 64
    mainnet_url = format_bch_explorer_url(txid, network="mainnet")
    assert mainnet_url == f"{BCH_MAINNET_EXPLORER}/tx/{txid}"

    chipnet_url = format_bch_explorer_url(txid, network="chipnet")
    assert chipnet_url == f"{BCH_CHIPNET_EXPLORER}/tx/{txid}"


def test_cashtoken_covenant_descriptor():
    """Verify deterministic covenant descriptor construction."""
    category_id = "2" * 64
    desc = construct_cashtoken_covenant_descriptor(
        covenant_name="AgentKeeperBudgetGuard",
        category_id=category_id,
        max_spend_sats=100000,
        oracle_pubkey="03" + "3" * 64,
    )
    assert desc["name"] == "AgentKeeperBudgetGuard"
    assert desc["category_id"] == category_id
    assert desc["max_spend_sats"] == 100000
    assert "locking_bytecode_pattern" in desc
