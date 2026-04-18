#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Installing remaining external repo dependencies..."

echo "\n=== Python Repos ==="

if [ -d "external-repos/base/web3-ai-trading-agent" ]; then
  echo "\n[1] web3-ai-trading-agent"
  cd external-repos/base/web3-ai-trading-agent
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "web3\|requests" 2>/dev/null; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/multi-chain/Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine" ]; then
  echo "\n[2] Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine"
  cd external-repos/multi-chain/Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "web3\|requests" 2>/dev/null; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/security/pump-fun-rug-checker-lite" ]; then
  echo "\n[3] pump-fun-rug-checker-lite"
  cd external-repos/security/pump-fun-rug-checker-lite
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "solana\|requests" 2>/dev/null; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/security/Rug-Killer-On-Solana" ]; then
  echo "\n[4] Rug-Killer-On-Solana"
  cd external-repos/security/Rug-Killer-On-Solana
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "solana\|requests" 2>/dev/null; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

echo "\n=== Node / TypeScript Repos ==="

if [ -d "external-repos/sui/capybot" ]; then
  echo "\n[5] capybot (Sui)"
  cd external-repos/sui/capybot
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping capybot"
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/sui/HoneyPotDetectionOnSui" ]; then
  echo "\n[6] HoneyPotDetectionOnSui"
  cd external-repos/sui/HoneyPotDetectionOnSui
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping HoneyPotDetectionOnSui"
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/base/defi-trading-mcp" ]; then
  echo "\n[7] defi-trading-mcp (MCP server)"
  cd external-repos/base/defi-trading-mcp
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping defi-trading-mcp"
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/base/pumpclaw" ]; then
  echo "\n[8] pumpclaw (multi-component)"
  cd external-repos/base/pumpclaw
  if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping pumpclaw"
    fi
  elif [ -f "package.json" ]; then
    echo "  Dependencies already installed, skipping"
  else
    echo "  ℹ pumpclaw has no root package.json (multi-component repo)"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/security/solana-rugchecker" ]; then
  echo "\n[9] solana-rugchecker"
  cd external-repos/security/solana-rugchecker
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping solana-rugchecker"
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/base/universal-crypto-mcp" ]; then
  echo "\n[10] universal-crypto-mcp (large monorepo)"
  cd external-repos/base/universal-crypto-mcp
  if [ ! -d "node_modules" ] && [ ! -d "pnpm_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  ⚠ npm not found, skipping universal-crypto-mcp"
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

echo "\n=== Special Repos ==="

if [ -d "external-repos/multi-chain/onchain-agent-kit" ]; then
  echo "\n[11] onchain-agent-kit"
  cd external-repos/multi-chain/onchain-agent-kit
  if [ -f "package.json" ] || [ -f "requirements.txt" ]; then
    if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
      if command -v npm >/dev/null 2>&1; then
        npm install
      else
        echo "  ⚠ npm not found, skipping Node install"
      fi
    elif [ -f "package.json" ] && [ -d "node_modules" ]; then
      echo "  Dependencies already installed, skipping"
    elif [ -f "requirements.txt" ] && [ ! -d ".venv/lib" ]; then
      python3 -m venv .venv || true
      . .venv/bin/activate
      if ! python3 -m pip freeze | grep -q "solana\|web3" 2>/dev/null; then
        echo "  Installing dependencies..."
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
      fi
      deactivate || true
    elif [ -f "requirements.txt" ]; then
      echo "  Python dependencies already installed, skipping"
    else
      echo "  ℹ onchain-agent-kit appears to be documentation/template only (no usable package.json/requirements.txt)"
    fi
  else
    echo "  ℹ onchain-agent-kit has no package.json or requirements.txt"
  fi
  cd "$ROOT_DIR"
fi

echo "\n✓ Remaining repo installation complete!"
echo "\nSummary:"
echo "  - 4 Python repos processed"
echo "  - 5+ Node/TypeScript repos processed"
echo "  - Review warnings above for any repos that were skipped"
