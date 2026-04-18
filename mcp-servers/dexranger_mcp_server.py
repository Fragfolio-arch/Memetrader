#!/usr/bin/env python3
"""
MCP Server for DEX Ranger Token Safety Checker
Wraps the dexranger-skill python script as an MCP tool.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Sequence

from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent, PromptMessage
import mcp.server.stdio

# Path to the dex ranger script
DEXRANGER_SCRIPT = "/workspaces/Memetrader/mcp-wrappers/solana/dexranger-skill/scripts/dexranger_check.py"

server = Server("dexranger-mcp")

@server.tool()
async def check_token_safety(chain: str, token_address: str) -> str:
    """
    Check token safety using DEX Ranger.
    
    Args:
        chain: Blockchain (ETH, SOL, BSC, TON)
        token_address: Token contract/mint address
        
    Returns:
        JSON with token safety analysis
    """
    try:
        # Run the dex ranger script
        result = subprocess.run(
            [sys.executable, DEXRANGER_SCRIPT, chain.upper(), token_address, "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return json.dumps({
                "error": "Script failed",
                "stderr": result.stderr,
                "stdout": result.stdout
            })
            
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Request timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())