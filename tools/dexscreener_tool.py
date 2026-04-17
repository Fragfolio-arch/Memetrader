import json
import requests
from tools.registry import registry

DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest"


def check_requirements() -> bool:
    """Check if DexScreener API is accessible"""
    try:
        response = requests.get(f"{DEXSCREENER_BASE_URL}/dex/search?q=ethereum", timeout=5)
        return response.status_code == 200
    except:
        return False


def search_pairs(query: str) -> str:
    """Search for trading pairs"""
    try:
        url = f"{DEXSCREENER_BASE_URL}/dex/search"
        params = {"q": query}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        pairs = []
        for pair in data.get("pairs", [])[:10]:
            pairs.append({
                "pair_address": pair.get("pairAddress"),
                "base_token": {
                    "address": pair.get("baseToken", {}).get("address"),
                    "name": pair.get("baseToken", {}).get("name"),
                    "symbol": pair.get("baseToken", {}).get("symbol")
                },
                "quote_token": {
                    "address": pair.get("quoteToken", {}).get("address"),
                    "name": pair.get("quoteToken", {}).get("name"),
                    "symbol": pair.get("quoteToken", {}).get("symbol")
                },
                "price_usd": pair.get("priceUsd"),
                "volume_24h": pair.get("volume", {}).get("h24"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "dex_id": pair.get("dexId"),
                "chain_id": pair.get("chainId")
            })

        return json.dumps({"pairs": pairs})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_pair_info(pair_address: str) -> str:
    """Get detailed pair information"""
    try:
        url = f"{DEXSCREENER_BASE_URL}/dex/pairs/{pair_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "pairs" in data and data["pairs"]:
            pair = data["pairs"][0]
            return json.dumps({
                "pair_address": pair.get("pairAddress"),
                "base_token": pair.get("baseToken"),
                "quote_token": pair.get("quoteToken"),
                "price_usd": pair.get("priceUsd"),
                "price_change_24h": pair.get("priceChange", {}).get("h24"),
                "volume_24h": pair.get("volume", {}).get("h24"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "fdv": pair.get("fdv"),
                "market_cap": pair.get("marketCap"),
                "dex_id": pair.get("dexId"),
                "chain_id": pair.get("chainId")
            })
        else:
            return json.dumps({"error": "Pair not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="dexscreener_search",
    toolset="data",
    schema={
        "name": "dexscreener_search",
        "description": "Search for trading pairs on DexScreener",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (token name, symbol, or contract address)"
                }
            },
            "required": ["query"]
        }
    },
    handler=lambda args, **kw: search_pairs(args.get("query", "")),
    check_fn=check_requirements
)

registry.register(
    name="dexscreener_pair_info",
    toolset="data",
    schema={
        "name": "dexscreener_pair_info",
        "description": "Get detailed information for a specific trading pair",
        "parameters": {
            "type": "object",
            "properties": {
                "pair_address": {
                    "type": "string",
                    "description": "Pair contract address"
                }
            },
            "required": ["pair_address"]
        }
    },
    handler=lambda args, **kw: get_pair_info(args.get("pair_address", "")),
    check_fn=check_requirements
)