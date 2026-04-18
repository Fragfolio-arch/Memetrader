# Smart Money Detector - References

Based on patterns from:

## Reference Repositories

1. **kryptogo-meme-trader**
   - URL: (referenced in Part 20)
   - Features: Wallet clustering, accumulation detection, swap execution
   - Key insight: Cluster analysis for smart money detection

2. **Jackhuang166/ai-memecoin-trading-bot**
   - Stars: 109
   - Features: Multi-agent, honeypot detection, win probability
   - Key insight: Win probability estimation

## Implementation Notes

This skill combines:
- Wallet clustering from kryptogo patterns
- Accumulation signals similar to whale tracking
- Integration with existing tools (helius_tool, wallet_tracker)

## API Dependencies

- Helius RPC: For Solana transaction data
- Wallet addresses: Known whale wallets for clustering

## Future Enhancements

- Add wallet address database
- Implement real-time cluster monitoring
- Add Discord/Telegram alerts for whale movements