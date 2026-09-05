#!/usr/bin/env python3
"""
AgentKeeper FastMCP Server
Exposes tools for:
- keeper_execute_tx: Execute onchain transactions via KeeperHub with MEV protection & retry management
- keeper_x402_settle: Autonomous HTTP 402 micro-payment settlement for paid APIs
- keeper_audit_verify: Cryptographic Merkle inclusion and execution receipt verifier
- keeper_agent_balance: Real-time multi-chain RPC balance and operational budget inspector
"""

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from agent_keeper.audit import AuditProofVerifier
from agent_keeper.config import PUBLIC_RPC_URLS, SUPPORTED_CHAINS
from agent_keeper.creditcoin import CreditcoinSettlementManager
from agent_keeper.relay import KeeperRelayClient
from agent_keeper.schemas import (
    AuditProofRequest,
    CreditcoinSettlementRequest,
    TxExecutionRequest,
    X402PaymentRequest,
)
from agent_keeper.x402 import X402PaymentManager

mcp = FastMCP(
    "agent-keeper",
    instructions=(
        "Autonomous onchain transaction gateway, x402 micro-payment solver, "
        "and cryptographic audit verification protocol for KeeperHub."
    ),
)

_audit_verifier = AuditProofVerifier()
_relay_client = KeeperRelayClient(audit_verifier=_audit_verifier)
_payment_manager = X402PaymentManager()
_creditcoin_manager = CreditcoinSettlementManager()


def _query_rpc_balance(address: str, chain_id: int) -> dict[str, Any]:
    """Query live onchain ETH balance via public JSON-RPC."""
    rpc_url = PUBLIC_RPC_URLS.get(chain_id)
    if not rpc_url:
        return {
            "error": f"No RPC configured for chain {chain_id}",
            "source": "unavailable",
        }

    try:
        with httpx.Client(timeout=3.5) as client:
            resp = client.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1,
                },
            )
            if resp.status_code == 200:
                result = resp.json().get("result")
                if result and isinstance(result, str):
                    val_wei = int(result, 16)
                    val_eth = val_wei / 10**18
                    return {
                        "balance_wei": val_wei,
                        "balance_eth": round(val_eth, 6),
                        "source": "live_rpc",
                    }
    except Exception as e:
        return {"error": str(e), "source": "rpc_unreachable"}

    return {"source": "unavailable"}


@mcp.tool()
def keeper_execute_tx(
    target_address: str,
    calldata_hex: str = "0x",
    value_wei: int = 0,
    chain_id: int = 1,
    max_priority_fee_gwei: float | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Execute an onchain transaction through KeeperHub's MEV-protected relay with automated gas optimization."""
    try:
        req = TxExecutionRequest(
            target_address=target_address,
            calldata_hex=calldata_hex,
            value_wei=value_wei,
            chain_id=chain_id,
            max_priority_fee_gwei=max_priority_fee_gwei,
            idempotency_key=idempotency_key,
        )
        res = _relay_client.execute_transaction(req)
        return res.model_dump()
    except Exception as e:
        return {"success": False, "error": str(e), "chain_id": chain_id}


@mcp.tool()
def keeper_x402_settle(
    resource_url: str,
    amount_usdc: float,
    recipient_address: str,
    token_address: str | None = None,
) -> dict[str, Any]:
    """Autonomously settle an HTTP 402 Payment Required challenge using EIP-712 payment permits."""
    try:
        req = X402PaymentRequest(
            resource_url=resource_url,
            amount_usdc=amount_usdc,
            recipient_address=recipient_address,
            token_address=token_address,
        )
        res = _payment_manager.settle_payment(req)
        return res.model_dump()
    except Exception as e:
        return {
            "success": False,
            "amount_usdc": amount_usdc,
            "recipient": recipient_address,
            "error": str(e),
        }


@mcp.tool()
def keeper_audit_verify(
    tx_hash: str | None = None,
    task_id: str | None = None,
    chain_id: int = 1,
) -> dict[str, Any]:
    """Cryptographically verify the Merkle proof, inclusion block, and execution receipt of an agent transaction."""
    try:
        req = AuditProofRequest(tx_hash=tx_hash, task_id=task_id, chain_id=chain_id)
        res = _audit_verifier.verify_proof(req)
        return res.model_dump()
    except Exception as e:
        return {"verified": False, "error": str(e)}


@mcp.tool()
def keeper_agent_balance(address: str | None = None) -> dict[str, Any]:
    """Inspect the AI agent's live multi-chain onchain treasury balances, spent budget, and remaining limits."""
    target_addr = address or _payment_manager.signer_address

    chain_queries = {
        "Base Mainnet (8453)": (8453, _query_rpc_balance(target_addr, 8453)),
        "Arbitrum One (42161)": (42161, _query_rpc_balance(target_addr, 42161)),
        "Ethereum Mainnet (1)": (1, _query_rpc_balance(target_addr, 1)),
    }

    balances: dict[str, Any] = {}
    for name, (_, data) in chain_queries.items():
        if data.get("source") == "live_rpc":
            balances[name] = {
                "ETH": f"{data.get('balance_eth', 0.0):.6f} ETH",
                "wei": data.get("balance_wei", 0),
                "source": "live_rpc",
            }
        else:
            balances[name] = {
                "ETH": "0.000000 ETH",
                "source": data.get("source", "unreachable"),
                "status": "sandbox_operational",
            }

    return {
        "success": True,
        "queried_address": target_addr,
        "spending_limit_usdc": _payment_manager.safety_limit,
        "total_spent_usdc": _payment_manager.total_spent,
        "remaining_budget_usdc": round(
            _payment_manager.safety_limit - _payment_manager.total_spent, 6
        ),
        "supported_chains": SUPPORTED_CHAINS,
        "balances": balances,
    }


@mcp.tool()
def keeper_creditcoin_settle(
    intent_id: str,
    solver_address: str,
    source_chain: str,
    source_tx_hash: str,
    expected_recipient: str,
    merkle_proof: list[tuple[str, str]],
    merkle_root: str,
) -> dict[str, Any]:
    """
    Settle a cross-chain task intent on Creditcoin 3.0 EVM (Chain ID 102031).
    Cryptographically verifies the source-chain Attestcoin Merkle proof and releases escrow reimbursement to the solver.
    """
    req = CreditcoinSettlementRequest(
        intent_id=intent_id,
        solver_address=solver_address,
        source_chain=source_chain,
        source_tx_hash=source_tx_hash,
        expected_recipient=expected_recipient,
        merkle_proof=merkle_proof,
        merkle_root=merkle_root,
    )

    receipt = _creditcoin_manager.execute_solver_reimbursement(
        intent_id=req.intent_id,
        solver_address=req.solver_address,
        source_chain=req.source_chain,
        source_tx_hash=req.source_tx_hash,
        expected_recipient=req.expected_recipient,
        merkle_proof=req.merkle_proof,
        merkle_root=req.merkle_root,
    )
    return receipt


if __name__ == "__main__":
    mcp.run()
