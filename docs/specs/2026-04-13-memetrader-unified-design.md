# MemeTrader Unified System - Detailed Design

> **Status**: Design Document (Brainstorming Phase)
> **Date**: 2026-04-13
> **Version**: 1.0

---

## Executive Summary

This document outlines the comprehensive design for unifying Hermes Agent with NOFX trading backend into a single AI-powered trading platform. The system will use Hermes as the single AI brain for all trading decisions, with NOFX serving as the execution layer.

### Key Decisions Made

| Decision | Description |
|----------|-------------|
| **Single AI Brain** | Hermes connects to NOFX via MCP - NOFX disables internal AI |
| **UI Integration** | Add Hermes features to NOFX-UI (Chat, Memory, Skills, Inspector) |
| **API Connection** | Use FastAPI on port 8643 (not Gateway) |
| **Data Sources** | Add CoinGecko, DexScreener, Birdeye, Helius |
| **DEX Support** | Prioritize Solana (Raydium, Jupiter), then EVM, then SUI |
| **Paper Trading** | Delete Hermes paper_engine.py - use NOFX testnet instead |

---

## Part 1: Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NOFX-UI (Port 3000)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  /hermes Page - Integrated AI Interface                            │   │
│  │                                                                     │   │
│  │  ┌─────────────┬─────────────┬─────────────┬─────────────┐         │   │
│  │  │    Chat    │   Memory   │   Skills   │  Inspector  │         │   │
│  │  │  (SSE)     │  (R/W)     │  (Browse)  │  (Debug)    │         │   │
│  │  └─────────────┴─────────────┴─────────────┴─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │ HTTP/WebSocket
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Hermes FastAPI Server (Port 8643)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Endpoints:                                                                 │
│  ├── POST /v1/chat/completions      → AI Chat with SSE streaming         │
│  ├── GET  /api/sessions             → Session management                 │
│  ├── GET  /api/memory                → Memory read                        │
│  ├── POST /api/memory                → Memory write                      │
│  ├── GET  /api/skills                → Skills list                         │
│  ├── GET  /api/skills/{name}         → Skill details                      │
│  ├── GET  /api/config                 → Configuration read                │
│  └── GET  /api/trading/...           → Trading portfolio (paper/NOFX)     │
│                                                                             │
│  MCP Client → Connects to external MCP servers                             │
│  (Will connect to NOFX MCP server when implemented)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Hermes Agent (Python)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Core Components:                                                            │
│  ├── AIAgent Loop (run_agent.py - 9400+ lines)                             │
│  ├── Tool Registry (60+ tools)                                              │
│  ├── Memory System (persistent across sessions)                             │
│  ├── Skills System (auto-improving skills)                                  │
│  ├── Context Compression (efficient long conversations)                   │
│  └── MCP Client (connects to external tools)                                │
│                                                                             │
│  LLM Configuration:                                                          │
│  • Single AI provider configured in ~/.hermes/config.yaml                   │
│  • Supports: OpenRouter, Anthropic, Google, DeepSeek, Qwen, Kimi, etc.   │
│  • Used for ALL decisions - trading, analysis, strategy                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ (When NOFX MCP implemented)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NOFX MCP Server (Future)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Exposed Tools:                                                              │
│  ├── analyze_market()        → Market analysis using Hermes LLM           │
│  ├── create_strategy()       → Strategy creation                           │
│  ├── execute_trade()         → Trade execution                             │
│  ├── get_positions()         → Position monitoring                         │
│  ├── optimize_grid()        → Grid optimization                           │
│  └── analyze_sentiment()     → News/social sentiment                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NOFX Trading Engine (Go - Port 8080)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Current (Disable AI):                                                      │
│  ├── AutoTrader config → Disable internal MCP AI calls                    │
│  ├── Remove DeepSeek, Qwen, Claude providers from NOFX config              │
│  └── NOFX executes trades ONLY - no AI decisions                           │
│                                                                             │
│  Trading Features:                                                          │
│  ├── Grid Trading Engine (working)                                          │
│  ├── 11 Exchange integrations (CEX + DEX)                                  │
│  ├── Position management                                                    │
│  └── Risk controls                                                           │
│                                                                             │
│  Current Exchanges:                                                          │
│  CEX: Binance, Bybit, OKX, Bitget, Gate, KuCoin, Indodax                   │
│  DEX: Hyperliquid, Aster, Lighter                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: UI Integration Design

### NOFX-UI New Page: `/hermes`

#### Page Structure

```
/hermes Page Layout
├── Header
│   ├── Logo + "AI Assistant" 
│   ├── Tabs: [Chat] [Memory] [Skills] [Inspector]
│   └── Settings gear icon
│
├── Main Content Area (tab-dependent)
│   ├── Chat Tab: Message list + input
│   ├── Memory Tab: File browser + editor
│   ├── Skills Tab: Category list + skill cards
│   └── Inspector Tab: Tool calls + timing + decisions
│
└── Footer
    ├── Model indicator (e.g., "Claude via OpenRouter")
    └── Connection status
```

#### Tab Details

##### 1. Chat Tab

| Feature | Implementation |
|---------|----------------|
| **Message Display** | Scrollable list, user/AI differentiation |
| **Input** | Text input + send button |
| **Streaming** | SSE from `/v1/chat/completions` |
| **Tool Calls** | Render as expandable cards |
| **Markdown** | Full markdown + syntax highlighting |
| **Actions** | Stop, retry, copy |

**API Endpoint**: `POST /v1/chat/completions`

```json
Request:
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "messages": [
    {"role": "user", "content": "Analyze SOL meme coins"}
  ],
  "stream": true
}

Response: SSE stream with chunks
```

##### 2. Memory Tab

| Feature | Implementation |
|---------|----------------|
| **File List** | Sidebar with memory files |
| **Search** | Search across memory entries |
| **Editor** | Markdown preview + live editing |
| **Actions** | Save, delete, create new |

**API Endpoints**:
- `GET /api/memory` - List all memory files
- `POST /api/memory` - Create/update memory
- `DELETE /api/memory` - Delete memory file

##### 3. Skills Tab

| Feature | Implementation |
|---------|----------------|
| **Category List** | Sidebar with categories |
| **Skill Cards** | Grid of available skills |
| **Search** | Search skills by name/tags |
| **Install** | One-click install for new skills |
| **Details** | Modal with skill documentation |

**API Endpoints**:
- `GET /api/skills` - List all skills
- `GET /api/skills/categories` - List categories
- `GET /api/skills/{name}` - Get skill details
- `POST /api/skills/{name}/install` - Install skill
- `POST /api/skills/{name}/toggle` - Enable/disable

##### 4. Inspector Tab

| Feature | Implementation |
|---------|----------------|
| **Tool Calls** | List of all tool calls in session |
| **Timing** | Latency per tool |
| ** Decisions** | AI reasoning display |
| **Errors** | Failed tool calls |
| **Copy** | Copy request/response |

---

## Part 3: Data Sources Design

### Current NOFX Data Providers

| Provider | Data Type | Status |
|----------|-----------|--------|
| **coinank** | Klines, OI, Liquidations, Instruments | ✅ Working |
| **nofxos** | AI500, OI rankings, NetFlow | ✅ Working |
| **hyperliquid** | Klines, Coin listings | ✅ Working |
| **alpaca** | Klines | ✅ Working |
| **twelvedata** | Klines | ✅ Working |

### New Data Sources to Add

#### Tier 1: Price & Market Data (Priority)

| Source | API | Free Tier | Data Provided |
|--------|-----|-----------|---------------|
| **CoinGecko** | REST | 10-30k/mo | Prices, market cap, volume, 24h change |
| **DexScreener** | REST | 10k/mo | Token analytics, pair data, trending |
| **Birdeye** | REST | 10k/mo | Solana TVL, token list, price |
| **DexLab** | REST | ✅ Free | Solana token data |

#### Tier 2: DEX & Chain Data

| Source | Chains | Data |
|--------|--------|------|
| **Helius** | Solana | RPC, gRPC (Yellowstone), parsed DEX trades |
| **Bitquery** | Multi | GraphQL - DEX trades, tokens, liquidity |

#### Tier 3: SUI Ecosystem

| Source | Data |
|--------|------|
| **Cetus API** | DEX data (in docs/specs plan) |
| **Sui RPC** | Chain data, transactions |

### Implementation: Add as Hermes Tools

```python
# tools/coingecko_tool.py
@registry.register(
    name="coingecko_price",
    toolset="market_data",
    schema={...},
    handler=lambda args, **kw: coingecko_price(
        token_id=args.get("token_id"),
        currency=args.get("currency", "usd")
    )
)
```

---

## Part 4: DEX Integration Design

### Exchange Priority

#### Priority 1: Solana DEXs (Best for Memes)

| DEX | Chain | API | SDK | Testnet |
|-----|-------|-----|-----|---------|
| **Raydium** | Solana | REST API | ✅ JS SDK | ✅ Devnet |
| **Jupiter** | Solana | REST API | ✅ JS SDK | ✅ Devnet |
| **Orca** | Solana | REST API | ✅ SDK | ✅ Devnet |
| **Meteora** | Solana | REST API | ✅ SDK | ✅ Devnet |

#### Priority 2: EVM DEXs

| DEX | Chain | Testnet | API |
|-----|-------|---------|-----|
| **Uniswap V3** | Ethereum, Arbitrum | ✅ Goerli/Sepolia | Subgraph |
| **Curve** | Ethereum, Arbitrum | ✅ Sepolia | Subgraph |
| **Velodrome** | Optimism | ✅ | Subgraph |
| **PancakeSwap** | BSC, Arbitrum | ✅ Testnet | REST |

#### Priority 3: SUI Ecosystem

| DEX | Chain | Testnet | Status |
|-----|-------|---------|--------|
| **Cetus** | SUI | ✅ Testnet | In plan |
| **Turbo** | SUI | ✅ Testnet | Not integrated |

### NOFX Trader Interface Pattern

Each exchange implements the same interface:

```go
type Trader interface {
    // Trading operations
    PlaceOrder(ctx context.Context, order Order) (string, error)
    CancelOrder(ctx context.Context, orderID string) error
    
    // Account operations
    GetAccount(ctx context.Context) (*Account, error)
    GetBalance(ctx context.Context, symbol string) (*Balance, error)
    
    // Position operations
    GetPositions(ctx context.Context) ([]Position, error)
    GetPosition(ctx context.Context, symbol string) (*Position, error)
}

type GridTrader interface {
    PlaceLimitOrder(req *LimitOrderRequest) (*OrderResult, error)
    GetOrderBook(symbol string, depth int) (bids, asks [][]float64, error)
}
```

---

## Part 5: Testing Strategy ($10 → $100k)

### Testing Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TESTING PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1: Paper Simulation (Current Hermes)                               │
│  ├── $10,000 virtual balance                                               │
│  ├── Works for ANY scenario                                               │
│  └── Issue: Doesn't use NOFX capabilities                                 │
│                                                                             │
│  Phase 2: NOFX Testnet                                                     │
│  ├── Hyperliquid testnet - REAL order execution                          │
│  ├── Lighter testnet - REAL order execution                               │
│  ├── Simulated P&L                                                         │
│  └── Issue: Limited DEX support (perp only)                               │
│                                                                             │
│  Phase 3: Solana Devnet                                                   │
│  ├── Raydium/Jupiter devnet - REAL swap execution                        │
│  ├── Virtual tokens (not real money)                                      │
│  ├── Test full trading flow                                               │
│  └── Target: Prove strategy works 5-10x                                   │
│                                                                             │
│  Phase 4: Small Real Money                                                │
│  ├── Move to mainnet with $10-100                                         │
│  ├── Same strategy proven in testnet                                      │
│  └── Scale up after consistent profits                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Success Criteria

| Phase | Target | Verify |
|-------|--------|--------|
| Phase 1 | 10x return | Consistent over 10 runs |
| Phase 2 | 10x return | On real exchange testnet |
| Phase 3 | 10x return | On Solana devnet |
| Phase 4 | Deploy | Move to real money |

---

## Part 6: Implementation Tasks

### Task Categories

#### A. Delete/Remove

| Task | File | Action |
|------|------|--------|
| Delete Hermes Paper Trading | `tools/trading/paper_engine.py` | Delete entire file |
| Remove paper trading exports | `tools/trading/__init__.py` | Remove paper imports |
| Remove paper trading API | `gateway/fastapi_server.py` | Remove `/api/trading/*` |

#### B. NOFX Integration

| Task | File | Action |
|------|------|--------|
| Disable NOFX internal AI | `nofx/trader/auto_trader.go` | Remove MCP AI calls |
| Connect Hermes to NOFX | `tools/nofx_trading_tool.py` | Ensure working |

#### C. UI Integration (NOFX-UI)

| Task | Action |
|------|--------|
| Create `/hermes` page | New React page component |
| Add Chat tab | Connect to `/v1/chat/completions` |
| Add Memory tab | Connect to `/api/memory` |
| Add Skills tab | Connect to `/api/skills` |
| Add Inspector tab | Parse tool calls from response |

#### D. Data Sources

| Task | Action |
|------|--------|
| Add CoinGecko tool | Create `tools/coingecko_tool.py` |
| Add DexScreener tool | Create `tools/dexscreener_tool.py` |
| Add Birdeye tool | Create `tools/birdeye_tool.py` |

**Tools to create:**
- `tools/coingecko_tool.py` - Prices, market cap, 17k+ coins
- `tools/dexscreener_tool.py` - Token analytics, pair data
- `tools/birdeye_tool.py` - Solana-specific, wallet tracking

#### E. DEX Integration

| Task | Action |
|------|--------|
| Add Raydium trader | Create `nofx/trader/raydium/` (devnet ✅) |
| Add Jupiter trader | Create `nofx/trader/jupiter/` (devnet ✅) |
| Add Cetus trader | Create `nofx/trader/cetus/` (testnet ✅) |
| Connect via Hermes MCP | Add MCP tools for DEX |

**DEX Priority:**
1. Raydium (Solana) - Most established
2. Jupiter (Solana) - Best liquidity aggregator
3. Cetus (SUI) - Testnet ready

#### F. Social Hype-Meter

| Task | Action |
|------|--------|
| Twitter scraper | Create `tools/twitter_sentiment_tool.py` |
| Telegram scraper | Create `tools/telegram_sentiment_tool.py` |
| Reddit scraper | Create `tools/reddit_sentiment_tool.py` |
| Discord scraper | Create `tools/discord_sentiment_tool.py` |

#### G. On-Chain Radar

| Task | Action |
|------|--------|
| Solana RPC | Integrate Helius for RPC + parsed DEX trades |
| SUI RPC | Integrate SUI RPC for chain data |
| Wallet tracking | Track smart-money wallets |

---

## Part 7: Configuration

### Unified Config: `~/.hermes/config.yaml`

```yaml
# Single AI Configuration
model:
  default: "openrouter/anthropic/claude-sonnet-4-20250514"

# Providers (configured once, used by both Hermes and NOFX)
# Remove from NOFX, use Hermes config only
providers:
  openrouter:
    api_key: "${OPENROUTER_API_KEY}"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"

# Trading Configuration (NOFX)
nofx:
  enabled: true
  api_url: http://localhost:8080
  api_token: your-jwt-token

# Data Sources
data_sources:
  coingecko:
    enabled: true
  dexscreener:
    enabled: true
  birdeye:
    enabled: true

# UI Settings (NOFX-UI)
ui:
  theme: dark
  hermes_tab: true
```

### NOFX-UI Settings Page Additions

| Setting | Description |
|---------|-------------|
| LLM Provider | Dropdown: OpenRouter, Anthropic, etc. |
| Model | Dropdown: Available models for provider |
| API Key | Input (stored in config) |
| Theme | Dark/Light (shared) |

---

## Part 8: Security Considerations

| Area | Consideration |
|------|---------------|
| **API Keys** | Store in `~/.hermes/.env`, not in code |
| **NOFX Connection** | JWT token auth between Hermes and NOFX |
| **UI Auth** | NOFX-UI has built-in auth (login/register) |
| **CORS** | FastAPI configured with CORS for NOFX-UI |
| **Rate Limiting** | Implement per-endpoint rate limits |

---

---

## Part 10: The Vision - Autonomous AI Trading Firm

### The Grand Vision

Building a **fully autonomous, self-evolving, high-frequency AI trading firm** dedicated to mastering the meme coin market.

**Ultimate Goal:** Turn **$10 → $100,000** through aggressive exponential compounding by catching massive multipliers.

### The Testing Protocol (Crucible)

Before risking real capital, the AI must prove itself:
- Must hit **$100,000 target 5 separate times** in paper trading
- Fed by live real-world data
- Only after consistent success → real capital deployment

### The Dual-Intelligence Engine

#### On-Chain Radar
- Scanning high-speed blockchains in real-time:
  - **Solana** - Primary (fastest for memes)
  - **SUI** - Secondary (new, low fees)
- Detecting: Volume spikes, new liquidity pools, smart-money wallet movements

#### Social Hype-Meter
- Scraping social platforms:
  - **Twitter (X)** - Primary social
  - **Telegram** - Community signals
  - **Reddit** - Subreddit sentiment
  - **Discord** - Server activity
- Gauging: Sentiment, current "meta", real human attention vs bots

### The Self-Evolving Mind

**Primary:** Hermes Memory System
- Stores trade history, outcomes, lessons learned
- Continuous context from past trades
- Adapts strategy based on memory

**Future Enhancement:** RL Agents
- Reinforcement learning for strategy optimization
- Can be added as separate skill
- Uses `rl_training_tool.py` pattern

### DEX Integration with Testnet

Only integrate DEXs with testnet/devnet support:
- **Raydium** - Solana devnet ✅
- **Jupiter** - Solana devnet ✅
- **Cetus** - SUI testnet ✅

No real money until proven in testnet 5x.

---

## Part 11: Success Metrics

### Trading Success

| Metric | Target |
|--------|--------|
| **Paper Trading** | 5x hits $100k target in simulation |
| **Final Target** | $10 → $100,000 |
| **Response Time** | < 2s for chat, < 5s for trades |
| **Uptime** | 99.9% for both services |
| **Tool Success** | > 95% tool call success rate |
| **Memory RAM** | < 500MB for Hermes |

### System Success

| Metric | Target |
|--------|--------|
| **Data Sources** | CoinGecko + DexScreener + Birdeye working |
| **DEX Support** | Raydium + Jupiter + Cetus integrated |
| **Testnet Pass** | 5x $100k in testnet before real capital |
| **Self-Evolution** | Memory system learning from every trade |

---

## Appendix: Port Mapping

| Service | Port | Description |
|---------|------|-------------|
| Hermes FastAPI | 8643 | AI chat, sessions, memory, skills, config |
| Hermes Gateway | 8642 | Messaging platforms (Telegram, Discord, Slack) |
| NOFX API | 8080 | Trading backend (15+ exchanges) |
| NOFX-UI | 3000 | Trading dashboard + Hermes UI |

---

## References

- Hermes Agent: `https://github.com/NousResearch/hermes-agent`
- Hermes Workspace: `https://github.com/outsourc-e/hermes-workspace`
- NOFX: `https://github.com/NoFxAiOS/nofx`
- Raydium API: `https://docs.raydium.io/raydium/api-reference/trade/trade-api`
- Jupiter API: `https://dev.jup.ag/api-reference`

---

## Part 12: References

- CoinGecko API: https://www.coingecko.com/en/api
- DexScreener: https://dexscreener.com
- Birdeye: https://birdeye.so
- Raydium API: https://docs.raydium.io/raydium/api-reference
- Jupiter API: https://dev.jup.ag/api-reference
- Cetus Docs: https://cetus-1.gitbook.io/cetus-developer-docs/
- Hermes Memory: `tools/memory_tool.py`
- RL Training: `tools/rl_training_tool.py`

---

*Document Version: 1.1*
*Status: Design Complete - Ready for Implementation Planning*