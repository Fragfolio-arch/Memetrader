import json
import os
import requests
from tools.registry import registry

DEXRANGER_API_URL = "https://api.dexranger.io/v2"


def _get_requests():
    try:
        import requests
        return requests
    except ImportError:
        return None


def check_requirements() -> bool:
    requests = _get_requests()
    if requests is None:
        return False
    return True


def _fetch_json(url: str, params: dict | None = None, timeout: int = 10):
    requests = _get_requests()
    if requests is None:
        raise RuntimeError("requests library is not installed")

    headers = {"Accept": "application/json"}
    if os.getenv("DEXRANGER_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('DEXRANGER_API_KEY')}"

    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def analyze_token(token_address: str, chain: str = "solana") -> str:
    """Analyze a token for safety issues (honeypot, scam, etc.)
    
    Args:
        token_address: Token mint address to analyze
        chain: Blockchain - "solana", "ethereum", "bsc", "ton"
    
    Returns:
        JSON string with safety analysis
    """
    try:
        data = _fetch_json(
            f"{DEXRANGER_API_URL}/token/security",
            params={
                "address": token_address,
                "chain": chain
            }
        )
        
        # Parse safety score and warnings
        safety_score = data.get("score", 0)
        is_honeypot = data.get("is_honeypot", False)
        is_mintable = data.get("is_mintable", False)
        is_pausable = data.get("is_pausable", False)
        warnings = data.get("warnings", [])
        
        result = {
            "token_address": token_address,
            "chain": chain,
            "safety_score": safety_score,
            "is_honeypot": is_honeypot,
            "is_mintable": is_mintable,
            "is_pausable": is_pausable,
            "warnings": warnings,
            "is_safe": safety_score >= 70 and not is_honeypot
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_address": token_address})


def check_liquidity(token_address: str, chain: str = "solana") -> str:
    """Check token liquidity on DEXes
    
    Args:
        token_address: Token mint address
        chain: Blockchain
    
    Returns:
        JSON string with liquidity info
    """
    try:
        data = _fetch_json(
            f"{DEXRANGER_API_URL}/token/liquidity",
            params={
                "address": token_address,
                "chain": chain
            }
        )
        
        liquidity_usd = data.get("liquidity_usd", 0)
        pool_count = data.get("pool_count", 0)
        
        result = {
            "token_address": token_address,
            "chain": chain,
            "liquidity_usd": liquidity_usd,
            "pool_count": pool_count,
            "has_liquidity": liquidity_usd > 1000
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_address": token_address})


def check_holder_distribution(token_address: str, chain: str = "solana") -> str:
    """Check holder distribution for top holders concentration
    
    Args:
        token_address: Token mint address
        chain: Blockchain
    
    Returns:
        JSON string with holder info
    """
    try:
        data = _fetch_json(
            f"{DEXRANGER_API_URL}/token/holders",
            params={
                "address": token_address,
                "chain": chain
            }
        )
        
        top_10_percent = data.get("top_10_percent_held", 0)
        holder_count = data.get("holder_count", 0)
        
        result = {
            "token_address": token_address,
            "chain": chain,
            "holder_count": holder_count,
            "top_10_percent_held": top_10_percent,
            "is_concentrated": top_10_percent > 50
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_address": token_address})


def full_security_scan(token_address: str, chain: str = "solana") -> str:
    """Perform full security scan combining all checks
    
    Args:
        token_address: Token mint address
        chain: Blockchain
    
    Returns:
        JSON string with complete security analysis
    """
    security = analyze_token(token_address, chain)
    liquidity = check_liquidity(token_address, chain)
    holders = check_holder_distribution(token_address, chain)
    
    try:
        security_data = json.loads(security)
        liquidity_data = json.loads(liquidity)
        holders_data = json.loads(holders)
    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse responses"})
    
    # Combine results
    combined = {
        "token_address": token_address,
        "chain": chain,
        "security": security_data,
        "liquidity": liquidity_data,
        "holders": holders_data,
        "overall_safe": (
            security_data.get("is_safe", False) and
            liquidity_data.get("has_liquidity", False) and
            not holders_data.get("is_concentrated", True)
        )
    }
    
    return json.dumps(combined, indent=2)


# Tool registration
registry.register(
    name="dexranger_security",
    toolset="security",
    schema={
        "name": "dexranger_security",
        "description": "Analyze token security using DEX Ranger API. Checks for honeypots, scam patterns, liquidity, and holder distribution on Solana, Ethereum, BSC, or TON.",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {
                    "type": "string",
                    "description": "Token mint address to analyze"
                },
                "chain": {
                    "type": "string",
                    "description": "Blockchain: solana, ethereum, bsc, ton",
                    "default": "solana"
                }
            },
            "required": ["token_address"]
        }
    },
    handler=lambda args, **kw: analyze_token(
        args.get("token_address", ""),
        args.get("chain", "solana")
    ),
    check_fn=check_requirements
)

registry.register(
    name="dexranger_liquidity",
    toolset="security",
    schema={
        "name": "dexranger_liquidity",
        "description": "Check token liquidity on DEXes",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {
                    "type": "string",
                    "description": "Token mint address"
                },
                "chain": {
                    "type": "string",
                    "description": "Blockchain: solana, ethereum, bsc, ton",
                    "default": "solana"
                }
            },
            "required": ["token_address"]
        }
    },
    handler=lambda args, **kw: check_liquidity(
        args.get("token_address", ""),
        args.get("chain", "solana")
    ),
    check_fn=check_requirements
)

registry.register(
    name="dexranger_holders",
    toolset="security",
    schema={
        "name": "dexranger_holders",
        "description": "Check token holder distribution for concentration",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {
                    "type": "string",
                    "description": "Token mint address"
                },
                "chain": {
                    "type": "string",
                    "description": "Blockchain: solana, ethereum, bsc, ton",
                    "default": "solana"
                }
            },
            "required": ["token_address"]
        }
    },
    handler=lambda args, **kw: check_holder_distribution(
        args.get("token_address", ""),
        args.get("chain", "solana")
    ),
    check_fn=check_requirements
)

registry.register(
    name="dexranger_full_scan",
    toolset="security",
    schema={
        "name": "dexranger_full_scan",
        "description": "Perform complete token security scan including safety, liquidity, and holder analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "token_address": {
                    "type": "string",
                    "description": "Token mint address to scan"
                },
                "chain": {
                    "type": "string",
                    "description": "Blockchain: solana, ethereum, bsc, ton",
                    "default": "solana"
                }
            },
            "required": ["token_address"]
        }
    },
    handler=lambda args, **kw: full_security_scan(
        args.get("token_address", ""),
        args.get("chain", "solana")
    ),
    check_fn=check_requirements
)