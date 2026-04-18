# Smart Money Detector

**Category:** Trading / On-Chain Analysis
**Description:** Detect smart money movements by analyzing wallet clustering and accumulation patterns on Solana. Identifies when whales are buying/selling specific tokens.
**Version:** 1.0.0
**Author:** Hermes Agent

## Features

- **Wallet Clustering:** Group related wallets to identify whale activity
- **Accumulation Detection:** Spot when smart money is accumulating a token
- **Distribution Tracking:** Monitor when whales are distributing/selling
- **Historical Pattern Analysis:** Compare current activity with historical patterns

## How It Works

1. **Cluster Analysis:** Use Helius RPC to get transaction history for known whale addresses
2. **Accumulation Signals:** Calculate net inflow/outflow for tokens per wallet cluster
3. **Smart Money Scoring:** Rate tokens based on whale activity (1-10 scale)
4. **Alert Generation:** Notify when smart money is heavily accumulating a token

## Usage

```
Analyze smart money activity for SOL
```

```
Find whale wallets accumulating BONK
```

```
Show distribution patterns for WIF
```

## Tools Used

- Helius RPC (via helius_tool)
- Wallet tracker (via wallet_tracker)
- Token price data (via coingecko_tool, dexscreener_tool)

## Key Metrics

| Metric | Description |
|--------|-------------|
| **Cluster Size** | Number of related wallets |
| **Net Flow** | 24h inflow minus outflow |
| **Holding Change** | % change in whale holdings |
| **Smart Score** | 1-10 rating based on activity |

## Integration

This skill combines:
- Wallet clustering (similar to kryptogo-meme-trader)
- Accumulation detection
- Swap execution capability

## Example Output

```
🐋 Smart Money Report: BONK

Cluster: 12 wallets identified
Net Flow: +45M BONK (24h)
Holding Change: +8.5%
Smart Score: 8/10

Recommendation: WHALE ACCUMULATING - Strong buy signal
```