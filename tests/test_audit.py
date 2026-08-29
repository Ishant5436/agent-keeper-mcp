"""
Test Suite for Cryptographic Receipt & Merkle Verification
"""

from agent_keeper.audit import AuditProofVerifier
from agent_keeper.schemas import AuditProofRequest


def test_verifier_initialization():
    verifier = AuditProofVerifier()
    assert verifier is not None


def test_valid_merkle_audit_verification():
    verifier = AuditProofVerifier()
    req = AuditProofRequest(
        tx_hash="0x5a1b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b",
        chain_id=1,
    )
    res = verifier.verify_proof(req)
    assert res.verified is True
    assert res.merkle_root.startswith("0x")
    assert res.confirmations >= 12
    assert res.execution_trace["verified_onchain"] is True


def test_tampered_proof_rejection():
    verifier = AuditProofVerifier()
    req = AuditProofRequest(
        tx_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
        chain_id=1,
    )
    res = verifier.verify_proof(req, tamper_proof=True)
    assert res.verified is False
    assert "Merkle root mismatch" in res.error
