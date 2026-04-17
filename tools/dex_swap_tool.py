import json
import os
import requests
from tools.registry import registry

JUPITER_API_URL = "https://api.jup.ag/swap/v1"
SOLANA_RPC = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")


def check_requirements() -> bool:
    """Check if Solana devnet is accessible"""
    try:
        response = requests.get(SOLANA_RPC, 
            json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
            timeout=5)
        return response.status_code == 200
    except:
        return False


def get_swap_quote(input_mint: str, output_mint: str, amount: int, slippage: float = 0.5) -> str:
    """Get swap quote from Jupiter aggregator"""
    try:
        url = f"{JUPITER_API_URL}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": int(slippage * 100)
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "input_mint": input_mint,
            "output_mint": output_mint,
            "input_amount": amount,
            "output_amount": data.get("outAmount"),
            "price_impact": data.get("priceImpactPct"),
            "route": data.get("routePlan", [])
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_list(chain: str = "solana") -> str:
    """Get available tokens for swap"""
    try:
        url = f"{JUPITER_API_URL}/tokens"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        tokens = []
        for token in data.get("tokens", [])[:50]:
            tokens.append({
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "name": token.get("name"),
                "decimals": token.get("decimals"),
                "liquidity": token.get("liquidity")
            })
        
        return json.dumps({"tokens": tokens})
    except Exception as e:
        return json.dumps({"error": str(e)})


def execute_swap() -> str:
    """Execute a swap (stub - not implemented)"""
    return json.dumps({"error": "Swap execution not implemented - use get_swap_quote for quotes"})


registry.register(
    name="dex_swap_quote",
    toolset="dex",
    schema={
        "name": "dex_swap_quote",
        "description": "Get a swap quote from Jupiter DEX aggregator for Solana",
        "parameters": {
            "type": "object",
            "properties": {
                "input_mint": {
                    "type": "string",
                    "description": "Input token mint address (e.g., So11111111111111111111111111111111111111112 for SOL)"
                },
                "output_mint": {
                    "type": "string",
                    "description": "Output token mint address"
                },
                "amount": {
                    "type": "integer",
                    "description": "Amount in lamports (smallest unit)"
                },
                "slippage": {
                    "type": "number",
                    "description": "Maximum slippage tolerance (0.5 = 0.5%)",
                    "default": 0.5
                }
            },
            "required": ["input_mint", "output_mint", "amount"]
        }
    },
    handler=lambda args, **kw: get_swap_quote(
        args.get("input_mint", ""),
        args.get("output_mint", ""),
        args.get("amount", 0),
        args.get("slippage", 0.5)
    ),
    check_fn=check_requirements
)

registry.register(
    name="dex_token_list",
    toolset="dex",
    schema={
        "name": "dex_token_list",
        "description": "Get list of available tokens for swap on Solana DEX",
        "parameters": {
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "Blockchain chain (default: solana)",
                    "default": "solana"
                }
            }
        }
    },
    handler=lambda args, **kw: get_token_list(args.get("chain", "solana")),
    check_fn=check_requirements
)

registry.register(
    name="dex_execute_swap",
    toolset="dex",
    schema={
        "name": "dex_execute_swap",
        "description": "Execute a token swap on Solana DEX (not implemented)",
        "parameters": {
            "type": "object",
            "properties": {
                "quote_response": {
                    "type": "string",
                    "description": "Quote response from dex_swap_quote"
                }
            },
            "required": ["quote_response"]
        }
    },
    handler=lambda args, **kw: execute_swap(),
    check_fn=check_requirements
)