#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "⚠️  WARNING: This will COMPLETELY remove external-repos/ directory"
echo "This frees up significant disk space but removes all 2nd script dependencies."
echo ""
echo "Repos that will be DELETED:"
echo "  - twikit (Twitter API)"
echo "  - capybot (Sui arbitrage)"
echo "  - HoneyPotDetectionOnSui"
echo "  - web3-ai-trading-agent"
echo "  - Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine"
echo "  - pump-fun-rug-checker-lite"
echo "  - Rug-Killer-On-Solana"
echo "  - solana-rugchecker"
echo "  - defi-trading-mcp"
echo "  - pumpclaw"
echo "  - universal-crypto-mcp"
echo "  - onchain-agent-kit"
echo ""
echo "⚠️  These repos can be re-cloned later if needed."
echo ""

read -p "Are you sure? Type 'yes' to confirm deletion: " confirmation

if [ "$confirmation" != "yes" ]; then
  echo "Cancelled - external-repos/ NOT deleted"
  exit 0
fi

if [ -d "external-repos" ]; then
  echo "Removing entire external-repos/ directory..."
  SIZE=$(du -sh external-repos 2>/dev/null | cut -f1 || echo "unknown")
  rm -rf external-repos
  echo "✓ Deleted! Freed approximately: $SIZE"
else
  echo "external-repos/ does not exist"
fi

echo ""
echo "✓ Complete! Disk space should be freed."
echo ""
echo "Repos KEPT (from 1st script):"
echo "  ✓ mcp-wrappers/solana/solana-agent-kit"
echo "  ✓ mcp-wrappers/solana/dexranger-skill"
echo "  ✓ mcp-wrappers/sui/sui-agent-kit"
echo "  ✓ mcp-wrappers/sui/sui-trader-mcp"
echo "  ✓ mcp-wrappers/social/twitter-alpha-sentiment-tracker-v2"
echo ""
echo "To re-clone 2nd script repos later, run:"
echo "  bash clone_repos.sh"
