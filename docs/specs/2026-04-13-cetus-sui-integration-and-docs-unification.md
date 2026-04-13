---
title: "Cetus SUI Integration & Documents Unification"
date: 2026-04-13
author: MemeTrader
status: draft
---

# Design: Cetus SUI Integration & Documentation Unification

## Overview

Two-pronged project:
1. **Technical**: Integrate Cetus DEX (SUI blockchain) into NOFX trading system
2. **Documentation**: Unify fragmented docs into single source for Hermes + NOFX + MemeTrader

---

## Objective 1: Cetus DEX Integration

### Background

**Current state**: NOFX supports 9 exchange integrations:
- lighter, okx, kucoin, indodax, hyperliquid, gate, bybit, bitget, aster

**Target**: Add Cetus (SUI blockchain) as the 10th exchange

### Architecture

```
nofx/
├── trader/
│   ├── cetus/           # NEW - Cetus integration
│   │   ├── trader.go    # Main trader interface
│   │   ├── trader_orders.go
│   │   ├── trader_account.go
│   │   ├── trader_positions.go
│   │   ├── order_sync.go
│   │   └── integration_test.go
```

### Integration Pattern (Following Existing Exchanges)

Each exchange implements the same interface:

```go
type ExchangeTrader interface {
    // Trading operations
    PlaceOrder(ctx context.Context, order Order) (string, error)
    CancelOrder(ctx context.Context, orderID string) error
    ModifyOrder(ctx context.Context, orderID string, update OrderUpdate) error
    
    // Account operations
    GetAccount(ctx context.Context) (*Account, error)
    GetBalance(ctx context.Context, symbol string) (*Balance, error)
    
    // Position operations
    GetPositions(ctx context.Context) ([]Position, error)
    GetPosition(ctx context.Context, symbol string) (*Position, error)
}
```

### Cetus-Specific Implementation

| Component | Implementation |
|------------|----------------|
| API Library | Use Cetus SDK or direct HTTP |
| Authentication | Wallet + private key signing |
| Endpoints | REST API for orders, WebSocket for fills |
| Rate Limits | TBD from Cetus docs |
| Markets | Concentrated liquidity pools |

### Key Differences from Other Exchanges

- **SUI blockchain** - different from EVM/Solana
- **Concentrated liquidity** - similar to Uniswap V3
- **Wallet-based** - not API-key based
- **Program calls** - smart contract interaction

### Implementation Scope

| Phase | Tasks |
|-------|-------|
| 1 | Setup Cetus client, authentication |
| 2 | Implement trading interface |
| 3 | Implement account/position queries |
| 4 | Order sync mechanism |
| 5 | Integration tests |

---

## Objective 2: Documentation Unification

### Current State

| Location | Content | Quality |
|----------|---------|---------|
| `/docs/` (root) | Mixed | Outdated |
| `/website/docs/` | Website content | Current |
| `/nofx/docs/` | NOFX-specific | Moderate |
| `README.md` (root) | High-level overview | Current |
| `AGENTS.md` | Hermes Agent | Current |
| Various `*.md` files | Project-specific | Fragmented |

### Target Structure

```
docs/
├── memetrader/                    # Unified documentation
│   ├── index.md                   # Entry point
│   ├── architecture/
│   │   ├── overview.md           # System architecture
│   │   ├── hermes-agent.md        # Hermes details
│   │   ├── nofx.md               # NOFX details
│   │   └── integration.md        # How they connect
│   ├── integrations/
│   │   ├── exchanges/            # All exchange integrations
│   │   │   ├── okx.md
│   │   │   ├── bybit.md
│   │   │   └── cetus.md           # NEW
│   │   ├── dex.md               # DEX integrations
│   │   └── providers.md         # Data providers
│   ├── trading/
│   │   ├── strategies.md
│   │   ├── risk-management.md
│   │   └── debugging.md
│   ├── deployment/
│   │   ├── local.md
│   │   ├── docker.md
│   │   └── production.md
│   └── reference/
│       ├── cli-commands.md
│       ├── environment-variables.md
│       └── troubleshooting.md
```

### Migration Strategy

| Phase | Tasks |
|-------|-------|
| 1 | Create new structure |
| 2 | Move core docs from each system |
| 3 | Create cross-reference index |
| 4 | Archive outdated content |
| 5 | Update website to link to unified docs |

### Documentation Standards

- All new docs go into `docs/memetrader/`
- Website links to unified docs
- Each integration has its own doc
- Debugging guides for each exchange/DEX

---

## Success Criteria

### Technical
- [ ] Cetus integration compiles
- [ ] Can place test orders
- [ ] Account/position queries work
- [ ] Integration tests pass

### Documentation
- [ ] All systems documented in one location
- [ ] Cross-references functional
- [ ] Website updated to link to unified docs
- [ ] Archives marked/documented

---

## Timeline

| Phase | Estimated Effort |
|-------|------------------|
| Cetus client setup | 1-2 days |
| Trading interface | 2-3 days |
| Account/positions | 1-2 days |
| Order sync | 1-2 days |
| Docs restructure | 1-2 days |

---

## Communication Architecture: MCP, ACP & Agentic Methods

### Current Integration Methods

| Layer | Technology | Description | Location |
|-------|-----------|------------|----------|
| **Trading API** | REST HTTP | Direct trade execution | `tools/nofx_trading_tool.py` |
| **AI Providers** | MCP | Multi-provider LLM interface | `nofx/mcp/` |
| **ACP** | Agent Client Protocol | Hermes IDE integration | `acp_adapter/` |
| **Tool Protocol** | Hermes Registry | 60+ tools for AI | `tools/` |

### Data Flow

```
User (Telegram/Discord/etc.)
    ↓
Hermes Agent (Python, Port 8643)
    ↓ HTTP API (localhost:8080)
NOFX (Go trading backend)
    ↓
Exchanges (OKX, Bybit, etc.)
```

### MCP Implementation (NOFX)

NOFX includes MCP for multi-provider AI calls:
- `nofx/mcp/provider/claude.go` - Anthropic
- `nofx/mcp/provider/openai.go` - OpenAI
- `nofx/mcp/provider/deepseek.go` - DeepSeek
- `nofx/mcp/grok.go`, `gemini.go`, `kimi.go`, `qwen.go`
- Uses x402 payment protocol for AI credits

### ACP Implementation (Hermes)

ACP adapter exposes Hermes via Agent Client Protocol:
- VS Code, Zed, JetBrains integration
- `acp_adapter/server.py` - Main ACP server
- Session management, tool execution
- Full AI agent capabilities

### Trading Tools Available

```
nofx_portfolio    - Get portfolio holdings
nofx_positions  - Get open positions
nofx_strategies  - List/create strategies
nofx_account   - Get account info
nofx_exchanges   - List connected exchanges
nofx_trade     - Execute a trade
```

---

## Documentation Archive Marking

**Legacy docs decision**: Mark outdated as "legacy/{topic}.md" - not delete

```
docs/
├── memetrader/           # Current docs
├── legacy/              # Marked as outdated
│   ├── old-architecture.md
│   └── deprecated-features.md
└── archive/             # Very old, reference only
```

---

## Open Questions (Updated)

1. **Cetus API**: Need to explore Cetus SDK/documentation - what's available?
2. **Testnet**: Is Sui testnet accessible for testing?
3. **Wallet**: How will wallet credentials be managed in NOFX?
4. **Docs maintainers**: Who will maintain the unified docs going forward?