"""
DEX MCP Configuration Helper

This module provides configuration templates for connecting to DEX MCP servers.
These servers can be added to ~/.hermes/config.yaml under mcp_servers.

Supported DEX MCP Servers (TESTED):
1. soliris-mcp - Solana MCP with rug-pull detection, copy trading, Jupiter swaps
2. fr3k-behemoth - Cosmic crypto trading MCP (multiple exchanges)
3. solana-mcp-server - Basic Solana wallet/tx handling

Previously tested but NOT AVAILABLE:
- @kukapay/sui-trader-mcp - package not found
- @edkdev/defi-trading-mcp - package not found
- @nirholas/universal-crypto-mcp - package not found
- @chainstacklabs/web3-ai-trading-agent - package not found
- solana-agent-kit - wrong package name, doesn't exist
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
        "soliris": {
            "description": "Soliris MCP - Solana with rug-pull detection, copy trading, Jupiter swaps",
            "command": "npx",
            "args": ["-y", "soliris-mcp"],
            "env": {
                "SOLANA_RPC_URL": "https://api.devnet.solana.com"
            },
            "timeout": 120,
            "connect_timeout": 60
        },
        "behemoth": {
            "description": "BEHEMOTH Cosmic Crypto Trading MCP - Multiple exchange support",
            "command": "npx",
            "args": ["-y", "fr3k-behemoth"],
            "timeout": 120,
            "connect_timeout": 60
        },
        "solana_mcp_server": {
            "description": "Basic Solana MCP Server - wallet management, transactions",
            "command": "npx",
            "args": ["-y", "solana-mcp-server"],
            "env": {
                "SOLANA_RPC_URL": "https://api.devnet.solana.com"
            },
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
  # Soliris MCP - Solana with rug-pull detection, copy trading, Jupiter swaps
  soliris:
    command: npx
    args:
      - -y
      - soliris-mcp
    env:
      SOLANA_RPC_URL: https://api.devnet.solana.com
    timeout: 120
    connect_timeout: 60
   
  # BEHEMOTH Cosmic Crypto Trading MCP - Multiple exchange support
  behemoth:
    command: npx
    args:
      - -y
      - fr3k-behemoth
    timeout: 120
    connect_timeout: 60

  # Basic Solana MCP Server - wallet management, transactions
  solana:
    command: npx
    args:
      - -y
      - solana-mcp-server
    env:
      SOLANA_RPC_URL: https://api.devnet.solana.com
    timeout: 120
    connect_timeout: 60
'''
    return template


if __name__ == "__main__":
    print(get_config_yaml_template())