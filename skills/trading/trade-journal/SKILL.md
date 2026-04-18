# Trade Journal

**Category:** Trading / Performance Analysis
**Description:** Post-trade analysis and learning system. Tracks trade history, analyzes what worked and what didn't, and adapts trading strategies based on outcomes. Similar to trading212-agent-skills patterns.
**Version:** 1.0.0
**Author:** Hermes Agent

## Features

- **Trade Logging:** Record every trade with entry/exit, reasoning, and outcomes
- **Performance Analysis:** Calculate win rate, profit factor, average trade
- **Strategy Adaptation:** Learn from wins/losses and update trading approach
- **Weekly Summaries:** Generate trading reports with insights
- **Pattern Recognition:** Identify recurring mistakes or successful patterns

## How It Works

1. **Automatic Logging:** After each trade, record to memory:
   - Token traded
   - Entry/exit prices
   - Position size
   - Win/loss
   - Reasoning behind decision
   - What worked/what didn't
2. **Weekly Analysis:** Every Sunday, analyze:
   - Win rate by token
   - Best/worst performing strategies
   - Common mistakes
   - Adjustments needed
3. **Strategy Updates:** Modify trading approach based on findings

## Usage

```
Log trade: Bought SOL at $180, sold at $195, profit +8.3%
```

```
What was my win rate this week?
```

```
Analyze my last 20 trades
```

```
What patterns have been most profitable?
```

## Data Tracked

| Field | Description |
|-------|-------------|
| Symbol | Token traded |
| Side | Long/Short |
| Entry Price | Purchase price |
| Exit Price | Selling price |
| Quantity | Amount traded |
| PnL | Profit/Loss |
| PnL % | Percentage return |
| Reasoning | Why trade was taken |
| Outcome | What actually happened |
| Mistakes | What went wrong |
| Lessons | What to improve |

## Metrics Calculated

- **Win Rate:** % of profitable trades
- **Profit Factor:** Gross profits / Gross losses
- **Average Win/Loss:** Mean return per trade
- **Sharpe Ratio:** Risk-adjusted returns
- **Max Drawdown:** Largest peak-to-trough

## Integration

Uses Hermes memory system for persistent storage across sessions.
Combines with:
- nofx_trade for execution tracking
- dex_swap for DEX trade logging

## Example Output

```
📈 Weekly Trade Summary - Week 15

Trades: 12
Win Rate: 66.7% (8 wins, 4 losses)
Total PnL: +$1,247
Profit Factor: 2.3

📊 By Token:
  SOL: 4 trades, +$890 (best performer)
  WIF: 3 trades, +$340
  BONK: 5 trades, +$17 (needs work)

🔍 Pattern Analysis:
  ✓ Volume spike entries: 75% win rate
  ✓ Whale following: 80% win rate
  ✗ Counter-trend trades: 20% win rate (stop doing)

📝 Key Lesson: Focus on momentum trades, avoid counter-trend
```