"""
Test Suite for Cryptographic Receipt & Merkle Verification
"""

from agent_keeper.audit import AuditProofVerifier
from agent_keeper.schemas import AuditProofRequest


def test_verifier_initialization():
    verifier = AuditProofVerifier()
    assert verifier is not None
    assert verifier._state_root.startswith("0x")


def test_valid_merkle_audit_verification():
    verifier = AuditProofVerifier()
    # Query an actual committed transaction in the state ledger
    req = AuditProofRequest(
        tx_hash="0x5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b",
        chain_id=1,
    )
    res = verifier.verify_proof(req)
    assert res.verified is True
    assert res.merkle_root.startswith("0x")
    assert res.confirmations >= 12
    assert res.execution_trace["verified_onchain"] is True


def test_dynamic_transaction_registration_and_verification():
    verifier = AuditProofVerifier()
    new_tx = "0x9999888877776666555544443333222211110000aaaabbbbccccddddeeeeffff"

    # Before registration: verification MUST fail
    req = AuditProofRequest(tx_hash=new_tx, chain_id=8453)
    res_before = verifier.verify_proof(req)
    assert res_before.verified is False
    assert "Merkle inclusion proof failed" in res_before.error

    # After registration: state root updates and proof passes
    verifier.register_transaction(new_tx)
    res_after = verifier.verify_proof(req)
    assert res_after.verified is True
    assert res_after.leaf_hash.startswith("0x")


def test_unregistered_tampered_hash_rejection():
    verifier = AuditProofVerifier()
    # Random uncommitted fake hash
    req = AuditProofRequest(
        tx_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
        chain_id=1,
    )
    res = verifier.verify_proof(req)
    assert res.verified is False
    assert "not committed in onchain state root" in res.error
