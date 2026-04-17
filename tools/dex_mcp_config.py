"""
DEX MCP Configuration Helper

This module provides configuration templates for connecting to DEX MCP servers.
These servers can be added to ~/.hermes/config.yaml under mcp_servers.

Supported DEX MCP Servers:
1. solana-agent-kit - 60+ Solana actions (Jupiter, Raydium, Pump.fun)
2. sui-trader-mcp - MCP for Cetus swaps
3. universal-crypto-mcp - 380+ tools across 20+ chains
"""

import json
from typing import Dict, Any, Optional


def get_dex_mcp_config(
    server_name: str = "dex",
    use_http: bool = False,
    custom_url: Optional[str] = None
) -> Dict[str, Any]:
    """Get MCP configuration for DEX servers
    
    Args:
        server_name: Name for the MCP server in config
        use_http: Use HTTP transport instead of stdio
        custom_url: Custom MCP server URL (for HTTP mode)
    
    Returns:
        Dict configuration for mcp_servers in config.yaml
    """
    
    configs = {
        "solana_agent_kit": {
            "description": "Solana Agent Kit - 60+ Solana actions",
            "command": "npx",
            "args": ["-y", "@sendaifun/solana-agent-kit"],
            "env": {
                "SOLANA_RPC_URL": "https://api.devnet.solana.com",
                "OPENAI_API_KEY": "${OPENAI_API_KEY}"
            },
            "timeout": 120,
            "connect_timeout": 60
        },
        "sui_trader_mcp": {
            "description": "SUI Trader MCP - Cetus swaps",
            "command": "npx", 
            "args": ["-y", "@kukapay/sui-trader-mcp"],
            "env": {
                "SUI_RPC_URL": "https://rpc.testnet.sui.io"
            },
            "timeout": 120,
            "connect_timeout": 60
        },
        "universal_crypto": {
            "description": "Universal Crypto MCP - 380+ tools across 20+ chains",
            "command": "npx",
            "args": ["-y", "@nirholas/universal-crypto-mcp"],
            "timeout": 120,
            "connect_timeout": 60
        }
    }
    
    if server_name not in configs:
        raise ValueError(f"Unknown server: {server_name}. Choose from: {list(configs.keys())}")
    
    config = configs[server_name]
    
    if use_http and custom_url:
        config = {
            "url": custom_url,
            "timeout": config.get("timeout", 120),
            "connect_timeout": config.get("connect_timeout", 60)
        }
    elif use_http:
        raise ValueError("custom_url required when use_http=True")
    
    return config


def get_config_yaml_template() -> str:
    """Get YAML template for DEX MCP configuration"""
    
    template = '''# Add to ~/.hermes/config.yaml under mcp_servers:

mcp_servers:
  # Solana Agent Kit - 60+ Solana actions (Jupiter, Raydium, Pump.fun)
  solana:
    command: npx
    args:
      - -y
      - @sendaifun/solana-agent-kit
    env:
      SOLANA_RPC_URL: https://api.devnet.solana.com
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    timeout: 120
    connect_timeout: 60
  
  # SUI Trader MCP - Cetus swaps on SUI
  sui:
    command: npx
    args:
      - -y
      - @kukapay/sui-trader-mcp
    env:
      SUI_RPC_URL: https://rpc.testnet.sui.io
    timeout: 120
    connect_timeout: 60
  
  # Universal Crypto MCP - Multi-chain tools
  crypto:
    command: npx
    args:
      - -y
      - @nirholas/universal-crypto-mcp
    timeout: 120
    connect_timeout: 60
'''
    return template


if __name__ == "__main__":
    print(get_config_yaml_template())