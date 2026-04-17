import json
import requests
from tools.registry import registry

BIRDEYE_BASE_URL = "https://public-api.birdeye.so"


def check_requirements() -> bool:
    """Check if Birdeye API is accessible"""
    try:
        response = requests.get(f"{BIRDEYE_BASE_URL}/defi/token_list?chain=solana", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_token_info(address: str) -> str:
    """Get token information"""
    try:
        url = f"{BIRDEYE_BASE_URL}/defi/token_overview"
        params = {"address": address}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            token_data = data.get("data", {})
            return json.dumps({
                "address": address,
                "name": token_data.get("name"),
                "symbol": token_data.get("symbol"),
                "decimals": token_data.get("decimals"),
                "price": token_data.get("price"),
                "price_change_24h": token_data.get("priceChange24hPercent"),
                "volume_24h": token_data.get("volume24hUSD"),
                "liquidity": token_data.get("liquidity"),
                "market_cap": token_data.get("mc"),
                "supply": token_data.get("supply")
            })
        else:
            return json.dumps({"error": "Token not found or API error"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_trending_tokens(chain: str = "solana") -> str:
    """Get trending tokens"""
    try:
        url = f"{BIRDEYE_BASE_URL}/defi/token_list"
        params = {"chain": chain}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            tokens = data.get("data", {}).get("tokens", [])
            trending = []
            for token in tokens[:20]:
                trending.append({
                    "address": token.get("address"),
                    "name": token.get("name"),
                    "symbol": token.get("symbol"),
                    "price": token.get("price"),
                    "volume_24h": token.get("volume24hUSD"),
                    "liquidity": token.get("liquidity")
                })
            return json.dumps({"trending_tokens": trending})
        else:
            return json.dumps({"error": "Failed to fetch trending tokens"})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="birdeye_token_info",
    toolset="data",
    schema={
        "name": "birdeye_token_info",
        "description": "Get detailed token information from Birdeye (Solana focus)",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Token contract address"
                }
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_token_info(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="birdeye_trending",
    toolset="data",
    schema={
        "name": "birdeye_trending",
        "description": "Get trending tokens from Birdeye",
        "parameters": {
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "Blockchain (default: solana)",
                    "default": "solana"
                }
            }
        }
    },
    handler=lambda args, **kw: get_trending_tokens(args.get("chain", "solana")),
    check_fn=check_requirements
)