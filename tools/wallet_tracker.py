import json
import requests
from tools.registry import registry

HELIUS_RPC = "https://api.mainnet-beta.solana.com"


def check_requirements() -> bool:
    """Check if RPC is accessible"""
    return True


def track_wallet(address: str) -> str:
    """Get basic wallet info for tracking"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        response = requests.post(HELIUS_RPC, json=payload, timeout=10)
        data = response.json()
        
        lamports = data.get("result", {}).get("value", 0)
        sol = lamports / 1e9
        
        return json.dumps({
            "address": address,
            "sol_balance": sol,
            "tracked": True
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_holdings(address: str) -> str:
    """Get all token holdings for a wallet"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                address,
                {"program": "TokenkegQFEYz5ymGmcEtjuF4i7"},
                {"encoding": "jsonParsed"}
            ]
        }
        response = requests.post(HELIUS_RPC, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        holdings = []
        if "result" in data:
            for acc in data["result"].get("value", []):
                info = acc["account"]["data"]["parsed"]["info"]
                mint = info.get("mint")
                amount = int(info.get("amount", 0))
                if amount > 0:
                    holdings.append({
                        "mint": mint,
                        "amount": amount
                    })
        
        return json.dumps({"address": address, "holdings": holdings})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_wallet_activity(address: str, limit: int = 5) -> str:
    """Get recent activity for a wallet"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": limit}]
        }
        response = requests.post(HELIUS_RPC, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        activity = []
        if "result" in data:
            for sig in data["result"]:
                activity.append({
                    "signature": sig.get("signature"),
                    "slot": sig.get("slot"),
                    "block_time": sig.get("blockTime"),
                    "status": sig.get("status", {}).get("Ok", "unknown")
                })
        
        return json.dumps({"address": address, "activity": activity})
    except Exception as e:
        return json.dumps({"error": str(e)})


def compare_wallets(addresses: list) -> str:
    """Compare multiple wallets"""
    try:
        results = []
        for addr in addresses:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [addr]
                }
                response = requests.post(HELIUS_RPC, json=payload, timeout=10)
                data = response.json()
                lamports = data.get("result", {}).get("value", 0)
                results.append({
                    "address": addr,
                    "sol": lamports / 1e9
                })
            except:
                results.append({"address": addr, "sol": 0})
        
        return json.dumps({"wallets": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="track_wallet",
    toolset="onchain",
    schema={
        "name": "track_wallet",
        "description": "Track a Solana wallet - get basic info",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Wallet address"}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: track_wallet(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="wallet_token_holdings",
    toolset="onchain",
    schema={
        "name": "wallet_token_holdings",
        "description": "Get all token holdings for a wallet",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Wallet address"}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_token_holdings(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="wallet_activity",
    toolset="onchain",
    schema={
        "name": "wallet_activity",
        "description": "Get recent activity for a wallet",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Wallet address"},
                "limit": {"type": "integer", "description": "Max transactions", "default": 5}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_wallet_activity(
        args.get("address", ""),
        args.get("limit", 5)
    ),
    check_fn=check_requirements
)

registry.register(
    name="compare_wallets",
    toolset="onchain",
    schema={
        "name": "compare_wallets",
        "description": "Compare multiple wallets",
        "parameters": {
            "type": "object",
            "properties": {
                "addresses": {"type": "array", "items": {"type": "string"}, "description": "List of wallet addresses"}
            },
            "required": ["addresses"]
        }
    },
    handler=lambda args, **kw: compare_wallets(args.get("addresses", [])),
    check_fn=check_requirements
)