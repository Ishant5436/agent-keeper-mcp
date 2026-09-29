"""Shared pytest fixtures."""

import pytest

# Obviously-fake checksum address so x402 signing works in tests. It has no
# contract behind it and must never be used outside the test suite.
TEST_VERIFIER = "0xABaBaBaBABabABabAbAbABAbABabababaBaBABaB"


@pytest.fixture(autouse=True)
def _x402_verifier_env(monkeypatch, request):
    if request.node.get_closest_marker("no_verifier_env"):
        monkeypatch.delenv("ARC_X402_VERIFIER", raising=False)
    else:
        monkeypatch.setenv("ARC_X402_VERIFIER", TEST_VERIFIER)
