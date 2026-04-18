#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Removing universal-crypto-mcp repository..."

if [ -d "external-repos/base/universal-crypto-mcp" ]; then
  SIZE=$(du -sh "external-repos/base/universal-crypto-mcp" 2>/dev/null | cut -f1 || echo "unknown")
  echo "Size: $SIZE"
  rm -rf "external-repos/base/universal-crypto-mcp"
  echo "✓ Deleted external-repos/base/universal-crypto-mcp"
  echo "✓ Freed approximately: $SIZE"
else
  echo "external-repos/base/universal-crypto-mcp does not exist"
fi

echo ""
echo "Note: universal-crypto-mcp can be installed via npm package when needed:"
echo "  npm install universal-crypto-mcp"
