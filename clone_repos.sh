#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

mkdir -p external-repos/solana external-repos/sui external-repos/social external-repos/base external-repos/multi-chain external-repos/security

repos=(
  # Social / Twitter
  "https://github.com/d60/twikit.git"
  "https://github.com/Rezzecup/twitter-alpha-sentiment-tracker-v2.git"

  # Solana
  "https://github.com/sendaifun/solana-agent-kit.git"
  "https://github.com/sashazykov/dexranger-skill.git"

  # SUI
  "https://github.com/kukapay/sui-trader-mcp.git"
  "https://github.com/pelagosaionsui/sui-agent-kit.git"
  "https://github.com/aldrin-labs/capybot.git"
  "https://github.com/SuiSec/HoneyPotDetectionOnSui.git"

  # Base / EVM + multi-chain
  "https://github.com/nirholas/universal-crypto-mcp.git"
  "https://github.com/edkdev/defi-trading-mcp.git"
  "https://github.com/clawd800/pumpclaw.git"
  "https://github.com/chainstacklabs/web3-ai-trading-agent.git"
  "https://github.com/sebasneuron/onchain-agent-kit.git"
  "https://github.com/igormoondev/onchain-agent-kit.git"
  "https://github.com/cortexaiofficial/Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine.git"

  # Security / Rug checks
  "https://github.com/Rezzecup/pump-fun-rug-checker-lite.git"
  "https://github.com/drixindustries/Rug-Killer-On-Solana.git"
  "https://github.com/degenfrends/solana-rugchecker.git"
)

for repo in "${repos[@]}"; do
  name=$(basename "$repo" .git)
  if [ -d "external-repos/solana/$name" ] || [ -d "external-repos/sui/$name" ] || [ -d "external-repos/social/$name" ] || [ -d "external-repos/base/$name" ] || [ -d "external-repos/multi-chain/$name" ] || [ -d "external-repos/security/$name" ] || [ -d "external-repos/core/$name" ]; then
    echo "SKIP already exists: $name"
    continue
  fi

  target="external-repos/$name"
  case "$name" in
    twikit|twitter-alpha-sentiment-tracker-v2)
      target="external-repos/social/$name" ;;
    solana-agent-kit|dexranger-skill)
      target="external-repos/solana/$name" ;;
    sui-trader-mcp|sui-agent-kit|capybot|HoneyPotDetectionOnSui)
      target="external-repos/sui/$name" ;;
    universal-crypto-mcp|defi-trading-mcp|pumpclaw|web3-ai-trading-agent)
      target="external-repos/base/$name" ;;
    onchain-agent-kit|Autonomous-AI-Trading-Agent-MCP-Flash-Arb-Engine)
      target="external-repos/multi-chain/$name" ;;
    pump-fun-rug-checker-lite|Rug-Killer-On-Solana|solana-rugchecker)
      target="external-repos/security/$name" ;;
  esac

  echo "Cloning $repo into $target"
  git clone "$repo" "$target" || {
    echo "FAILED to clone $repo"
    continue
  }
done

echo "Clone script finished. Check external-repos/ for the cloned repositories."
