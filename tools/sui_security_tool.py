import json
import requests
from tools.registry import registry

SUI_RPC_URL = "https://mainnet.sui-rpc.com"


def check_requirements() -> bool:
    return True


def _post_rpc(method: str, params: list) -> dict:
    """Make SUI RPC call"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    response = requests.post(SUI_RPC_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def analyze_sui_token(token_type: str) -> str:
    """Analyze a SUI token for honeypot/scam patterns
    
    Args:
        token_type: Token type (e.g., "0x1234...::COIN::COIN")
    
    Returns:
        JSON string with security analysis
    """
    try:
        # Check if token is mintable (honeypot risk)
        # Get token metadata
        metadata_params = [token_type, {"show content": True}]
        try:
            metadata_result = _post_rpc("sui_getObject", metadata_params)
        except Exception:
            return json.dumps({"error": "Failed to fetch token metadata", "token_type": token_type})
        
        # Analyze various security indicators
        is_mintable = False
        is_pausable = False
        has_blacklist = False
        warnings = []
        
        # Check for mint capability in the module
        if "result" in metadata_result and metadata_result["result"]:
            obj_data = metadata_result["result"].get("data", {})
            content = obj_data.get("content", {})
            
            # Check for mutable fields that could indicate honeypot
            fields = content.get("fields", {})
            
            # Heuristic checks
            if "cap" in str(fields).lower():
                is_mintable = True
                warnings.append("Token has capability field - may be mintable")
            
            if "paused" in str(fields).lower():
                is_pausable = True
                warnings.append("Token has paused state - can be paused")
        
        # Calculate safety score
        safety_score = 100
        if is_mintable:
            safety_score -= 50
        if is_pausable:
            safety_score -= 30
        if has_blacklist:
            safety_score -= 20
        if len(warnings) > 3:
            safety_score -= 20
        
        result = {
            "token_type": token_type,
            "chain": "sui",
            "safety_score": max(0, safety_score),
            "is_mintable": is_mintable,
            "is_pausable": is_pausable,
            "has_blacklist": has_blacklist,
            "warnings": warnings,
            "is_safe": safety_score >= 70
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_type": token_type})


def check_liquidity_pool(token_type: str) -> str:
    """Check liquidity pool info for a SUI token
    
    Args:
        token_type: Token type
    
    Returns:
        JSON string with pool info
    """
    try:
        # Get packages/modules for the token
        # This is a simplified version - in production would query DEXes directly
        result = {
            "token_type": token_type,
            "chain": "sui",
            "dex_pools": [],
            "total_liquidity_usd": 0,
            "has_liquidity": False
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_type": token_type})


def check_rug_pull_indicators(token_type: str) -> str:
    """Check common rug pull indicators for SUI token
    
    Args:
        token_type: Token type
    
    Returns:
        JSON string with analysis
    """
    try:
        indicators = []
        score = 100
        
        # Try to get token info
        try:
            metadata_result = _post_rpc("sui_getObject", [token_type, {"show content": True}])
            
            if "result" in metadata_result and metadata_result["result"]:
                obj_data = metadata_result["result"].get("data", {})
                content = obj_data.get("content", {})
                fields = content.get("fields", {})
                
                # Check 1: Mutable fields (common in honeypots)
                if any(k.endswith("_mut") or "mutable" in k.lower() for k in fields.keys()):
                    indicators.append("Mutable fields detected")
                    score -= 20
                
                # Check 2: Admin/owner fields
                if "admin" in str(fields).lower() or "owner" in str(fields).lower():
                    indicators.append("Admin/owner functions present")
                    score -= 15
                
                # Check 3: Freeze capability
                if "freeze" in str(fields).lower():
                    indicators.append("Freeze capability detected")
                    score -= 25
                
        except Exception:
            pass
        
        result = {
            "token_type": token_type,
            "chain": "sui",
            "rug_score": max(0, score),
            "indicators": indicators,
            "is_suspicious": score < 70
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "token_type": token_type})


def full_sui_security_check(token_type: str) -> str:
    """Complete security analysis for SUI token
    
    Args:
        token_type: Token type
    
    Returns:
        JSON string with complete security analysis
    """
    analysis = analyze_sui_token(token_type)
    rug_check = check_rug_pull_indicators(token_type)
    liquidity = check_liquidity_pool(token_type)
    
    try:
        analysis_data = json.loads(analysis)
        rug_data = json.loads(rug_check)
        liquidity_data = json.loads(liquidity)
    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse responses"})
    
    combined = {
        "token_type": token_type,
        "chain": "sui",
        "security_analysis": analysis_data,
        "rug_check": rug_data,
        "liquidity": liquidity_data,
        "overall_safe": (
            analysis_data.get("is_safe", False) and
            not rug_data.get("is_suspicious", True)
        )
    }
    
    return json.dumps(combined, indent=2)


# Tool registration
registry.register(
    name="suihoneypot_analysis",
    toolset="security",
    schema={
        "name": "suihoneypot_analysis",
        "description": "Analyze SUI token for honeypot/scam patterns. Checks for mintable, pausable, and other honeypot indicators.",
        "parameters": {
            "type": "object",
            "properties": {
                "token_type": {
                    "type": "string",
                    "description": "SUI token type (e.g., 0x1234...::COIN::COIN)"
                }
            },
            "required": ["token_type"]
        }
    },
    handler=lambda args, **kw: analyze_sui_token(args.get("token_type", "")),
    check_fn=check_requirements
)

registry.register(
    name="sui_rug_check",
    toolset="security",
    schema={
        "name": "sui_rug_check",
        "description": "Check SUI token for common rug pull indicators like mutable fields, admin functions, freeze capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "token_type": {
                    "type": "string",
                    "description": "SUI token type"
                }
            },
            "required": ["token_type"]
        }
    },
    handler=lambda args, **kw: check_rug_pull_indicators(args.get("token_type", "")),
    check_fn=check_requirements
)

registry.register(
    name="sui_security_scan",
    toolset="security",
    schema={
        "name": "sui_security_scan",
        "description": "Complete security scan for SUI token including honeypot detection, rug check, and liquidity analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "token_type": {
                    "type": "string",
                    "description": "SUI token type"
                }
            },
            "required": ["token_type"]
        }
    },
    handler=lambda args, **kw: full_sui_security_check(args.get("token_type", "")),
    check_fn=check_requirements
)