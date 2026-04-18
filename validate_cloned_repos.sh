#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Starting local repo validation for cloned integrations..."

echo "\n1) Python repos"

if [ -d "mcp-wrappers/social/twitter-alpha-sentiment-tracker-v2" ]; then
  echo "\n- twitter-alpha-sentiment-tracker-v2"
  cd mcp-wrappers/social/twitter-alpha-sentiment-tracker-v2
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "tweepy\|transformers\|torch"; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/social/twikit" ]; then
  echo "\n- twikit"
  cd external-repos/social/twikit
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "httpx\|beautifulsoup4"; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    python3 -m pip install -e .
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

if [ -d "mcp-wrappers/solana/dexranger-skill" ]; then
  echo "\n- dexranger-skill"
  cd mcp-wrappers/solana/dexranger-skill
  echo "  -> dexranger-skill is standalone Python script + standard library; no extra Python install needed"
  if command -v python3 >/dev/null 2>&1; then
    python3 scripts/dexranger_check.py --help >/dev/null 2>&1 || true
  fi
  cd "$ROOT_DIR"
fi

echo "\n2) Node / TypeScript repos"

if [ -d "mcp-wrappers/solana/solana-agent-kit" ]; then
  echo "\n- solana-agent-kit"
  cd mcp-wrappers/solana/solana-agent-kit
  if [ ! -d "node_modules" ] && [ ! -d "pnpm_modules" ]; then
    if command -v pnpm >/dev/null 2>&1; then
      pnpm install
    else
      echo "  WARNING: pnpm not found. Install pnpm@9+ and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "mcp-wrappers/sui/sui-agent-kit" ]; then
  echo "\n- sui-agent-kit"
  cd mcp-wrappers/sui/sui-agent-kit
  if [ ! -d "node_modules" ] && [ ! -d "pnpm_modules" ]; then
    if command -v pnpm >/dev/null 2>&1; then
      pnpm install
    else
      echo "  WARNING: pnpm not found. Install pnpm@9+ and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "mcp-wrappers/sui/sui-trader-mcp" ]; then
  echo "\n- sui-trader-mcp"
  cd mcp-wrappers/sui/sui-trader-mcp
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  WARNING: npm not found. Install Node.js and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/solana/solana-agent-kit" ] && [ ! -d "mcp-wrappers/solana/solana-agent-kit" ]; then
  echo "\n- external solana-agent-kit"
  cd external-repos/solana/solana-agent-kit
  if [ ! -d "node_modules" ] && [ ! -d "pnpm_modules" ]; then
    if command -v pnpm >/dev/null 2>&1; then
      pnpm install
    else
      echo "  WARNING: pnpm not found. Install pnpm@9+ and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/sui/sui-agent-kit" ] && [ ! -d "mcp-wrappers/sui/sui-agent-kit" ]; then
  echo "\n- external sui-agent-kit"
  cd external-repos/sui/sui-agent-kit
  if [ ! -d "node_modules" ] && [ ! -d "pnpm_modules" ]; then
    if command -v pnpm >/dev/null 2>&1; then
      pnpm install
    else
      echo "  WARNING: pnpm not found. Install pnpm@9+ and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/sui/sui-trader-mcp" ] && [ ! -d "mcp-wrappers/sui/sui-trader-mcp" ]; then
  echo "\n- external sui-trader-mcp"
  cd external-repos/sui/sui-trader-mcp
  if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
      npm install
    else
      echo "  WARNING: npm not found. Install Node.js and rerun this step."
    fi
  else
    echo "  Dependencies already installed, skipping"
  fi
  cd "$ROOT_DIR"
fi

if [ -d "external-repos/social/twikit" ] && [ ! -d "external-repos/social/twikit/.venv" ]; then
  echo "\n- external twikit"
  cd external-repos/social/twikit
  if [ ! -d ".venv/lib" ]; then
    python3 -m venv .venv || true
  fi
  . .venv/bin/activate
  if ! python3 -m pip freeze | grep -q "httpx\|beautifulsoup4"; then
    echo "  Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    python3 -m pip install -e .
  else
    echo "  Dependencies already installed, skipping"
  fi
  deactivate || true
  cd "$ROOT_DIR"
fi

echo "\nRepo validation script complete. Review any warnings above."
