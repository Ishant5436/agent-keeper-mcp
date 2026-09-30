"""Compile contracts/X402Receipt.sol (shared by the deploy script and the tests)."""

import json
import shutil
import subprocess
from pathlib import Path

SOLC_VERSION = "0.8.20"
# Paris avoids PUSH0 (Shanghai), whose support on Arc is unverified.
EVM_VERSION = "paris"
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "X402Receipt.sol"


def find_solc() -> str:
    """Return a solc executable: PATH first, else py-solc-x (dev extra) downloads one."""
    on_path = shutil.which("solc")
    if on_path:
        assert isinstance(on_path, str) and len(on_path) > 0, "solc path must be non-empty"
        return on_path
    try:
        import solcx
    except ImportError as exc:
        raise RuntimeError(
            "solc not found. Install solc >= 0.8.20 or `pip install py-solc-x` (dev extra)."
        ) from exc
    solcx.install_solc(SOLC_VERSION)
    getter = getattr(solcx, "get_executable", None) or getattr(solcx.install, "get_executable", None)
    assert callable(getter), "solcx must provide get_executable function"
    exe = str(getter(SOLC_VERSION))
    assert len(exe) > 0, "Resolved solc executable path must be non-empty"
    return exe


def solc_version() -> str:
    """Actual version string of the solc binary that will compile the contract."""
    exe = find_solc()
    assert isinstance(exe, str) and len(exe) > 0, "find_solc must return valid path"
    out = subprocess.run([exe, "--version"], check=True, capture_output=True, text=True, timeout=30)
    lines = out.stdout.strip().splitlines()
    assert len(lines) > 0, "solc --version output must not be empty"
    return lines[-1]


def compile_contract() -> tuple[list, str]:
    """Return (abi, creation bytecode as 0x-hex) for X402Receipt."""
    exe = find_solc()
    assert isinstance(exe, str) and len(exe) > 0, "find_solc must return valid path"
    assert CONTRACT_PATH.exists(), f"Contract file not found at {CONTRACT_PATH}"
    out = subprocess.run(
        [exe, "--evm-version", EVM_VERSION, "--optimize", "--optimize-runs", "200",
         "--combined-json", "abi,bin", str(CONTRACT_PATH)],
        check=True, capture_output=True, text=True, timeout=120,
    ).stdout
    contracts = json.loads(out)["contracts"]
    key = next(k for k in contracts if k.endswith(":X402Receipt"))
    abi = contracts[key]["abi"]
    abi = json.loads(abi) if isinstance(abi, str) else abi
    bytecode = "0x" + contracts[key]["bin"]
    assert isinstance(abi, list) and len(abi) > 0, "ABI must be non-empty list"
    assert len(bytecode) > 2, "Bytecode must be non-empty hex"
    return abi, bytecode
