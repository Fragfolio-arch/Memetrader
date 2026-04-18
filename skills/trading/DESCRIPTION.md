# Trading Skills

Skills for cryptocurrency and meme coin trading. These skills integrate with the Hermes trading system to provide AI-powered market analysis, smart money detection, and trade journaling.

## Available Skills

| Skill | Description |
|-------|-------------|
| **smart-money-detector** | Detect whale/wallet clustering and accumulation patterns |
| **memecoin-scanner** | Scan for emerging meme coins with volume spikes and social momentum |
| **trade-journal** | Post-trade analysis, performance tracking, and strategy adaptation |

## Requirements

All trading skills require:
- Helius RPC API key (for Solana data)
- CoinGecko API (free tier)
- DEX Ranger API (optional, for security checks)

## Setup

```bash
# Install skills
hermes skill install trading/smart-money-detector
hermes skill install trading/memecoin-scanner
hermes skill install trading/trade-journal
```

## Usage

Each skill provides natural language commands for trading analysis:

```
Analyze smart money for [TOKEN]
Scan for new meme coins
Show my trade journal
```