"""
AgentKeeper Configuration & Safety Invariants
"""

import os

# Default Supported EVM Chains
SUPPORTED_CHAINS: dict[int, str] = {
    1: "Ethereum Mainnet",
    10: "Optimism Mainnet",
    8453: "Base Mainnet",
    42161: "Arbitrum One",
    11155111: "Sepolia Testnet",
}

# KeeperHub Relay & Gateway Settings
KEEPERHUB_API_URL = os.environ.get("KEEPERHUB_API_URL", "https://api.keeperhub.com/v1")
KEEPERHUB_API_KEY = os.environ.get("KEEPERHUB_API_KEY", "")
AGENT_PRIVATE_KEY = os.environ.get("AGENT_PRIVATE_KEY", "")

# NASA Power of 10 Safety Invariant Constants
MAX_RETRY_ATTEMPTS = 10
MAX_CALLDATA_BYTES = 131072  # 128 KB
MAX_AUTONOMOUS_PAYMENT_USDC = 5.00  # Strict micro-payment budget per call ($5.00 USDC)
MAX_VALUE_WEI_CAP = (
    100000000000000000  # 0.10 ETH safety cap (~$250 max native transfer)
)
DEFAULT_REQUEST_TIMEOUT = 15.0
