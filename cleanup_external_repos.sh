#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Cleaning up external-repos dependencies to free up disk space..."
echo "This will remove node_modules and .venv directories from external-repos/\n"

TOTAL_FREED=0

# Python venv cleanup
echo "=== Removing Python .venv directories ==="
for repo in external-repos/base/web3-ai-trading-agent \
            external-repos/multi-chain/Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine \
            external-repos/security/pump-fun-rug-checker-lite \
            external-repos/security/Rug-Killer-On-Solana \
            external-repos/multi-chain/onchain-agent-kit; do
  if [ -d "$repo/.venv" ]; then
    echo "Removing $repo/.venv"
    SIZE=$(du -sh "$repo/.venv" 2>/dev/null | cut -f1 || echo "?")
    rm -rf "$repo/.venv"
    echo "  Freed: $SIZE"
    TOTAL_FREED=$((TOTAL_FREED + 1))
  fi
done

# Node modules cleanup
echo "\n=== Removing Node node_modules directories ==="
for repo in external-repos/sui/capybot \
            external-repos/sui/HoneyPotDetectionOnSui \
            external-repos/base/defi-trading-mcp \
            external-repos/base/pumpclaw \
            external-repos/security/solana-rugchecker \
            external-repos/base/universal-crypto-mcp; do
  if [ -d "$repo/node_modules" ]; then
    echo "Removing $repo/node_modules"
    SIZE=$(du -sh "$repo/node_modules" 2>/dev/null | cut -f1 || echo "?")
    rm -rf "$repo/node_modules"
    echo "  Freed: $SIZE"
    TOTAL_FREED=$((TOTAL_FREED + 1))
  fi
done

# npm/pnpm cache cleanup (optional, only if needed)
echo "\n=== Optional: Cleaning npm/pnpm cache ==="
if [ -d "$HOME/.npm" ]; then
  echo "Removing ~/.npm cache"
  SIZE=$(du -sh "$HOME/.npm" 2>/dev/null | cut -f1 || echo "?")
  rm -rf "$HOME/.npm"
  echo "  Freed: $SIZE"
fi

if [ -d "$HOME/.pnpm-store" ]; then
  echo "Removing ~/.pnpm-store cache"
  SIZE=$(du -sh "$HOME/.pnpm-store" 2>/dev/null | cut -f1 || echo "?")
  rm -rf "$HOME/.pnpm-store"
  echo "  Freed: $SIZE"
fi

echo "\n✓ Cleanup complete!"
echo "Removed $TOTAL_FREED dependency directories from external-repos/"
echo "\nYou can re-run validate_external_repos.sh if needed to reinstall after freeing more space."
