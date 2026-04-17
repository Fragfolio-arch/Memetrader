import json
import requests
from tools.registry import registry

CETUS_API_URL = "https://api.cetus.ac"


def check_requirements() -> bool:
    """Check if Cetus API is accessible"""
    try:
        response = requests.get(f"{CETUS_API_URL}/info", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_token_price(token_address: str) -> str:
    """Get token price from Cetus"""
    try:
        url = f"{CETUS_API_URL}/token/price"
        params = {"address": token_address}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "token": token_address,
            "price": data.get("price"),
            "change_24h": data.get("priceChange24h"),
            "volume_24h": data.get("volume24h")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_pool_info(pool_address: str) -> str:
    """Get pool information"""
    try:
        url = f"{CETUS_API_URL}/pool/info"
        params = {"address": pool_address}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "pool": pool_address,
            "token_a": data.get("coinA"),
            "token_b": data.get("coinB"),
            "liquidity": data.get("liquidity"),
            ".volume_24h": data.get("volume24h")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_swap_quote(input_token: str, output_token: str, amount: int) -> str:
    """Get swap quote from Cetus"""
    try:
        url = f"{CETUS_API_URL}/swap/quote"
        params = {
            "fromCoin": input_token,
            "toCoin": output_token,
            "amount": amount
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "input_token": input_token,
            "output_token": output_token,
            "input_amount": amount,
            "output_amount": data.get("outAmount"),
            "price_impact": data.get("priceImpact")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_list(chain: str = "sui") -> str:
    """Get list of tokens on SUI/cetus"""
    try:
        url = f"{CETUS_API_URL}/tokens"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        tokens = []
        for token in data.get("tokens", [])[:50]:
            tokens.append({
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "name": token.get("name"),
                "decimals": token.get("decimals")
            })
        
        return json.dumps({"tokens": tokens})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="cetus_price",
    toolset="dex",
    schema={
        "name": "cetus_price",
        "description": "Get token price from Cetus DEX (SUI)",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address"}
            },
            "required": ["token_address"]
        }
    },
    handler=lambda args, **kw: get_token_price(args.get("token_address", "")),
    check_fn=check_requirements
)

registry.register(
    name="cetus_pool",
    toolset="dex",
    schema={
        "name": "cetus_pool",
        "description": "Get pool information from Cetus",
        "parameters": {
            "type": "object",
            "properties": {
                "pool_address": {"type": "string", "description": "Pool contract address"}
            },
            "required": ["pool_address"]
        }
    },
    handler=lambda args, **kw: get_pool_info(args.get("pool_address", "")),
    check_fn=check_requirements
)

registry.register(
    name="cetus_swap_quote",
    toolset="dex",
    schema={
        "name": "cetus_swap_quote",
        "description": "Get swap quote from Cetus DEX",
        "parameters": {
            "type": "object",
            "properties": {
                "input_token": {"type": "string", "description": "Input token address"},
                "output_token": {"type": "string", "description": "Output token address"},
                "amount": {"type": "integer", "description": "Amount in smallest units"}
            },
            "required": ["input_token", "output_token", "amount"]
        }
    },
    handler=lambda args, **kw: get_swap_quote(
        args.get("input_token", ""),
        args.get("output_token", ""),
        args.get("amount", 0)
    ),
    check_fn=check_requirements
)

registry.register(
    name="cetus_tokens",
    toolset="dex",
    schema={
        "name": "cetus_tokens",
        "description": "Get token list from Cetus",
        "parameters": {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "description": "Chain (default: sui)", "default": "sui"}
            }
        }
    },
    handler=lambda args, **kw: get_token_list(args.get("chain", "sui")),
    check_fn=check_requirements
)