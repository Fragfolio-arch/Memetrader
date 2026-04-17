import json
import requests
from tools.registry import registry

SUI_RPC_URL = "https://rpc.mainnet.sui.io"


def check_requirements() -> bool:
    """Check if SUI RPC is accessible"""
    try:
        response = requests.post(SUI_RPC_URL, 
            json={"jsonrpc": "2.0", "id": 1, "method": "sui_getTotalSupply", "params": ["0x2::sui::SUI"]},
            timeout=5)
        return response.status_code == 200
    except:
        return False


def get_balance(address: str) -> str:
    """Get SUI balance for an address"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sui_getBalance",
            "params": [address, "0x2::sui::SUI"]
        }
        response = requests.post(SUI_RPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            result = data["result"]
            return json.dumps({
                "address": address,
                "balance": result.get("balance", 0),
                "object_id": result.get("objectId")
            })
        return json.dumps({"error": "No result"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_objects(address: str) -> str:
    """Get all objects owned by an address"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sui_getObjectsOwnedByAddress",
            "params": [address]
        }
        response = requests.post(SUI_RPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        objects = []
        if "result" in data:
            for obj in data["result"]:
                objects.append({
                    "object_id": obj.get("objectId"),
                    "type": obj.get("type"),
                    "version": obj.get("version")
                })
        
        return json.dumps({"address": address, "objects": objects})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_balance(address: str, token_type: str) -> str:
    """Get balance for a specific token"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sui_getBalance",
            "params": [address, token_type]
        }
        response = requests.post(SUI_RPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            result = data["result"]
            return json.dumps({
                "address": address,
                "token_type": token_type,
                "balance": result.get("balance", 0)
            })
        return json.dumps({"error": "No result"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_transactions(address: str, limit: int = 10) -> str:
    """Get transaction history for an address"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sui_getTransactions",
            "params": {
                "Address": address,
                "limit": min(limit, 50)
            }
        }
        response = requests.post(SUI_RPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        txs = []
        if "result" in data:
            for tx in data["result"].get("data", []):
                txs.append({
                    "digest": tx.get("digest"),
                    "timestamp": tx.get("timestamp"),
                    "tx_module": tx.get("transaction", {}).get("data", {}).get("transaction", {}).get("kind", {}).get("Call", {}).get("module", "")
                })
        
        return json.dumps({"address": address, "transactions": txs})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_price(token_address: str) -> str:
    """Get token price from Cetus (returns mock for now)"""
    try:
        return json.dumps({
            "token": token_address,
            "price": "N/A",
            "note": "Use cetus_price tool for token prices"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="sui_get_balance",
    toolset="onchain",
    schema={
        "name": "sui_get_balance",
        "description": "Get SUI balance for an address",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "SUI address"}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_balance(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="sui_get_objects",
    toolset="onchain",
    schema={
        "name": "sui_get_objects",
        "description": "Get all objects owned by SUI address",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "SUI address"}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_objects(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="sui_get_token_balance",
    toolset="onchain",
    schema={
        "name": "sui_get_token_balance",
        "description": "Get balance for a specific SUI token",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "SUI address"},
                "token_type": {"type": "string", "description": "Token type address"}
            },
            "required": ["address", "token_type"]
        }
    },
    handler=lambda args, **kw: get_token_balance(
        args.get("address", ""),
        args.get("token_type", "")
    ),
    check_fn=check_requirements
)

registry.register(
    name="sui_get_transactions",
    toolset="onchain",
    schema={
        "name": "sui_get_transactions",
        "description": "Get transaction history for SUI address",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "SUI address"},
                "limit": {"type": "integer", "description": "Max transactions", "default": 10}
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_transactions(
        args.get("address", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)