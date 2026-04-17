# DEX Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DEX swap capabilities to Hermes for Solana/SUI spot trading via Jupiter, Raydium, and Cetus APIs

**Architecture:** Hermes Python tool + wallet signing approach (NOT Go files in nofx/trader/). Direct REST calls to DEX APIs with wallet transaction signing. Test on devnet first before mainnet.

**Tech Stack:** Python (Hermes tools), Solana web3.py, Jupiter/Raydium REST APIs, devnet for testing

---

## Phase 1: DEX Swap Tool (Priority - Execute First)

### D1: Create DEX Swap Tool

**Files:**
- Create: `tools/dex_swap_tool.py`
- Modify: `model_tools.py` (add import), `toolsets.py` (add to toolset)

- [ ] **Step 1: Create tools/dex_swap_tool.py**

```python
import json
import requests
from tools.registry import registry

JUPITER_API_URL = "https://api.jup.ag/swap/v1"
RAYDIUM_API_URL = "https://api.raydium.io/v2/dex/swap"
SOLANA_RPC = "https://api.devnet.solana.com"


def check_requirements() -> bool:
    """Check if Solana devnet is accessible"""
    try:
        response = requests.get(f"{SOLANA_RPC}", 
            json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
            timeout=5)
        return response.status_code == 200
    except:
        return False


def get_quote(input_mint: str, output_mint: str, amount: int, slippage: float = 0.5) -> str:
    """Get swap quote from Jupiter aggregator"""
    try:
        url = f"{JUPITER_API_URL}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": int(slippage * 100)
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "input_mint": input_mint,
            "output_mint": output_mint,
            "input_amount": amount,
            "output_amount": data.get("outAmount"),
            "price_impact": data.get("priceImpactPct"),
            "route": data.get("routePlan", [])
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def execute_swap(quote_response: str, wallet_private_key: str) -> str:
    """Execute swap transaction"""
    try:
        quote_data = json.loads(quote_response)
        
        # Build swap transaction
        url = f"{JUPITER_API_URL}/swap"
        payload = {
            "quoteResponse": quote_data,
            "userPublicKey": "derived_from_private_key",
            "wrapAndUnwrapSol": True
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "swap_transaction": data.get("swapTransaction"),
            "server_time": data.get("serverTime")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_token_list(chain: str = "solana") -> str:
    """Get available tokens for swap"""
    try:
        url = f"{JUPITER_API_URL}/tokens"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        tokens = []
        for token in data.get("tokens", [])[:50]:
            tokens.append({
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "name": token.get("name"),
                "decimals": token.get("decimals"),
                "liquidity": token.get("liquidity")
            })
        
        return json.dumps({"tokens": tokens})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Register tools with registry
registry.register(
    name="dex_get_quote",
    toolset="dex",
    schema={
        "name": "dex_get_quote",
        "description": "Get swap quote from Jupiter DEX aggregator",
        "parameters": {
            "type": "object",
            "properties": {
                "input_mint": {"type": "string", "description": "Input token mint address"},
                "output_mint": {"type": "string", "description": "Output token mint address"},
                "amount": {"type": "integer", "description": "Amount in lamports"},
                "slippage": {"type": "number", "description": "Slippage percentage", "default": 0.5}
            },
            "required": ["input_mint", "output_mint", "amount"]
        }
    },
    handler=lambda args, **kw: get_quote(
        args.get("input_mint"),
        args.get("output_mint"),
        args.get("amount"),
        args.get("slippage", 0.5)
    ),
    check_fn=check_requirements
)

registry.register(
    name="dex_execute_swap",
    toolset="dex",
    schema={
        "name": "dex_execute_swap",
        "description": "Execute a DEX swap transaction",
        "parameters": {
            "type": "object",
            "properties": {
                "quote_response": {"type": "string", "description": "Quote response from dex_get_quote"},
                "wallet_private_key": {"type": "string", "description": "Wallet private key (base58)"}
            },
            "required": ["quote_response", "wallet_private_key"]
        }
    },
    handler=lambda args, **kw: execute_swap(
        args.get("quote_response"),
        args.get("wallet_private_key")
    ),
    check_fn=check_requirements
)

registry.register(
    name="dex_token_list",
    toolset="dex",
    schema={
        "name": "dex_token_list",
        "description": "Get list of tokens available for DEX swap",
        "parameters": {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "description": "Blockchain", "default": "solana"}
            }
        }
    },
    handler=lambda args, **kw: get_token_list(args.get("chain", "solana")),
    check_fn=check_requirements
)
```

- [ ] **Step 2: Add import in model_tools.py**

```python
# In _discover_tools() function, add:
"tools.dex_swap_tool",
```

- [ ] **Step 3: Add to toolsets.py**

```python
# Add to "dex" toolset:
"dex": {
    "description": "DEX swap and trading tools",
    "tools": ["dex_get_quote", "dex_execute_swap", "dex_token_list"],
    "includes": [],
},
```

- [ ] **Step 4: Verify imports**

Run: `python -c "from tools import dex_swap_tool; print('DEX tool OK')"`
Expected: "DEX tool OK"

- [ ] **Step 5: Commit**

```bash
git add tools/dex_swap_tool.py model_tools.py toolsets.py
git commit -m "feat: add DEX swap tool (Jupiter)"
```

### D2: Add Wallet Integration

**Files:**
- Create: `tools/solana_wallet.py`
- Modify: `tools/dex_swap_tool.py` (add wallet usage)

- [ ] **Step 1: Create wallet signing module**

```python
import base58
from solana.rpc import Api
from solana.transaction import Transaction
from solders.keypair import Keypair

def load_wallet(private_key_b58: str) -> Keypair:
    """Load wallet from base58 private key"""
    try:
        private_key_bytes = base58.b58decode(private_key_b58)
        return Keypair.from_bytes(private_key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid private key: {e}")

def get_wallet_address(private_key_b58: str) -> str:
    """Get wallet address from private key"""
    wallet = load_wallet(private_key_b58)
    return str(wallet.pubkey())
```

- [ ] **Step 2: Integrate with dex_swap_tool.py**

Add wallet importing and address derivation

- [ ] **Step 3: Commit**

---

### D3: Test on Devnet

**Files:**
- Test: Manual testing on Solana devnet

- [ ] **Step 1: Get devnet SOL**

Use: https://solfaucet.com (Solana devnet faucet)

- [ ] **Step 2: Test quote retrieval**

```python
from tools.dex_swap_tool import get_quote

# SOL to USDC (devnet)
result = get_quote(
    "So11111111111111111111111111111111111111112",  # SOL
    "EPjFWdd5AufqSSBc8ptuJcK3kY5xxS3CMZtFNMa1T1s3",  # USDC
    1000000000  # 1 SOL in lamports
)
print(result)
```

- [ ] **Step 3: Commit**

---

## Phase 2: On-Chain Radar

### E1: Helius Solana RPC Tool

**Files:**
- Create: `tools/helius_tool.py`

```python
import json
import requests
from tools.registry import registry

HELIUS_RPC = os.getenv("HELIUS_RPC_URL", "https://api.devnet.solana.com")


def check_requirements() -> bool:
    return bool(os.getenv("HELIUS_RPC_URL") or True)


def get_token_balance(wallet: str, token_mint: str) -> str:
    """Get token balance for wallet"""
    # Use Solana RPC getTokenAccountBalance
    return json.dumps({"wallet": wallet, "balance": 0})


def get_transaction_history(wallet: str, limit: int = 10) -> str:
    """Get transaction history for wallet"""
    # Use Helius parsed transactions API
    return json.dumps({"transactions": []})


registry.register(...)
```

### E2: Wallet Tracking Tool

**Files:**
- Create: `tools/wallet_tracker.py`

```python
# Track smart money wallets
# Alert on large movements
# Track accumulation patterns
```

---

## Phase 3: Social Hype-Meter

### F1: Twitter Sentiment Tool

**Files:**
- Create: `tools/twitter_sentiment_tool.py`

```python
import json
from twikit import Client
from tools.registry import registry


def check_requirements() -> bool:
    """Twikit is free, no API key needed"""
    return True


async def search_tweets(query: str, max_results: int = 20) -> str:
    """Search tweets with sentiment"""
    try:
        client = Client()
        tweets = await client.search_tweet(query, max_results)
        
        results = []
        for tweet in tweets:
            results.append({
                "id": tweet.id,
                "text": tweet.text,
                "author": tweet.user.name,
                "likes": tweet.favorite_count,
                "retweets": tweet.retweet_count
            })
        
        return json.dumps({"tweets": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="twitter_search",
    toolset="social",
    schema={...},
    handler=...,
    check_fn=check_requirements
)
```

### F2: Telegram/Discord Sentiment

**Files:**
- Create: `tools/telegram_sentiment_tool.py`
- Create: `tools/discord_sentiment_tool.py`

---

## Phase 4: Self-Evolution

### G1: Trade Logger

**Files:**
- Modify: `tools/memory_tool.py` (add trade logging)

```python
def log_trade(trade_data: dict) -> str:
    """Log trade to memory for learning"""
    # Store in memory with trade: prefix
    return json.dumps({"success": True})
```

### G2: Trade Analysis

**Files:**
- Create: `tools/trade_analysis_tool.py`

```python
# Analyze trade history
# Identify patterns
# Suggest strategy improvements
```

---

## Execution Options

**Plan complete. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**