# MemeTrader Implementation Plan

**Generated using superpower skills (writing-plans) approach**

**Date:** April 17, 2026  
**Version:** 1.0  
**Based on:** 2026-04-13-memetrader-unified-design.md v9.0

## Overview

This implementation plan breaks down the MemeTrader unified system into bite-sized tasks (2-5 minutes each). Each task includes:
- Exact file paths
- Complete code examples where applicable
- Testing/verification steps
- Commit points

**Assumptions:**
- Implementer has zero context of the codebase
- Skilled developer but unfamiliar with Hermes/NOFX
- All changes are committed frequently
- TDD approach where possible

## Phase 1: Cleanup and Integration Setup

### A1: Remove Paper Trading from Hermes

**Goal:** Eliminate paper trading functionality as per design decision to use NOFX for all trading.

#### Task A1.1: Delete paper trading engine
- **File:** `/workspaces/Memetrader/tools/trading/paper_engine.py`
- **Action:** Delete the entire file
- **Verification:** Run `find /workspaces/Memetrader -name "*paper*" -type f` to confirm no paper files remain
- **Commit:** "Remove paper trading engine"

#### Task A1.2: Remove paper trading exports
- **File:** `/workspaces/Memetrader/tools/trading/__init__.py`
- **Action:** Remove all imports and exports related to paper trading
- **Before:**
```python
from .paper_engine import PaperTradingEngine
```
- **After:** (empty or other imports only)
- **Verification:** Run `python -c "from tools.trading import *"` to ensure no import errors
- **Commit:** "Remove paper trading imports"

#### Task A1.3: Remove paper trading API endpoints
- **File:** `/workspaces/Memetrader/gateway/fastapi_server.py`
- **Action:** Remove all `/api/trading/*` routes
- **Search for:** Routes containing "trading" or "paper"
- **Verification:** Start FastAPI server and confirm `/api/trading/*` endpoints return 404
- **Commit:** "Remove paper trading API endpoints"

### B1: NOFX Integration Setup

**Goal:** Disable NOFX internal AI and ensure Hermes can connect to NOFX.

#### Task B1.1: Disable NOFX internal AI calls
- **File:** `/workspaces/Memetrader/nofx/trader/auto_trader.go`
- **Action:** Comment out or remove MCP AI calls
- **Search for:** Lines containing "MCP", "AI", "claude", "deepseek", "qwen"
- **Before:**
```go
// AI decision making code
```
- **After:** (removed or commented)
- **Verification:** Check NOFX logs for absence of AI-related calls
- **Commit:** "Disable NOFX internal AI"

#### Task B1.2: Verify NOFX trading tool connection
- **File:** `/workspaces/Memetrader/tools/nofx_trading_tool.py`
- **Action:** Ensure the tool is properly registered and functional
- **Verification:** Run Hermes CLI and check if `nofx_trade` tool is available
- **Test:** Execute a simple NOFX command via Hermes
- **Commit:** "Verify NOFX tool integration"

## Phase 2: UI Integration (NOFX-UI)

**Goal:** Add `/hermes` page to NOFX-UI with Chat, Memory, Skills, Inspector tabs.

### C1: Create Hermes Page Component

#### Task C1.1: Create main Hermes page component
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage.tsx` (create new)
- **Content:**
```tsx
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ChatTab from './HermesPage/ChatTab';
import MemoryTab from './HermesPage/MemoryTab';
import SkillsTab from './HermesPage/SkillsTab';
import InspectorTab from './HermesPage/InspectorTab';

export default function HermesPage() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">AI Assistant</h1>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
          <TabsTrigger value="inspector">Inspector</TabsTrigger>
        </TabsList>
        
        <TabsContent value="chat">
          <ChatTab />
        </TabsContent>
        <TabsContent value="memory">
          <MemoryTab />
        </TabsContent>
        <TabsContent value="skills">
          <SkillsTab />
        </TabsContent>
        <TabsContent value="inspector">
          <InspectorTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```
- **Verification:** NOFX-UI compiles without errors
- **Commit:** "Create Hermes page component"

#### Task C1.2: Add route to NOFX-UI router
- **File:** `/workspaces/Memetrader/nofx-ui/src/App.tsx` (or router config)
- **Action:** Add route for `/hermes`
- **Code:**
```tsx
import HermesPage from './pages/HermesPage';

// In router:
<Route path="/hermes" element={<HermesPage />} />
```
- **Verification:** Navigate to `/hermes` in browser
- **Commit:** "Add Hermes page route"

### C2: Implement Chat Tab

#### Task C2.1: Create ChatTab component
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage/ChatTab.tsx` (create new)
- **Content:**
```tsx
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ChatTab() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8643/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'anthropic/claude-sonnet-4-20250514',
          messages: [{ role: 'user', content: input }],
          stream: true
        })
      });
      
      // Handle SSE streaming
      const reader = response.body?.getReader();
      let assistantContent = '';
      
      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        // Parse SSE and accumulate content
        assistantContent += chunk;
      }
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-[600px]">
      <ScrollArea className="flex-1 p-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'
            }`}>
              {msg.content}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </ScrollArea>
      
      <div className="flex gap-2 p-4 border-t">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button onClick={sendMessage} disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </Button>
      </div>
    </div>
  );
}
```
- **Verification:** Can send messages and receive responses
- **Commit:** "Implement Chat tab component"

#### Task C2.2: Add stop/retry/copy actions
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage/ChatTab.tsx`
- **Action:** Add buttons for stop, retry, copy
- **Code:** Add buttons in message display
- **Verification:** Buttons work as expected
- **Commit:** "Add chat actions (stop/retry/copy)"

### C3: Implement Memory Tab

#### Task C3.1: Create MemoryTab component
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage/MemoryTab.tsx` (create new)
- **Content:**
```tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MemoryFile {
  name: string;
  content: string;
  lastModified: string;
}

export default function MemoryTab() {
  const [files, setFiles] = useState<MemoryFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<MemoryFile | null>(null);
  const [content, setContent] = useState('');

  useEffect(() => {
    loadMemoryFiles();
  }, []);

  const loadMemoryFiles = async () => {
    try {
      const response = await fetch('http://localhost:8643/api/memory');
      const data = await response.json();
      setFiles(data.files || []);
    } catch (error) {
      console.error('Load memory error:', error);
    }
  };

  const saveMemory = async () => {
    if (!selectedFile) return;
    
    try {
      await fetch('http://localhost:8643/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: selectedFile.name,
          content: content
        })
      });
      loadMemoryFiles(); // Refresh
    } catch (error) {
      console.error('Save memory error:', error);
    }
  };

  const selectFile = (file: MemoryFile) => {
    setSelectedFile(file);
    setContent(file.content);
  };

  return (
    <div className="flex h-[600px]">
      <div className="w-1/3 border-r p-4">
        <h3 className="font-semibold mb-4">Memory Files</h3>
        <ScrollArea className="h-full">
          {files.map((file) => (
            <div
              key={file.name}
              className={`p-2 cursor-pointer rounded ${
                selectedFile?.name === file.name ? 'bg-blue-100' : 'hover:bg-gray-100'
              }`}
              onClick={() => selectFile(file)}
            >
              {file.name}
            </div>
          ))}
        </ScrollArea>
      </div>
      
      <div className="flex-1 p-4">
        {selectedFile ? (
          <>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold">{selectedFile.name}</h3>
              <Button onClick={saveMemory}>Save</Button>
            </div>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="h-full"
              placeholder="Memory content..."
            />
          </>
        ) : (
          <div className="text-center text-gray-500 mt-20">
            Select a memory file to edit
          </div>
        )}
      </div>
    </div>
  );
}
```
- **Verification:** Can load, view, and edit memory files
- **Commit:** "Implement Memory tab component"

### C4: Implement Skills Tab

#### Task C4.1: Create SkillsTab component
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage/SkillsTab.tsx` (create new)
- **Content:**
```tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Skill {
  name: string;
  description: string;
  version: string;
  tags: string[];
  enabled: boolean;
}

export default function SkillsTab() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      const response = await fetch('http://localhost:8643/api/skills');
      const data = await response.json();
      setSkills(data.skills || []);
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Load skills error:', error);
    }
  };

  const toggleSkill = async (skillName: string) => {
    try {
      await fetch(`http://localhost:8643/api/skills/${skillName}/toggle`, {
        method: 'POST'
      });
      loadSkills(); // Refresh
    } catch (error) {
      console.error('Toggle skill error:', error);
    }
  };

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Available Skills</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {skills.map((skill) => (
          <Card key={skill.name}>
            <CardHeader>
              <CardTitle className="flex justify-between items-center">
                {skill.name}
                <Badge variant={skill.enabled ? 'default' : 'secondary'}>
                  {skill.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </CardTitle>
              <CardDescription>{skill.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1 mb-4">
                {skill.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
              <Button
                onClick={() => toggleSkill(skill.name)}
                variant={skill.enabled ? 'destructive' : 'default'}
                size="sm"
                className="w-full"
              >
                {skill.enabled ? 'Disable' : 'Enable'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```
- **Verification:** Can view and toggle skills
- **Commit:** "Implement Skills tab component"

### C5: Implement Inspector Tab

#### Task C5.1: Create InspectorTab component
- **File:** `/workspaces/Memetrader/nofx-ui/src/pages/HermesPage/InspectorTab.tsx` (create new)
- **Content:**
```tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ToolCall {
  id: string;
  name: string;
  args: any;
  result: any;
  duration: number;
  timestamp: Date;
  success: boolean;
}

export default function InspectorTab() {
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);

  useEffect(() => {
    // This would be populated from chat session data
    // For now, show placeholder
    setToolCalls([]);
  }, []);

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Tool Call Inspector</h3>
      <ScrollArea className="h-[500px]">
        {toolCalls.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">
            No tool calls in current session
          </div>
        ) : (
          toolCalls.map((call) => (
            <Card key={call.id} className="mb-4">
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  {call.name}
                  <Badge variant={call.success ? 'default' : 'destructive'}>
                    {call.success ? 'Success' : 'Failed'}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {call.timestamp.toLocaleString()} • {call.duration}ms
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <strong>Arguments:</strong>
                    <pre className="bg-gray-100 p-2 rounded text-sm mt-1">
                      {JSON.stringify(call.args, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <strong>Result:</strong>
                    <pre className="bg-gray-100 p-2 rounded text-sm mt-1">
                      {JSON.stringify(call.result, null, 2)}
                    </pre>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </ScrollArea>
    </div>
  );
}
```
- **Verification:** Component renders without errors
- **Commit:** "Implement Inspector tab component"

## Phase 3: Data Sources Integration

**Goal:** Add CoinGecko, DexScreener, and Birdeye tools to Hermes.

### D1: CoinGecko Tool

#### Task D1.1: Create CoinGecko tool
- **File:** `/workspaces/Memetrader/tools/coingecko_tool.py` (create new)
- **Content:**
```python
import json
import requests
from tools.registry import registry

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

def check_requirements() -> bool:
    """Check if CoinGecko API is accessible"""
    try:
        response = requests.get(f"{COINGECKO_BASE_URL}/ping", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_coin_price(coin_id: str, currency: str = "usd") -> str:
    """Get current price for a coin"""
    try:
        url = f"{COINGECKO_BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": currency,
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if coin_id in data:
            price_data = data[coin_id]
            return json.dumps({
                "coin_id": coin_id,
                "price": price_data.get(currency, 0),
                "change_24h": price_data.get(f"{currency}_24h_change", 0),
                "currency": currency
            })
        else:
            return json.dumps({"error": f"Coin {coin_id} not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_trending_coins() -> str:
    """Get trending coins"""
    try:
        url = f"{COINGECKO_BASE_URL}/search/trending"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        coins = []
        for coin in data.get("coins", []):
            item = coin.get("item", {})
            coins.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "market_cap_rank": item.get("market_cap_rank")
            })
        
        return json.dumps({"trending_coins": coins})
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="coingecko_price",
    toolset="data",
    schema={
        "name": "coingecko_price",
        "description": "Get current price and 24h change for a cryptocurrency from CoinGecko",
        "parameters": {
            "type": "object",
            "properties": {
                "coin_id": {
                    "type": "string",
                    "description": "Coin ID (e.g., 'bitcoin', 'ethereum', 'solana')"
                },
                "currency": {
                    "type": "string",
                    "description": "Target currency (default: usd)",
                    "default": "usd"
                }
            },
            "required": ["coin_id"]
        }
    },
    handler=lambda args, **kw: get_coin_price(
        args.get("coin_id", ""),
        args.get("currency", "usd")
    ),
    check_fn=check_requirements
)

registry.register(
    name="coingecko_trending",
    toolset="data",
    schema={
        "name": "coingecko_trending",
        "description": "Get trending cryptocurrencies from CoinGecko",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    handler=lambda args, **kw: get_trending_coins(),
    check_fn=check_requirements
)
```
- **Verification:** Run `python -c "from tools.coingecko_tool import *"` - no errors
- **Test:** Call tool via Hermes CLI
- **Commit:** "Add CoinGecko tool"

#### Task D1.2: Add CoinGecko to tool discovery
- **File:** `/workspaces/Memetrader/model_tools.py`
- **Action:** Add import in `_discover_tools()` function
- **Code:**
```python
# Add after other tool imports
from tools import coingecko_tool
```
- **Verification:** Tool appears in available tools list
- **Commit:** "Register CoinGecko tool"

### D2: DexScreener Tool

#### Task D2.1: Create DexScreener tool
- **File:** `/workspaces/Memetrader/tools/dexscreener_tool.py` (create new)
- **Content:**
```python
import json
import requests
from tools.registry import registry

DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest"

def check_requirements() -> bool:
    """Check if DexScreener API is accessible"""
    try:
        response = requests.get(f"{DEXSCREENER_BASE_URL}/dex/search?q=ethereum", timeout=5)
        return response.status_code == 200
    except:
        return False

def search_pairs(query: str) -> str:
    """Search for trading pairs"""
    try:
        url = f"{DEXSCREENER_BASE_URL}/dex/search"
        params = {"q": query}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pairs = []
        for pair in data.get("pairs", [])[:10]:  # Limit to 10 results
            pairs.append({
                "pair_address": pair.get("pairAddress"),
                "base_token": {
                    "address": pair.get("baseToken", {}).get("address"),
                    "name": pair.get("baseToken", {}).get("name"),
                    "symbol": pair.get("baseToken", {}).get("symbol")
                },
                "quote_token": {
                    "address": pair.get("quoteToken", {}).get("address"),
                    "name": pair.get("quoteToken", {}).get("name"),
                    "symbol": pair.get("quoteToken", {}).get("symbol")
                },
                "price_usd": pair.get("priceUsd"),
                "volume_24h": pair.get("volume", {}).get("h24"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "dex_id": pair.get("dexId"),
                "chain_id": pair.get("chainId")
            })
        
        return json.dumps({"pairs": pairs})
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_pair_info(pair_address: str) -> str:
    """Get detailed pair information"""
    try:
        url = f"{DEXSCREENER_BASE_URL}/dex/pairs/{pair_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "pairs" in data and data["pairs"]:
            pair = data["pairs"][0]
            return json.dumps({
                "pair_address": pair.get("pairAddress"),
                "base_token": pair.get("baseToken"),
                "quote_token": pair.get("quoteToken"),
                "price_usd": pair.get("priceUsd"),
                "price_change_24h": pair.get("priceChange", {}).get("h24"),
                "volume_24h": pair.get("volume", {}).get("h24"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "fdv": pair.get("fdv"),
                "market_cap": pair.get("marketCap"),
                "dex_id": pair.get("dexId"),
                "chain_id": pair.get("chainId")
            })
        else:
            return json.dumps({"error": "Pair not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="dexscreener_search",
    toolset="data",
    schema={
        "name": "dexscreener_search",
        "description": "Search for trading pairs on DexScreener",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (token name, symbol, or contract address)"
                }
            },
            "required": ["query"]
        }
    },
    handler=lambda args, **kw: search_pairs(args.get("query", "")),
    check_fn=check_requirements
)

registry.register(
    name="dexscreener_pair_info",
    toolset="data",
    schema={
        "name": "dexscreener_pair_info",
        "description": "Get detailed information for a specific trading pair",
        "parameters": {
            "type": "object",
            "properties": {
                "pair_address": {
                    "type": "string",
                    "description": "Pair contract address"
                }
            },
            "required": ["pair_address"]
        }
    },
    handler=lambda args, **kw: get_pair_info(args.get("pair_address", "")),
    check_fn=check_requirements
)
```
- **Verification:** Run `python -c "from tools.dexscreener_tool import *"` - no errors
- **Test:** Search for "solana" via tool
- **Commit:** "Add DexScreener tool"

#### Task D2.2: Register DexScreener tool
- **File:** `/workspaces/Memetrader/model_tools.py`
- **Action:** Add import
- **Code:**
```python
from tools import dexscreener_tool
```
- **Verification:** Tool available in Hermes
- **Commit:** "Register DexScreener tool"

### D3: Birdeye Tool

#### Task D3.1: Create Birdeye tool
- **File:** `/workspaces/Memetrader/tools/birdeye_tool.py` (create new)
- **Content:**
```python
import json
import requests
from tools.registry import registry

BIRDEYE_BASE_URL = "https://public-api.birdeye.so"

def check_requirements() -> bool:
    """Check if Birdeye API is accessible"""
    try:
        # Birdeye has a free tier, check with a simple call
        response = requests.get(f"{BIRDEYE_BASE_URL}/defi/token_list?chain=solana", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_token_info(address: str) -> str:
    """Get token information"""
    try:
        url = f"{BIRDEYE_BASE_URL}/defi/token_overview"
        params = {"address": address}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            token_data = data.get("data", {})
            return json.dumps({
                "address": address,
                "name": token_data.get("name"),
                "symbol": token_data.get("symbol"),
                "decimals": token_data.get("decimals"),
                "price": token_data.get("price"),
                "price_change_24h": token_data.get("priceChange24hPercent"),
                "volume_24h": token_data.get("volume24hUSD"),
                "liquidity": token_data.get("liquidity"),
                "market_cap": token_data.get("mc"),
                "supply": token_data.get("supply")
            })
        else:
            return json.dumps({"error": "Token not found or API error"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_trending_tokens(chain: str = "solana") -> str:
    """Get trending tokens"""
    try:
        url = f"{BIRDEYE_BASE_URL}/defi/token_list"
        params = {"chain": chain}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            tokens = data.get("data", {}).get("tokens", [])
            trending = []
            for token in tokens[:20]:  # Top 20
                trending.append({
                    "address": token.get("address"),
                    "name": token.get("name"),
                    "symbol": token.get("symbol"),
                    "price": token.get("price"),
                    "volume_24h": token.get("volume24hUSD"),
                    "liquidity": token.get("liquidity")
                })
            return json.dumps({"trending_tokens": trending})
        else:
            return json.dumps({"error": "Failed to fetch trending tokens"})
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="birdeye_token_info",
    toolset="data",
    schema={
        "name": "birdeye_token_info",
        "description": "Get detailed token information from Birdeye (Solana focus)",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Token contract address"
                }
            },
            "required": ["address"]
        }
    },
    handler=lambda args, **kw: get_token_info(args.get("address", "")),
    check_fn=check_requirements
)

registry.register(
    name="birdeye_trending",
    toolset="data",
    schema={
        "name": "birdeye_trending",
        "description": "Get trending tokens from Birdeye",
        "parameters": {
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "Blockchain (default: solana)",
                    "default": "solana"
                }
            }
        }
    },
    handler=lambda args, **kw: get_trending_tokens(args.get("chain", "solana")),
    check_fn=check_requirements
)
```
- **Verification:** Import test passes
- **Test:** Get SOL token info
- **Commit:** "Add Birdeye tool"

#### Task D3.2: Register Birdeye tool
- **File:** `/workspaces/Memetrader/model_tools.py`
- **Action:** Add import
- **Code:**
```python
from tools import birdeye_tool
```
- **Verification:** Tool available
- **Commit:** "Register Birdeye tool"

## Phase 4: DEX Integration

**Goal:** Add DEX trading capabilities to NOFX.

### E1: Raydium Integration

#### Task E1.1: Create Raydium trader directory
- **File:** `/workspaces/Memetrader/nofx/trader/raydium/` (create directory)
- **Action:** Create directory structure
- **Verification:** Directory exists
- **Commit:** "Create Raydium trader directory"

#### Task E1.2: Implement Raydium trader interface
- **File:** `/workspaces/Memetrader/nofx/trader/raydium/trader.go` (create new)
- **Content:**
```go
package raydium

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
    
    "github.com/NoFxAiOS/nofx/trader"
)

type RaydiumTrader struct {
    client *http.Client
    baseURL string
}

func NewRaydiumTrader() *RaydiumTrader {
    return &RaydiumTrader{
        client: &http.Client{Timeout: 30 * time.Second},
        baseURL: "https://api.raydium.io/v2",
    }
}

func (r *RaydiumTrader) GetName() string {
    return "raydium"
}

func (r *RaydiumTrader) GetMarkets(ctx context.Context) ([]trader.Market, error) {
    // Implementation for getting markets
    return []trader.Market{}, nil
}

func (r *RaydiumTrader) GetTicker(ctx context.Context, symbol string) (*trader.Ticker, error) {
    // Implementation for getting ticker
    return &trader.Ticker{}, nil
}

func (r *RaydiumTrader) GetOrderBook(ctx context.Context, symbol string, depth int) (*trader.OrderBook, error) {
    // Implementation for order book
    return &trader.OrderBook{}, nil
}

func (r *RaydiumTrader) PlaceLimitOrder(ctx context.Context, req *trader.LimitOrderRequest) (*trader.OrderResult, error) {
    // Implementation for limit orders
    return &trader.OrderResult{}, fmt.Errorf("not implemented yet")
}

func (r *RaydiumTrader) PlaceMarketOrder(ctx context.Context, req *trader.MarketOrderRequest) (*trader.OrderResult, error) {
    // Implementation for market orders - priority for swaps
    return &trader.OrderResult{}, fmt.Errorf("not implemented yet")
}

func (r *RaydiumTrader) GetPositions(ctx context.Context) ([]trader.Position, error) {
    // Implementation for positions
    return []trader.Position{}, nil
}

func (r *RaydiumTrader) GetOrders(ctx context.Context, symbol string) ([]trader.Order, error) {
    // Implementation for orders
    return []trader.Order{}, nil
}

func (r *RaydiumTrader) CancelOrder(ctx context.Context, orderID string) error {
    // Implementation for cancel
    return fmt.Errorf("not implemented yet")
}
```
- **Verification:** Go code compiles
- **Commit:** "Implement Raydium trader interface"

#### Task E1.3: Add Raydium to NOFX trader registry
- **File:** `/workspaces/Memetrader/nofx/trader/registry.go` (or equivalent)
- **Action:** Register Raydium trader
- **Code:** Add to trader registry
- **Verification:** Raydium appears in available traders
- **Commit:** "Register Raydium trader"

### E2: Jupiter Integration

#### Task E2.1: Create Jupiter trader directory
- **File:** `/workspaces/Memetrader/nofx/trader/jupiter/` (create directory)
- **Verification:** Directory exists
- **Commit:** "Create Jupiter trader directory"

#### Task E2.2: Implement Jupiter trader
- **File:** `/workspaces/Memetrader/nofx/trader/jupiter/trader.go` (create new)
- **Content:** Similar structure to Raydium but using Jupiter API
- **Focus:** Swap functionality (market orders)
- **Verification:** Compiles
- **Commit:** "Implement Jupiter trader"

#### Task E2.3: Register Jupiter trader
- **File:** Registry file
- **Action:** Add Jupiter to registry
- **Verification:** Available in NOFX
- **Commit:** "Register Jupiter trader"

### E3: Cetus Integration

#### Task E3.1: Create Cetus trader directory
- **File:** `/workspaces/Memetrader/nofx/trader/cetus/` (create directory)
- **Verification:** Directory exists
- **Commit:** "Create Cetus trader directory"

#### Task E3.2: Implement Cetus trader
- **File:** `/workspaces/Memetrader/nofx/trader/cetus/trader.go` (create new)
- **Content:** SUI-focused DEX trader
- **Verification:** Compiles
- **Commit:** "Implement Cetus trader"

#### Task E3.3: Register Cetus trader
- **Action:** Add to registry
- **Verification:** Available
- **Commit:** "Register Cetus trader"

## Phase 5: Social Hype-Meter

**Goal:** Add social sentiment analysis tools.

### F1: Twitter Sentiment Tool

#### Task F1.1: Create Twitter sentiment tool
- **File:** `/workspaces/Memetrader/tools/twitter_sentiment_tool.py` (create new)
- **Content:**
```python
import json
from twikit import Client
from tools.registry import registry

def check_requirements() -> bool:
    """Check if Twitter access works"""
    try:
        # Twikit doesn't require API keys
        client = Client()
        return True
    except:
        return False

async def search_tweets(query: str, max_results: int = 20) -> str:
    """Search tweets with sentiment analysis"""
    try:
        client = Client()
        # Note: Twikit handles auth internally
        
        tweets = await client.search_tweet(query, max_results)
        
        results = []
        for tweet in tweets:
            results.append({
                "id": tweet.id,
                "text": tweet.text,
                "author": tweet.user.name,
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at.isoformat(),
                "likes": tweet.favorite_count,
                "retweets": tweet.retweet_count,
                "replies": tweet.reply_count
            })
        
        return json.dumps({"tweets": results})
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="twitter_search",
    toolset="social",
    schema={
        "name": "twitter_search",
        "description": "Search Twitter for tweets about cryptocurrencies",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'solana meme coin')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 20
                }
            },
            "required": ["query"]
        }
    },
    handler=lambda args, **kw: search_tweets(
        args.get("query", ""),
        args.get("max_results", 20)
    ),
    check_fn=check_requirements
)
```
- **Verification:** Import works
- **Test:** Search for "bitcoin"
- **Commit:** "Add Twitter sentiment tool"

#### Task F1.2: Register Twitter tool
- **File:** `/workspaces/Memetrader/model_tools.py`
- **Action:** Add import
- **Code:**
```python
from tools import twitter_sentiment_tool
```
- **Verification:** Tool available
- **Commit:** "Register Twitter tool"

### F2: Telegram Sentiment Tool

#### Task F2.1: Create Telegram sentiment tool
- **File:** `/workspaces/Memetrader/tools/telegram_sentiment_tool.py` (create new)
- **Content:** Similar to Twitter but for Telegram channels
- **Note:** May require API keys for full access
- **Verification:** Basic functionality
- **Commit:** "Add Telegram sentiment tool"

### F3: Discord Sentiment Tool

#### Task F3.1: Create Discord sentiment tool
- **File:** `/workspaces/Memetrader/tools/discord_sentiment_tool.py` (create new)
- **Content:** Discord channel monitoring
- **Verification:** Works
- **Commit:** "Add Discord sentiment tool"

## Phase 6: On-Chain Radar

**Goal:** Add blockchain monitoring capabilities.

### G1: Helius Integration

#### Task G1.1: Create Helius RPC tool
- **File:** `/workspaces/Memetrader/tools/helius_tool.py` (create new)
- **Content:** Solana RPC integration with parsed DEX trades
- **Verification:** Can query Solana
- **Commit:** "Add Helius RPC tool"

### G2: SUI RPC Integration

#### Task G2.1: Create SUI RPC tool
- **File:** `/workspaces/Memetrader/tools/sui_rpc_tool.py` (create new)
- **Content:** SUI blockchain queries
- **Verification:** Works
- **Commit:** "Add SUI RPC tool"

## Phase 7: Configuration and Testing

### H1: Update Unified Config

#### Task H1.1: Update config.yaml template
- **File:** `/workspaces/Memetrader/cli-config.yaml.example`
- **Action:** Add NOFX and data source configs
- **Code:**
```yaml
nofx:
  enabled: true
  api_url: http://localhost:8080
  api_token: your-jwt-token-here

data_sources:
  coingecko:
    enabled: true
  dexscreener:
    enabled: true
  birdeye:
    enabled: true

social:
  twitter:
    enabled: true
  telegram:
    enabled: true
  discord:
    enabled: true
```
- **Verification:** Valid YAML
- **Commit:** "Update config template"

### H2: Testing

#### Task H2.1: Test data source tools
- **Action:** Run Hermes CLI and test each new tool
- **Verification:** All tools return valid data
- **Commit:** "Test data source integrations"

#### Task H2.2: Test UI integration
- **Action:** Start NOFX-UI and navigate to /hermes
- **Verification:** All tabs load and function
- **Commit:** "Test UI integration"

#### Task H2.3: Test DEX connections
- **Action:** Test DEX APIs in devnet/testnet
- **Verification:** Can fetch prices and place test orders
- **Commit:** "Test DEX integrations"

## Success Criteria Verification

- [ ] Paper trading removed from Hermes
- [ ] NOFX AI disabled
- [ ] /hermes page accessible in NOFX-UI
- [ ] Chat, Memory, Skills, Inspector tabs working
- [ ] CoinGecko, DexScreener, Birdeye tools available
- [ ] Raydium, Jupiter, Cetus traders registered
- [ ] Twitter, Telegram, Discord tools working
- [ ] Helius and SUI RPC tools functional
- [ ] Unified config updated

## Next Steps

1. **Security audit** - Review all API keys and permissions
2. **Performance testing** - Load test with multiple concurrent users
3. **Paper trading validation** - Ensure 5x $100k target achievable
4. **Testnet deployment** - Move to real exchange testnets
5. **Risk management** - Implement stop losses and position limits
6. **Monitoring** - Add logging and alerting

---

**Total estimated tasks:** 50+  
**Estimated completion time:** 4-6 weeks  
**Risk level:** Medium (new integrations)  
**Testing requirement:** Extensive (multiple APIs and blockchains)