# MemeTrader Unified System - Detailed Design

> **Status**: Design Document (Brainstorming Complete)
> **Date**: 2026-04-13
> **Version**: 4.0 (Final - All Decisions Made)

---

## Executive Summary

This document outlines the comprehensive design for unifying Hermes Agent with NOFX trading backend into a single AI-powered trading platform. The system will use Hermes as the single AI brain for all trading decisions, with NOFX serving as the execution layer.

### Key Decisions Made (v4.0 - Final)

| Decision | Description | Status |
|----------|-------------|--------|
| **Single AI Brain** | Hermes connects to NOFX via MCP - NOFX disables internal AI | ✅ |
| **UI Integration** | Add Hermes features to NOFX-UI (Chat, Memory, Skills, Inspector) | ✅ |
| **API Connection** | Use FastAPI on port 8643 (not Gateway) | ✅ |
| **Data Sources** | Add CoinGecko, DexScreener, Birdeye, Helius | ✅ |
| **DEX Support** | Prioritize Solana (Raydium, Jupiter), then EVM, then SUI | ✅ |
| **Paper Trading** | Delete Hermes paper_engine.py - use NOFX testnet instead | ✅ |
| **Routing (R3)** | Auto-route based on trade type (perp→NOFX, DEX→Hermes) | ✅ |
| **Strategy (S2)** | Hybrid - NOFX grid + Hermes for DEX/sentiment | ✅ |
| **Wallet (Hermes)** | DEX wallet in Hermes (2-wallet pattern) | ✅ |
| **Wallet Security** | 2-wallet + safety limits (W1) | ✅ |
| **Core Agent** | Hermes as core agent with multi-agent system | ✅ |
| **Multi-Agent** | cronjob + delegate + background processes | ✅ |
| **Social Agents** | 4 agents: Twitter + Telegram + Discord + News | ✅ |
| **News Agent** | Separate dedicated agent (Q7) | ✅ |
| **Twitter API** | Twikit (FREE - no API key!) | ✅ |
| **Signal Output** | Dual: OWN trading group + PUBLIC signal channel | ✅ |
| **Public Revenue** | Tip jar enabled (R1) | ✅ |
| **Autonomous** | A2: Autonomous with limits | ✅ |

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

### DEX Swap - NEW Functionality

**Current State:** NOFX is perp-focused - NO swap functionality exists.

**New Addition Required:** Add DEX swap capability for:
- Token-to-token swaps (SOL/USDC, SOL/COIN, COIN/COIN)
- Limit orders on DEX
- Grid trading on DEX

### DEX Integration Technical Details

| DEX | Language | API | Devnet | Notes |
|-----|----------|-----|-------|-------|
| **Raydium** | TypeScript | REST API | ✅ | No Go SDK - needs wrapper |
| **Jupiter** | TypeScript | v1 API (new) | ✅ | Best aggregator |
| **Cetus** | TypeScript | REST | ✅ | SUI only |

### DEX Implementation Approach

1. **Hermes Tool** (`tools/dex_swap_tool.py`)
   - Direct REST calls to DEX APIs
   - Wallet signing via Solana wallet
   - Devnet for testing

2. **NOFX Integration** (future)
   - Add Go wrapper for DEX
   - Full trading pipeline

### Supported Swap Pairs

```
SOL/USDC - Most liquid
SOL/COIN - Meme coin trading (main use case)
COIN/COIN - Any token pair via Jupiter routing
```

### Trading Types

| Type | Description | Support |
|------|------------|----------|
| **Market Swap** | Instant swap at best price | Via DEX API |
| **Limit Swap** | Swap at target price | New (needs implementation) |
| **Grid Swap** | Multiple limit orders | New (needs implementation) |
| **Perp Trading** | Existing in NOFX | ✅ |

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

## Part 13: Wallet & Security

### DEX Wallet Management

**Solana Wallet:**
- Stored in config: `SOLANA_WALLET_PRIVATE_KEY`
- Used for signing DEX transactions
- Supports devnet for testing

**Wallet Pattern in Code:**
```go
type DexWallet struct {
    PrivateKey string  // Base58 encoded
    PublicKey string  // Wallet address
}

// Sign transaction for submission
func (w *DexWallet) SignTransaction(tx []byte) ([]byte, error)
```

### Hermes Integration

**Trading Flow:**
```
User → Hermes (chat) → 
  → nofx_trade (perp) OR 
  → dex_swap (new - token swap)
  → Wallet signing
  → DEX API → Blockchain
```

**Tool Options:**
- Use `nofx_trade` for perps (existing)
- Use `dex_swap` for DEX (new)

---

## Part 14: Testnet Setup

### Devnet Configuration

**Solana Devnet:**
- RPC: https://api.devnet.solana.com
- WS: wss://api.devnet.solana.com
- Faucet: https://solfaucet.com

**Test Tokens:**
- Airdrop SOL from faucet
- Use USDC mock for testing

### Testing Pipeline

```
Step 1: Devnet Swap
  - Test basic swap (SOL → USDC)
  - Verify transaction success
  - No real value

Step 2: Meme Coin Test
  - Swap to test token
  - Verify routing works

Step 3: Limit Order Test
  - Place limit order
  - Test fill/cancel

Step 4: Grid Test
  - Deploy grid strategy
  - Verify multiple orders

Step 5: Production Ready
  - Move to mainnet
  - Start with small amount
```

---

## Part 15: Implementation Priority

### Phase 1: Data Sources (C)
1. CoinGecko tool
2. DexScreener tool
3. Birdeye tool

### Phase 2: DEX Swap Tool (D)
1. Hermes tool: `dex_swap_tool.py`
2. Jupiter integration
3. Raydium integration
4. Limit order support

### Phase 3: On-Chain Radar
1. Solana RPC via Helius
2. Wallet tracking
3. Pool detection

### Phase 4: Social Hype-Meter
1. Twitter scraper
2. Telegram scraper
3. Sentiment analysis

### Phase 5: Self-Evolution
1. Hermes memory integration
2. Trade analysis logging
3. Strategy adaptation

---

## Part 16: References

### Data Sources APIs
- CoinGecko API: https://www.coingecko.com/en/api
- DexScreener: https://dexscreener.com
- Birdeye: https://birdeye.so
- CoinGecko Docs: https://docs.coingecko.com

### DEX APIs
- Raydium Swap API: https://docs.raydium.io/raydium/for-traders/raydium-swap
- Jupiter API v1: https://dev.jup.ag/docs/swap-api
- Jupiter Ultra Swap: https://docs.jup.ag/
- Cetus Docs: https://cetus-1.gitbook.io/cetus-developer-docs/

### Solana
- Solana RPC: https://solana.com/docs/rpc
- Helius: https://helius.dev (RPC + parsed DEX)
- Solana Stack Exchange: https://solanastackexchange.com

### NOFX
- Existing perp traders: `nofx/trader/bybit/`, `nofx/trader/okx/`, etc.
- Grid interface: `nofx/trader/types/interface.go`
- Wallet management: `nofx/wallet/`

### Hermes
- Memory: `tools/memory_tool.py`
- RL Training: `tools/rl_training_tool.py`
- NOFX trading tool: `tools/nofx_trading_tool.py`

---

## Part 17: Hermes Core Agent Architecture

### Overview: Hermes as the Single AI Brain

Hermes becomes the **core agent** that orchestrates ALL trading decisions. It doesn't just handle chat - it's the brain that thinks, decides, learns, and evolves.

### Hermes Capabilities

| Capability | Description | Use Case |
|-----------|------------|----------|
| **60+ Tools** | File, terminal, web, trading, analysis | Execute all tasks |
| **Memory System** | Persistent sessions + cross-session recall | Learn from trades |
| **Skills System** | Auto-improving skills | Trading strategies |
| **MCP Client** | Connect to external tools | Extend via MCP |
| **Session DB** | SQLite with FTS5 search | Trade history |
| **Context Compression** | Auto-summarize long convos | Deep analysis |
| **Prompt Caching** | Anthropic caching support | Cost efficiency |
| **Multi-Platform** | CLI, Telegram, Discord, Slack | Any interface |

### Hermes Core Agent Flow

```
User Input (Chat/Telegram/Discord/CLI)
         │
         ▼
┌─────────────────────────────────────────┐
│         HERMES CORE AGENT              │
│  ┌─────────────────────────────┐  │
│  │  System Prompt (Identity) │  │
│  │  + Memory Context     │  │
│  │  + Skills          │  │
│  │  + Tools          │  │
│  └─────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌─────────────────────────────┐  │
│  │   LLM Decision Engine   │  │
│  │  (Anthropic/OpenAI)   │  │
│  └─────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌─────────────────────────────┐  │
│  │   Tool Execution        │  │
│  │  • nofx_trade         │  │
│  │  • dex_swap (NEW)     │  │
│  │  • memory           │  │
│  │  • web_search      │  │
│  │  • ...            │  │
│  └─────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌─────────────────────────────┐  │
│  │   Learning Loop      │  │
│  │  Save to memory    │  │
│  │  Update skills   │  │
│  └─────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ▼
   Trading Execution
```

### Hermes Decision Routing (R3)

| Trade Type | Route | Executor |
|-----------|-------|---------|
| **Perp/Futures** | `nofx_trade` → NOFX | NOFX |
| **Hyperliquid** | `nofx_trade` → NOFX | NOFX |
| **DEX Spot Swap** | `dex_swap` → Hermes + Wallet | Hermes |
| **DEX Limit Order** | `dex_limit_order` → Hermes + Wallet | Hermes |
| **Grid on DEX** | `dex_grid` → Hermes + Wallet | Hermes |

---

## Part 18: Multi-Agent System (cronjob + delegate)

### Built-in Multi-Agent Capabilities

Hermes has **built-in** multi-agent capabilities:

| Component | Function | Trading Use Case |
|-----------|----------|-------------|
| **cronjob** | Schedule recurring tasks | Market scanning every 5 min |
| **delegate_task** | Spawn parallel subagents | Analyze 10 coins simultaneously |
| **Background processes** | Run tasks in background | Execute & monitor trades |
| **Skills** | Auto-loading strategies | Trading strategy skills |

### Cron Jobs for Trading

```python
# Market scanner - every 5 minutes
cronjob(action="create", job_id="market_scanner", 
       prompt="Scan top 20 coins on CoinGecko for >10% volume spike. "
              "Check Twitter for sentiment. "
              "If strong buy signal, create trade plan in memory.",
       schedule="*/5 * * * *")

# Position checker - every 15 minutes  
cronjob(action="create", job_id="position_check",
       prompt="Check all open positions. "
              "If any >5% loss, evaluate stop loss. "
              "If any >10% gain, evaluate take profit.",
       schedule="*/15 * * * *")

# Morning summary - daily
cronjob(action="create", job_id="morning_report",
       prompt="Generate trading summary for yesterday. "
              "What worked, what didn't. "
              "Update strategy in memory.",
       schedule="0 8 * * *")
```

### Delegate for Parallel Analysis

```python
delegate_task(
    goal="Analyze these 10 memecoins and rank by buy potential",
    coins=["SOL", "BONK", "WIF", "POPCAT", "MEW", "BOME", "PYTH", "JUP", "RAY", "ANIME"],
    context="Use CoinGecko for prices, DexScreener for liquidity, "
            "Twitter for sentiment. Score 1-10 each.",
    toolsets=["web", "trading"]
)
```

---

## Part 19: Wallet Architecture (2-Wallet Pattern)

### Security Pattern: 2-Wallet per DEX

| DEX | Agent Credentials | Main Wallet | Security |
|-----|--------------|-----------|----------|---------|
| **Hyperliquid** | privateKey (hex) | walletAddr | 2-wallet |
| **Lighter** | API Key + Index | walletAddr | 2-wallet + API |
| **Raydium** | Private key (base58) | Main wallet addr | 2-wallet |
| **Jupiter** | Private key (base58) | Main wallet addr | 2-wallet |
| **Cetus** | Private key | Main wallet addr | 2-wallet |

### Agent Wallet (Sign Only)

- **Purpose**: Sign transactions, hold minimal balance
- **Security**: Balance should be ~0 (like Hyperliquid)
- **Usage**: Transaction signing

### Main Wallet (Funds)

- **Purpose**: Hold funds, never expose private key
- **Security**: Never used for signing directly
- **Usage**: Fund agent wallet when needed

### Implementation in Hermes

```python
# Hermes config: ~/.hermes/config.yaml
dex:
  solana:
    agent_wallet_private_key: "${SOLANA_AGENT_KEY}"  # Encrypted
    main_wallet_address: "${SOLANA_MAIN_WALLET}"
  sui:
    agent_wallet_private_key: "${SUI_AGENT_KEY}"  # Encrypted
    main_wallet_address: "${SUI_MAIN_WALLET}"
```

---

## Part 20: Similar Skills Research (GitHub)

### Existing Skills to Reference

| Skill | Stars | Key Features |
|-------|------|-------------|
| **kryptogo-meme-trader** | - | Wallet clustering, accumulation detection, swap execution |
| **solana-agent** | 15 | Zero-hallucination tool calling, GPT-5.4 |
| **solclaw** | 11 | 60+ Solana actions via WhatsApp/Telegram |
| **pumpclaw** | 5 | pump.fun trading, token launch |
| **trading212-agent-skills** | 50 | Trading 212 API wrapper |
| **Jackhuang166/ai-memecoin-trading-bot** | 109 | Multi-agent, honeypot detection, win probability |

### Key Insights from Skills

1. **Cluster Analysis**: Kryptogo-style wallet clustering for smart money detection
2. **Learning System**: Post-trade analysis, trade journal, strategy adaptation
3. **Safety Guardrails**: Max position size, stop-loss, take-profit
4. **Autonomous vs Supervised**: Default supervised, opt-in autonomous

---

## Part 21: Complete System Diagram (v2.0)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          MEMETRADER COMPLETE SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐              │
│  │              HERMES CORE AGENT (Port 8643)                       │              │
│  │  ┌─────────────────────────────────────────────────────┐   │              │
│  │  │  AI Brain: LLM (Anthropic/OpenAI/DeepSeek)      │   │              │
│  │  │  • Single decision engine for all trading       │   │              │
│  │  │  • Memory: learns from every trade            │   │              │
│  │  │  • Skills: auto-improving strategies         │   │              │
│  │  └─────────────────────────────────────────────────────┘   │              │
│  │                        │                                   │              │
│  │  ┌─────────────────────────────────────────────────────┐   │              │
│  │  │  Multi-Agent System                            │   │              │
│  │  │  • cronjob: scheduled scanning              │   │              │
│  │  │  • delegate: parallel coin analysis      │   │              │
│  │  │  • background: async trade execution   │   │              │
│  │  └─────────────────────────────────────────────────────┘   │              │
│  │                        │                                   │              │
│  │  ┌─────────────────────────────────────────────────────┐   │              │
│  │  │  60+ Tools                                      │   │              │
│  │  │  • nofx_trade: perp/futures                  │   │              │
│  │  │  • dex_swap: NEW - Solana DEX swaps         │   │              │
│  │  │  • coingecko_price: market data          │   │              │
│  │  │  • dexscreener_*: token analytics    │   │              │
│  │  │  • birdeye_*: Solana data          │   │              │
│  │  │  • twitter_sentiment: social radar    │   │              │
│  │  │  • telegram_sentiment: signals       │   │              │
│  │  │  • memory: persistent learning      │   │              │
│  │  │  • delegate_task: parallel agents │   │              │
│  │  │  • cronjob: scheduled tasks       │   │              │
│  │  └─────────────────────���───────────────────────────────┘   │              │
│  └───────────────────────────────────────────────────────────────────────────┘              │
│                                    │                                             │
│                                    │ AUTO-ROUTING (R3)                           │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  ┌────────────────────┐ │
│  │                   NOFX TRADING BACKEND                  │  │  DEX WALLETS     │ │
│  │  ┌───────────────────────────────────────────┐       │  │  (Hermes Tool)   │ │
│  │  │  Perps/Futures: OKX, Bybit, Gate, etc.  │       │  │  ┌──────────┐  │ │
│  │  │  Hyperliquid, Lighter, Aster              │       │  │  │ Agent   │  │ │
│  │  │  Grid Trading Engine                   │       │  │  │ Key     │  │ │
│  │  │  Position Management               │       │  │  └──────────┘  │ │
│  │  │  Risk Controls                  │       │  │  ┌──────────┐  │ │
│  │  └───────────────────────────────────────────┘       │  │  │ Main    │  │ │
│  └───────────────────────────────────────────┘       │  │  │ Wallet │  │ │
│                                                │  └──────────┘  │ │
│                                                └────────────────────┘ │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA SOURCES                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │CoinGecko│ │DexScreen│ │ Birdeye │ │ Helius  │ │ NOFXos  │  │   │
│  │  │Prices │ │  Token  │ │Solana  │ │ RPC    │ │  OI    │  │   │
│  │  │+Market│ │Analytics│ │ Data   │ │+Webhooks│ │+AI500  │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐   │
│  │                    SOCIAL HYPE-METER                                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │
│  │  │ Twitter │ │Telegram │ │ Reddit  │ │ Discord │                    │   │
│  │  │ Sentiment│ │ Signals │ │Discussion│ │ Activity│                    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                    │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐   │
│  │                    DEX INTEGRATIONS (Solana/SUI)                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                  │   │
│  │  │ Raydium │ │ Jupiter │ │  Cetus  │ │  Meteora │                  │   │
│  │  │  DEX   │ │Aggregtr │ │  SUI    │ │  Liquidity│                  │   │
│  │  │ Devnet │ │  Devnet │ │ Testnet │ │  Devnet │                  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                  │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐   │
│  │                    LEARNING SYSTEM                                    │   │
│  │  ┌───────────────────────────────────────────────────────────────┐    │   │
│  │  │  After every trade:                                          │    │   │
│  │  │  1. Save trade to memory (Hermes)                          │    │   │
│  │  │  2. Analyze what worked/didn't                          │    │   │
│  │  │  3. Update strategy skill if successful                 │    │   │
│  │  │  4. Log to trade journal                               │    │   │
│  │  └───────────────────────────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Complete Data Flow

```
User: "Buy BONK, sentiment looks bullish"
         │
         ▼
┌────────────────────────────────┐
│  HERMES CORE AGENT                │
│  1. Analyze user request        │
│  2. Fetch CoinGecko price    │
│  3. Fetch DexScreener liquidity│
│  4. Fetch Twitter sentiment │
│  5. Fetch cluster analysis  │
│  6. Make decision          │
└────────────────────────────────┘
         │
         ▼ (DEX Spot → R3 Auto-route)
┌────────────────────────────────┐
│  DEX_SWAP Tool (Hermes)          │
│  1. Get quote (Jupiter API) │
│  2. Sign with agent wallet │
│  3. Submit transaction │
│  4. Monitor confirm    │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  JUPITER DEX (Solana)           │
│  Execute swap on-chain        │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  LEARNING (Hermes Memory)        │
│  Save trade analysis       │
│  Update strategy       │
│  Log to journal      │
└────────────────────────────────┘
```

---

## Part 22: Testing Pipeline (Complete)

```
TESTING PHASE 1: Paper Simulation
├── Goal: Prove strategy works in virtual
├── Environment: NOFX testnet / Hyperliquid testnet
├── Target: 5x hit $100,000
└── Verify: Consistent results across 10 runs

TESTING PHASE 2: DEX Devnet
├── Goal: Test real DEX execution
├── Environment: Solana devnet (Raydium/Jupiter)
├── Target: Execute 10 successful swaps
└── Verify: Transactions confirm

TESTING PHASE 3: Small Real Money
├── Goal: First real trades
├── Environment: Solana mainnet
├── Amount: $10-100
└── Verify: Full pipeline works

TESTING PHASE 4: Scale Up
├── Goal: Grow from $10 to $100,000
├── Strategy: Proven in phases 1-3
└── Risk: Maximum 5% of portfolio per trade

SUCCESS CRITERIA:
- ✅ 5x hit $100k in paper
- ✅ 10 successful devnet swaps
- ✅ First real money trade executed
- ✅ Learning system captures trade data
```

---

## Part 23: Social Signal Agent System (Complete)

### Overview

The Social Signal Agent System enables the AI to:
1. **Monitor** social platforms (Twitter, Telegram, Discord)
2. **Detect** signals (mentions, news, sentiment)
3. **Route** signals to Hermes Core for decision
4. **Output** to dual channels (OWN group + PUBLIC channel)

### Social Signal Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SOCIAL SIGNAL AGENT SYSTEM                                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐           │
│  │                           ORCHESTRATOR (Hermes Core - Port 8643)                                      │           │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────────────────┐           │           │
│  │  │  • Receives ALL signals from social agents                                 │           │           │
│  │  │  • Makes trading decisions (buy/sell/hold)                               │           │           │
│  │  │  • Routes to appropriate executor (perp→NOFX, DEX→Hermes)               │           │           │
│  │  │  • Executes trades and monitors positions                                │           │           │
│  │  │  • Learning: saves analysis to memory after each trade                  │           │           │
│  │  └──────────────────────────────────────────────────────────────────────────────────────────────┘           │
│  └───────────────────────────────────────────────────────────────────────────────────────────────────────┘           │
│                                              ▲                                                             │
│                                              │ Signals & Alerts                                              │
│                                              │                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐           │
│  │                                    SOCIAL AGENTS (3 Parallel)                                      │           │
│  │                                                                                              │           │
│  │  ┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐ ┌──────────────────┐  │           │
│  │  │         TWITTER AGENT              │ │       TELEGRAM AGENT               │ │  DISCORD AGENT  │  │           │
│  │  ├───────────────────────────────┤ ├───────────────────────────────┤ ├────────────────┤  │           │
│  │  │ Tool: twitter_follow_tool │ │ Tool: telegram_join_tool  │ │Tool: discord_join│  │           │
│  │  │ Library: twikit (FREE) │ │ Library: python-telegram-bot│ │Library: discord.py│  │           │
│  │  ├───────────────────────────────┤ ├───────────────────────────────┤ ├────────────────┤  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • Track coin accounts   │ │ • Join coin channels   │ │• Join servers  │  │           │
│  │  │   e.g., @PumpFun   │ │   e.g., @wif_sol   │ │• Monitor chats│  │           │
│  │  │   e.g., @elonmusk │ │   e.g., Bonk      │ │• Detect tokens│  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • Monitor KOL accounts│ │ • Monitor channels    │ │• Signal       │  │           │
│  │  │   e.g., @cryptorec│ │ • Detect news      │ │               │  │           │
│  │  │   e.g., @santi   │ │ • Alert main     │ │• Alert main   │  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • Detect $CASHTAG   │ │ • Forward to orch  │ │• Forward to orch│  │           │
│  │  │   e.g., $BONK   │ │                          │ │               │  │           │
│  │  │   e.g., $WIF   │ │                          │ │               │  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • Sentiment analysis │ │                          │ │               │  │           │
│  │  │   Score: -1 to +1 │ │                          │ │               │  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • KOL tracking   │ │                          │ │               │  │           │
│  │  │   Whale movements│ │                          │ │               │  │           │
│  │  │                          │ │                          │ │               │  │           │
│  │  │ • FREE (twikit) │ │ • Bot with API key│ │• Bot with API│  │           │
│  │  │   No API key!    │ │                          │ │               │  │           │
│  │  └──────────────────────────────────────┘ └──────────────────────────────────────┘ └────────────────┘  │           │
│  │                   │                           │                           │                                 │           │
│  └───────────────────┼───────────────────┼───────────────────┼─────────────────────────────────┘           │
│                      │                           │                           │                                             │
└──────────────────────┼───────────────────┼───────────────────┼─────────────────────────────────────────────┘
                       │                           │                           │
                       │                           │          ┌────────────────┴────────────────┐
                       │                           │          │    OUTPUT CHANNELS     │
                       │                           │          ├─────────────────────┤
                       ▼                           ▼          │
┌─────────────────────────────────────────┐ ┌─────────────┐ │   OWN TRADING GROUP    │
│          SIGNAL ROUTING                 │ │ PUBLIC SIGNAL CH   │
│  ┌───────────────────────┐   │ │          │ │ (Telegram)          │
│  │  Signal Priority  │   │ │          │ ├─────────────────────┤
│  │  • High: KOL    │   │ │          │ │• Execute trades    │
│  │    mentions     │   │ │          │ │• Position updates │
│  │  • Medium:     │   │ │          │ │• Confidential    │
│  │    volume spike│   │ │          │ │• Full control   │
│  │  • Low:      │   ��� │          │ ├─────────────────────┤
│  │    mentions   │   │ │          │ │PUBLIC SIGNAL CH   │
│  │             │   │ │          │ │(Telegram)          │
│  │  Route to:     │   │ │          │ ├─────────────────────┤
│  │  • Hermes    │   │ │          │ │• Share signals   │
│  │    Orchestr  │   │ │          │ │• Educational    │
│  │             │   │ │          │ │• Community     │
│  │  • Telegram │   │ │          │ │• Build audience│
│  │    group    │   │ │          │ │• Revenue pot.  │
│  └───────────────┘   │ │          │ └─────────────────────┘
└──────────────────────┼─────────────┼────┘
                     │          │
                     ▼          ▼
           ┌──────────────┐ ┌──────────────┐
           │ Hermes Core  │ │ Telegram   │
           │ Orchestr.  │ │ Bot       │
           └──────────────┘ └──────────────┘
```

### Social Agent Specifications

#### Twitter Agent (via Twikit - FREE!)

| Feature | Details |
|---------|---------|
| **Library** | twikit (4.2k stars on GitHub) |
| **Cost** | FREE - no API key needed! |
| **Features** | Search, post, user tweets, DMs |
| **Setup** | Login with username/password |

**Twitter Agent Tasks:**

```python
# Track specific coin/cashtag
async def track_cashtag(cashtag: str):
    # Search tweets with $CASHTAG
    tweets = await client.search(cashtag)
    # Filter by engagement
    # Score sentiment
    # Alert if high activity

# Monitor KOL (Key Opinion Leader)
async def monitor_kol(username: str):
    # Get user tweets
    # Detect buy/sell signals
    # Alert on position changes
```

#### Telegram Agent

| Feature | Details |
|---------|---------|
| **Library** | python-telegram-bot |
| **Cost** | Bot token only (free) |
| **Features** | Join channels, read messages, send |

**Telegram Agent Tasks:**

```python
# Join coin channel
async def join_channel(channel_username: str):
    # Request to join
    # Wait for approval
    # Begin monitoring

# Monitor for signals
async def monitor_channel():
    # Read new messages
    # Detect coin mentions
    # Forward to orchestrator
```

#### Discord Agent

| Feature | Details |
|---------|---------|
| **Library** | discord.py |
| **Cost** | Bot token (free) |
| **Features** | Join servers, read messages |

### Signal Output Channels (Dual)

#### OWN Trading Group (Private Telegram)

| Feature | Details |
|---------|---------|
| **Purpose** | Execute trades, position updates |
| **Access** | Private - only you |
| **Features** | Full trade control |

**Messages:**
- Buy signal executed
- Sell signal executed
- Position opened/closed
- Stop loss triggered
- Take profit triggered
- Daily P&L summary

#### PUBLIC Signal Channel (Telegram)

| Feature | Details |
|---------|---------|
| **Purpose** | Share signals, build community |
| **Access** | Public - invite link |
| **Features** | Revenue potential |

**Messages:**
- Coin name + entry price
- Target price
- Confidence score
- Brief rationale
- Educational content

### Signal Flow Diagram

```
NEW COIN DETECTED (from any social)
         │
         ▼
┌────────────────────────────────┐
│  SOCIAL AGENT RECEIVES            │
│  1. Twitter: $BONK mentioned  │
│  2. Telegram: "BUY BONK"    │
│  3. Discord: trending       │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  SIGNAL VALIDATION              │
│  • Check sentiment score      │
│  • Check volume spike     │
│  • Check KOL mention     │
│  • Pass/Fail threshold  │
└────────────────────────────────┘
         │
         ▼ (Pass)
┌────────────────────────────────┐
│  ROUTE TO ORCHESTRATOR      │
│  Hermes receives signal    │
│  with:                    │
│  • coin_name          │
│  • signal_type        │
│  • source           │
│  • confidence       │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  HERMES CORE DECISION         │
│  LLM analyzes:              │
│  • Price data           │
│  • Liquidity          │
│  • Risk assessment    │
│  • Make decision:         │
│    BUY / SELL / HOLD   │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  EXECUTE + ALERT              │
│                             │
│  IF BUY:                    │
│  • Execute DEX swap       │
│  • Alert OWN group      │
│  • Log to memory     │
│                             │
│  IF SIGNAL ONLY:              │
│  • Alert PUBLIC channel  │
│  • Wait for approval    │
└────────────────────────────────┘
```

### Configuration

```yaml
# Social Signal Configuration
social:
  twitter:
    enabled: true
    library: twikit  # FREE!
    track_coins:
      - $BONK
      - $WIF
      - $MEW
      - $POPCAT
    track_kols:
      - cryptorec
      - santi
      - elonmusk
  
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}
    join_channels:
      - bonk_sol
      - wif_sol
  
  discord:
    enabled: true
    bot_token: ${DISCORD_BOT_TOKEN}
    join_servers:
      - memecoin_trading

# Signal Output
signals:
  own_group_id: ${OWN_TELEGRAM_GROUP_ID}
  public_channel_id: ${PUBLIC_CHANNEL_ID}
  
  # Autonomous settings
  max_position_size: 0.1 SOL
  max_daily_trades: 5
  require_approval_over: 1.0 SOL
```

### Implementation Priority

| Priority | Agent | Status |
|----------|-------|--------|
| 1 | Telegram (already integrated) | Use existing |
| 2 | Twitter via Twikit | NEW tool - FREE |
| 3 | Telegram channel joiner | NEW tool |
| 4 | Discord joiner | NEW tool |
| 5 | Signal routing | NEW |
| 6 | Dual output | Configure |

---

## Part 25: Wallet Security Architecture (Complete)

### Overview

Wallet security implements the **2-Wallet Pattern** with safety limits, following the Hyperliquid security model and best practices from solana-agent-kit, AgentDex, and Nexgent.

### 2-Wallet Pattern

```
┌────────────────────────────────────────────────────────────────┐
│                   2-WALLET PATTERN SECURITY                   │
├────────────────────────────────────────────────────────────────┤
│                                                          │
│  MAIN WALLET (Funds)                                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Address: ${SOLANA_MAIN_WALLET}                     │   │
│  │ Balance: Holds trading budget                     │   │
│  │ Purpose: Fund agent wallet when needed          │   │
│  │ NEVER signs transactions                      │   │
│  │ NEVER exposed to code/API                  │   │
│  └────────────────────────────────────────────────────┘   │
│                         ▲                                │
│         Fund when needed │                                │
│                         │ Transfer SOL                  │
│                         ▼                                │
│  AGENT WALLET (Sign Only)                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Private Key: ${SOLANA_AGENT_KEY} (env, encrypted)  │   │
│  │ Balance: MAX 0.1 SOL (capped)                    │   │
│  │ Purpose: Sign transactions ONLY                 │   │
│  │ If compromised: minimal loss                 │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Security Configuration

```yaml
# Wallet Security Configuration
wallet:
  # 2-WALLET PATTERN
  agent_wallet:
    private_key_env: SOLANA_AGENT_PRIVATE_KEY
    max_balance: 0.1 SOL
    
  main_wallet:
    address_env: SOLANA_MAIN_WALLET
    
  # SAFETY LIMITS (from AgentDex/Nexgent research)
  limits:
    max_trade_sol: 0.1 SOL           # Max per trade
    max_daily_trades: 5              # Max trades per day
    max_slippage_bps: 300            # 3% slippage max
    max_price_impact_bps: 500        # 5% price impact max
    require_approval_over: 1.0 SOL   # Approval needed for large trades
    
  # MODES
  modes:
    simulation: true                 # Test first
    live_trading: false              # Enable after proven
```

### Security Measures (Research-Based)

| Measure | Source | Implementation |
|---------|--------|----------------|
| **max_trade_sol** | AgentDex | Hard cap per trade |
| **max_slippage_bps** | AgentDex | Reject high slippage |
| **max_price_impact_bps** | Nexgent | Reject large impact |
| **Transaction simulation** | AgentDex | Simulate before broadcast |
| **Fail-closed model** | AgentDex | Reject anything risky |
| **Permission layers** | sol-cli | Separate canSwap/canSend |
| **Token allowlist** | sol-cli | Only trade approved tokens |

### Reference Implementation Patterns

| Tool | Pattern | Security |
|------|---------|----------|
| **solana-agent-kit** | KeypairWallet | Encrypted key storage |
| **AgentDex** | Keypair + config | Safety limits |
| **sol-cli** | Key file (chmod 600) | Permissions layers |
| **Nexgent** | Simulation mode | Live/sim separate |

---

## Part 26: Complete Agent Summary

### All Agents (5 + Orchestrator)

```
AGENT ARCHITECTURE:

         ┌─────────────────────────────────────────┐
         │   HERMES CORE (Orchestrator)             │
         │   Port 8643 - Single AI Brain          │
         └─────────────────────────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
┌─────────┐   ┌─────────┐   ┌──────────────────┐
│ NOFX    │   │  DEX   │   │ SOCIAL AGENTS     │
│ Trader  │   │ Swap   │   │ (4 Parallel)      │
└─────────┘   └─────────┘   └──────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Twitter    │     │  Telegram   │     │  Discord    │
│   Agent     │     │   Agent     │     │   Agent     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│• Track      │     │• Join      │     │• Join       │
│ $CASHTAG   │     │ channels  │     │ servers    │
│• Monitor   │     │• Monitor │     │• Monitor   │
│ KOLs       │     │ chats   │     │ chats     │
│• Detect    │     │• Detect │     │• Detect    │
│ $COIN     │     │ mentions│     │ mentions  │
│• Sentiment │     │• Signal │     │• Signal    │
│ (twikit!) │     │• Forward│     │• Forward  │
└──────────────┘     └──────────────┘     └──────────────┘
         │                        │
         │              ┌─────────┴─────────┐
         │              │                  │
         │              ▼                  ▼
         │      ┌──────────────┐  ┌──────────────┐
         │      │   NEWS     │  │   OUTPUT   │
         │      │   Agent    │  │   CHANNELS │
         │      ├──────────────┤  ├──────────────┤
         │      │• RSS feeds │  │• OWN group │
         │      │• News API │  │  (private)│
         │      │• Announce│  │• PUBLIC   │
         │      │• Signal  │  │  channel  │
         │      └──────────────┘  │  +TIPJAR │
         │              └──────────────────┘
         │
         └──────────► Social Signal Routing
```

### Agent Details

| Agent | Platform | Library | Purpose |
|-------|----------|---------|---------|
| **Twitter Agent** | Twitter | twikit (FREE!) | Track $CASHTAG, KOLs, sentiment |
| **Telegram Agent** | Telegram | python-telegram-bot | Join channels, monitor, signal |
| **Discord Agent** | Discord | discord.py | Join servers, monitor, signal |
| **News Agent** | RSS/News | feedparser | Monitor news, announcements |
| **Hermes Orchestrator** | All | Hermes Core | Make decisions, execute |

### News Agent Specification (NEW - Q7)

```
┌────────────────────────────────────────────────────────────────┐
│                      NEWS AGENT                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Function: Monitor news sources for coin-related announcements │
│                                                                │
│  Sources:                                                      │
│  • RSS feeds (CoinGecko, major news)                          │
│  • News APIs (Birdeye, DexScreener news)                       │
│  • Official announcements (project blogs)                    │
│                                                                │
│  Signals Detected:                                             │
│  • New token launch                                           │
│  • Partnership announcements                                │
│  • Token burns                                               │
│  • Major updates                                              │
│  • Regulatory news                                           │
│                                                                │
│  Integration:                                                 │
│  • Separate dedicated agent (not combined)                   │
│  • Forward signals to Hermes orchestrator                       │
│  • Alert both OWN group and PUBLIC channel                      │
└────────────────────────────────────────────────────────────────┘
```

### Public Signal Channel with Revenue (NEW - R1)

```
┌────────���───────────────────────────────────────────────────────┐
│    PUBLIC SIGNAL CHANNEL + REVENUE      │
├────────────────────────────────────┤
│                                     │
│  Platform: Telegram (Q6)          │
│                                     │
│  Contents:                         │
│  • Coin name + entry price          │
│  • Target price                   │
│  • Confidence score               │
│  • Brief rationale                │
│  • Educational content           │
│                                     │
│  Revenue:                        │
│  • Tip jar: ${TIP_JAR_WALLET}    │
│  • Optional: supporter-only      │
│  • Community building           │
│  • Trust-based tips              │
│                                     │
│  Security:                     │
│  • Signals are educational      │
│  • Not financial advice        │
│  • Trade at your own risk        │
└────────────────────────────────────┘
```

---

## Part 24: Complete System Architecture (v3.0 - Final)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MEMETRADER COMPLETE SYSTEM (v3.0)                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐               │
│  │                              HERMES CORE AGENT (Port 8643)                                    │               │
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐               │               │
│  │  │                                    AI BRAIN                                            │               │               │
│  │  │  • Single LLM for ALL trading decisions                                    │               │               │
│  │  │  • Memory: learns from EVERY trade (persistent)                   │               │               │
│  │  │  • Skills: auto-improving strategies                         │               │               │
│  │  │  • Context: 60k+ tokens, efficient compression           │               │               │
│  │  └───────────────────────────────────────────────────────────────────────────────────────────────┘               │               │
│  │                                                │                                                 │               │
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐               │               │
│  │  │                              MULTI-AGENT SYSTEM                                         │               │               │
│  │  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │               │               │
│  │  │  │      CRONJOB         │  │      DELEGATE         │  │    BACKGROUND       │  │               │               │
│  │  │  │  Agent              │  │  Agent              │  │  Agent              │  │               │               │
│  │  │  ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤  │               │               │
│  │  │  │ • Scan every 5 min   │  │ • Analyze 10 coins │  │ • Execute swap   │  │               │               │
│  │  │  │ • Check positions   │  │   parallel         │  │ • Monitor confirm│  │               │               │
│  │  │  │ • Daily report  │  │ • Aggregate     │  │ • Update on     │  │               │               │
│  │  │  │ • Position check│  │   results       │  │   complete     │  │               │               │
│  │  │  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │               │               │
│  │  └───────────────────────────────────────────────────────────────────────────────────────────────┘               │               │
│  │                                                │                                                 │               │
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐               │               │
│  │  │                                    60+ TOOLS                                             │               │               │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │               │               │
│  │  │  │ nofx_trade │ │ dex_swap   │ │ coingecko  │ │ twikit    │ │  memory   │ │ delegate │ │               │               │
│  │  │  │  (perp)   │ │  (NEW)   │ │  price   │ │ (FREE!)  │ │  learn   │ │ (parallel)│ │               │               │
│  │  │  │    ↓     │ │    ↓     │ │    ↓     │ │    ↓     │ │    ↓     │ │   ↓      │ │               │               │
│  │  │  │  NOFX    │ │ Jupiter  │ │ CoinGecko│ │ Twitter │ │ Memory DB│ │ Subagents│ │               │               │
│  │  │  │  perps   │ │  DEX    │ │ prices  │ │ scrapes │ │ learnings│ │ workers │ │               │               │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │               │               │
│  │  └───────────────────────────────────────────────────────────────────────────────────────────────┘               │               │
│  └───────────────────────────────────────────────────────────────────────────────────────────────────────┘               │
│                                              │                                                                       │
│                                              │ AUTO-ROUTING (R3)                                                    │
│                                              ▼                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ ┌───────────────────────────────────────────────┐                       │
│  │              NOFX TRADING BACKEND                    │ │       DEX WALLETS (Hermes)           │                       │
│  │  ┌───────────────────────────────────────────┐ │ │  ┌──────────────────────────────┐  │                       │
│  │  │  Perps/Futures:                       │ │ │  │ 2-WALLET PATTERN       │  │                       │
│  │  │  • OKX, Bybit, Gate, Hyperliquid │ │ │  │                      │  │                       │
│  │  │  • Lighter, Aster, KuCoin     │ │ │  │ Agent Wallet (signing) │  │                       │
│  │  │  • Grid Trading Engine     │ │ │  │ • Balance: ~0 SOL    │  │                       │
│  │  │  • Position Management│ │ │  │ • For signing TX   │  │                       │
│  │  │  • Risk Controls │ │ │  │                      │  │                       │
│  │  │  • NOFX testnet │ │ │  Main Wallet (funds)│  │                       │
│  │  │                │ │ │  • Holds funds     │  │                       │
│  │  │  DEX SPOT (via Hermes):    │ │ │  • Never expose  │  │                       │
│  │  │  • Jupiter (aggregator)│ │ │  • For funding    │  │                       │
│  │  │  • Raydium         │ │ │  └──────────────────────────────┘  │                       │
│  │  │  • Cetus (SUI)      │ │ └───────────────────────────────────────────────┘                       │
│  │  │                │ │                                                                     │
│  │  │  DEX Integration:        │ │  Solana mainnet: Jupiter/Raydium                 │
│  │  │  • Devnet first    │ │  SUI testnet: Cetus                           │
│  │  │  • Test 10 trades│ │  All via Hermes dex_swap tool              │
│  │  │  • Then mainnet │ │                                                                     │
│  │  └───────────────────────────────────────────┘ │                                                                     │
│  └───────────────────────────────────────────────────────────────────────┘                                │
│                                              │                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐                                              │
│  │              DATA SOURCES (All Free/Low Cost)          │                                              │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐┌──────────────┐ ┌──────────────┐ ┌────────────┐│           │
│  │  │  CoinGecko │ │ DexScreener│ │  Birdeye  ││  Helius   │ │  NofxOS   │ │  Twikit  ││           │
│  │  │  Prices   │ │  Token    │ │  Solana  ││  RPC     │ │   OI      │ │  FREE!   ││           │
│  │  │ +Market   │ │ Analytics│ │   Data   ││ +Webhooks│ │ +AI500   │ │ Twitter  ││           │
│  │  │  Free    │ │  Free    │ │  Free    ││  Free tier│ │  Free    │ │ No API   ││           │
│  │  │ (30/min) │ │ (10k/mo) │ │  (free)  ││         │ │         │ │  key!   ││           │
│  │  └──────────────┘ └──────────────┘ └──────���───────┘└──────────────┘ └──────────────┘ └────────────┘│           │
│  └───────────────────────────────────────────────────────────────────────┘                                              │
│                                                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐                                              │
│  │              SOCIAL SIGNAL AGENTS (3 Parallel)                        │                                              │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │                                              │
│  │  │  Twitter  │ │ Telegram  │ │  Discord  │                    │                                              │
│  │  │  Agent   │ │  Agent    │ │  Agent    │                    │                                              │
│  │  ├──────────────┤ ├──────────────┤ ├──────────────┤                    │                                              │
│  │  │ • Track   │ │ • Join    │ │ • Join     │                    │                                              │
│  │  │   $COIN  │ │  channels│ │  servers  │                    │                                              │
│  │  │ • Monitor│ │ • Monitor│ │ • Monitor│                    │                                              │
│  │  │   KOLs  │ │  chats  │ │  chats   │                    │                                              │
│  │  │ • Detect│ │ • Detect│ │ • Detect │                    │                                              │
│  │  │   $TAG  │ │  mentions│ │  mentions│                    │                                              │
│  │  │ • Sentiment│ │ • Signal│ │ • Signal │                    │                                              │
│  │  │   (twikit│ │ • Forward│ │ • Forward │                    │                                              │
│  │  │   FREE!)│ │   to orch│ │   to orch│                    │                                              │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                    │                                              │
│  └───────────────────────────────────────────────────────────────────────┘                                              │
│                                                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐                                              │
│  │              OUTPUT CHANNELS (Dual)                        │                                              │
│  │  ┌──────────────────────────────────────┐ ┌──────────────────────────────────────┐  │           │
│  │  │         OWN TRADING GROUP              │ │      PUBLIC SIGNAL CHANNEL           │  │           │
│  │  │      (Private Telegram)             │ │        (Telegram)              │  │           │
│  │  ├──────────────────────────────┬─────┤ ├──────────────────────────────┬───────┤  │           │
│  │  │  • Execute trades           │ Signal│ │  • Share signals             │Signal │  │           │
│  │  │  • Position updates      │→Orch │ │  • Educational content    │→Public│  │           │
│  │  │  • Stop loss alerts      │      │ │  • Build community         │      │  │           │
│  │  │  • Take profit alerts    │      │ │  • Revenue potential       │      │  │           │
│  │  │  • Full control        │      │ │                          │      │  │           │
│  │  └──────────────────────────────┴─────┘ └──────────────────────────────┴───────┘  │           │
│  └───────────────────────────────────────────────────────────────────────┘                                              │
│                                                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐                                              │
│  │              LEARNING SYSTEM                        │                                              │
│  │  ┌───────────────────────────────────────────────────────────────┐    │                                              │
│  │  │  After EVERY trade:                                          │    │                                              │
│  │  │  1. Save trade to Hermes memory                         │    │                                              │
│  │  │  2. Analyze: What worked, what didn't             │    │                                              │
│  │  │  3. Update strategy skill if successful          │    │                                              │
│  │  │  4. Log to trade journal                      │    │                                              │
│  │  │  5. Self-evolve: adapt strategy based on results    │    │                                              │
│  │  └───────────────────────────────────────────────────────────────┘    │                                              │
│  └───────────────────────────────────────────────────────────────────────┘                                              │
│                                                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Complete Trading Flow

```
USER INPUT: "What's the sentiment on BONK?"
         │
         ▼
┌─────────────────────────────────────┐
│     HERMES CORE AGENT                 │
│  1. Receive user message            │
│  2. Check memory context          │
│  3. Determine tools needed      │
└─────────────────────────────────────┘
         │
         ▼ (needs social data)
┌─────────────────────────────────────┐
│   SOCIAL SIGNAL AGENTS              │
│  • Twitter: check $BONK           │
│  • Get recent tweets             │
│  • Calculate sentiment score     │
│  • Return to orchestrator       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   HERMES LLM DECISION              │
│  • Analyze sentiment            │
│  • Check price/liquidity    │
│  • Generate response         │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   RESPONSE TO USER                 │
│  "Bullish sentiment (0.75)..."
└─────────────────────────────────────┘


USER: "BUY 0.1 SOL BONK"
         │
         ▼
┌─────────────────────────────────────┐
│     HERMES CORE AGENT                 │
│  1. Parse: BUY action             │
│  2. Route: DEX spot (not perp)   │
│  3. Check wallet balance       │
└─────────────────────────────────────┘
         │
         ▼ (DEX Spot)
┌─────────────────────────────────────┐
│     DEX_SWAP TOOL                  │
│  1. Get quote (Jupiter API)  │
│  2. Calculate output         │
│  3. Check slippage         │
│  4. Sign with agent wallet  │
│  5. Submit transaction    │
│  6. Monitor confirm     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   EXECUTE + LOG                    │
│  • Execute swap on DEX          │
│  • Alert OWN group           │
│  • Save to memory          │
│  • Update trade journal  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   LEARNING (After trade)            │
│  • Analyze outcome          │
│  • Save lesson to memory │
│  • Update strategy      │
└─────────────────────────────────────┘
```

### Cost Summary (Monthly)

| Component | Cost | Status |
|-----------|------|--------|
| Hermes (self-hosted) | FREE | ✅ |
| NOFX (self-hosted) | FREE | ✅ |
| CoinGecko | FREE (30/min) | ✅ |
| DexScreener | FREE (10k/mo) | ✅ |
| Birdeye | FREE | ✅ |
| Helius | FREE tier | ✅ |
| Twitter (twikit) | FREE! | ✅ |
| Telegram Bot | FREE | ✅ |
| Discord Bot | FREE | ✅ |
| **Total** | **$0** | ✅ |

---

*Document Version: 4.0*
*Status: Design Complete - All Brainstorming Decisions Documented*
*Ready for Implementation Planning*