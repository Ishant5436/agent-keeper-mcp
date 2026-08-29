"""
AgentKeeper Configuration & Chain Constants
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

# NASA Power of 10 Invariant Constants
MAX_RETRY_ATTEMPTS = 10
MAX_CALLDATA_BYTES = 131072  # 128 KB
MAX_AUTONOMOUS_PAYMENT_USDC = 5.00  # Strict safety budget per single call
DEFAULT_REQUEST_TIMEOUT = 15.0
