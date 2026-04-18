# MemeCoin Scanner

**Category:** Trading / Market Analysis
**Description:** Scan cryptocurrency markets for emerging meme coins with volume spikes, liquidity additions, and social momentum. Based on Jackhuang166/ai-memecoin-trading-bot patterns.
**Version:** 1.0.0
**Author:** Hermes Agent

## Features

- **Volume Spike Detection:** Find coins with >10% volume increase
- **New Liquidity Alerts:** Detect newly created liquidity pools
- **Social Momentum:** Correlate with Twitter/Telegram sentiment
- **Honeypot Detection:** Filter out scam tokens using DEX Ranger
- **Win Probability:** Calculate trade success probability based on historical data

## How It Works

1. **Data Collection:** Query CoinGecko, DexScreener, Birdeye for trending tokens
2. **Volume Analysis:** Calculate volume changes and identify spikes
3. **Social Check:** Analyze Twitter/Telegram sentiment for each token
4. **Security Scan:** Run DEX Ranger security check to filter honeypots
5. **Scoring:** Rate tokens on 1-10 scale based on:
   - Volume spike percentage
   - Liquidity level
   - Social sentiment
   - Security score

## Usage

```
Scan top 20 coins for volume spikes
```

```
Find new meme coins with high social momentum
```

```
List emerging tokens with >5M volume
```

## Tools Used

- CoinGecko API (via coingecko_tool)
- DexScreener (via dexscreener_tool)
- Birdeye (via birdeye_tool)
- Twitter sentiment (via twitter_sentiment_tool)
- DEX Ranger security (via dexranger_tool)

## Scoring Formula

```
Score = (Volume Score × 0.3) + (Liquidity Score × 0.2) + (Social Score × 0.3) + (Security Score × 0.2)

Where:
- Volume Score: 1-10 based on 24h volume change
- Liquidity Score: 1-10 based on pool liquidity
- Social Score: 1-10 based on Twitter/Telegram mentions
- Security Score: 1-10 based on DEX Ranger (honeypot check)
```

## Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Volume Spike | >50% | Flag as hot |
| Liquidity | >$100K | Pass security check |
| Social Score | >7/10 | Strong signal |
| Security | >70 score | Safe to trade |

## Integration

This skill implements:
- Volume spike detection (multi-agent pattern from ai-memecoin-trading-bot)
- Honeypot detection (security check)
- Win probability estimation

## Example Output

```
📊 MemeCoin Scanner Results

🥇 PEPE
  Volume: +156% (24h)
  Liquidity: $450K
  Social: 8.5/10
  Security: 85/100
  WIN PROBABILITY: 72%

🥈 WIF
  Volume: +89% (24h)
  Liquidity: $1.2M
  Social: 9/10
  Security: 92/100
  WIN PROBABILITY: 81%

Recommendation: Top picks - WIF, PEPE
```