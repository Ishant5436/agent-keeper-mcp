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
        return on_path
    try:
        import solcx
    except ImportError as exc:
        raise RuntimeError(
            "solc not found. Install solc >= 0.8.20 or `pip install py-solc-x` (dev extra)."
        ) from exc
    solcx.install_solc(SOLC_VERSION)
    return str(solcx.get_executable(SOLC_VERSION))


def compile_contract() -> tuple[list, str]:
    """Return (abi, creation bytecode as 0x-hex) for X402Receipt."""
    out = subprocess.run(
        [find_solc(), "--evm-version", EVM_VERSION, "--optimize", "--optimize-runs", "200",
         "--combined-json", "abi,bin", str(CONTRACT_PATH)],
        check=True, capture_output=True, text=True, timeout=120,
    ).stdout
    contracts = json.loads(out)["contracts"]
    key = next(k for k in contracts if k.endswith(":X402Receipt"))
    abi = contracts[key]["abi"]
    abi = json.loads(abi) if isinstance(abi, str) else abi
    return abi, "0x" + contracts[key]["bin"]
