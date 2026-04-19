# SUI MCP Server Integration Guide for MemeTrader

## Overview
This document describes how to integrate ExpertVagabond's SUI MCP server (sui-mcp-server) with the MemeTrader system to enhance Sui blockchain and Cetus DEX capabilities beyond the current basic implementations.

## MCP Server Details
- **Repository**: https://github.com/ExpertVagabond/sui-mcp-server
- **NPM Package**: sui-mcp-server@0.4.1
- **Transport**: stdio
- **License**: MIT
- **Tools**: 53 tools covering wallet management, DeFi (Cetus, DeepBook), Move contracts, staking, SuiNS, and network analytics

## Current Sui/Cetus Implementation in MemeTrader
Before integrating the MCP server, MemeTrader already has:
- `tools/cetus_tool.py` - Basic Cetus swap and conditional limit order functionality
- `nofx/trader/cetus/` - NOFX Cetus trader implementation
- SUI RPC tool - `tools/sui_rpc_tool.py`

## Enhanced Capabilities via MCP Server
The sui-mcp-server provides significantly enhanced functionality:

### 1. **Advanced Cetus DEX Operations**
- `cetus_get_pools` - Query Cetus CLMM pools by coin types with liquidity and fee rates
- `cetus_get_pool` - Get detailed info for specific Cetus pool by object ID
- Enhanced pool analytics beyond basic swaps

### 2. **DeepBook Integration** (Sui's Central Limit Order Book)
- `deepbook_get_pool` - Get DeepBook v3 pool info (mid price, spread, balances)
- Enables true limit order trading on Sui via DeepBook CLOB

### 3. **Move Contract Interaction**
- `move_call` - Execute Move function calls
- `dev_inspect` - Simulate Move calls without execution
- `get_normalized_module`, `get_move_function`, `get_move_struct`
- Enables interaction with Sui smart contracts and custom programs

### 4. **Staking Operations**
- `get_stakes` - Get all staking positions
- `request_add_stake` - Stake SUI with validators
- `request_withdraw_stake` - Withdraw staked SUI
- `get_validators` - Get validator set with APY and commission

### 5. **SuiNS (Domain Service)**
- `suins_get_name_record` - Get detailed SuiNS name record
- `suins_get_price` - Get registration/renewal pricing
- `resolve_name` / `resolve_address` - Name resolution both directions

### 6. **Network Analytics & Debugging**
- `query_events` / `query_transactions` - On-chain event and transaction querying
- `get_object_history` - Trace transaction history of objects
- `get_checkpoint` / `get_epoch_info` - Network state analysis
- `get_reference_gas_price` - Current gas prices

### 7. **Wallet Management**
- Full wallet lifecycle: create, import, list, balance queries
- Transfer SUI and objects between addresses
- Coin operations: merge, split, get metadata

## Integration Approaches

### Approach 1: Direct MCP Tool Integration (Recommended)
Create new Hermes tools that wrap sui-mcp-server functions:

**New Tools to Create:**
- `tools/sui_mcp_wallet_tool.py` - Wallet management functions
- `tools/sui_mcp_cetus_tool.py` - Enhanced Cetus pool operations
- `tools/sui_mcp_deepbook_tool.py` - DeepBook limit order capabilities
- `tools/sui_mcp_staking_tool.py` - Staking operations
- `tools/sui_mcp_suins_tool.py` - SuiNS domain management
- `tools/sui_mcp_move_tool.py` - Move contract interaction

### Approach 2: Enhanced Existing Tools
Enhance existing tools to use MCP where beneficial:
- Enhance `tools/cetus_tool.py` with MCP-based pool queries for better liquidity data
- Enhance `tools/sui_rpc_tool.py` with MCP-based analytics
- Create new limit order tools that leverage DeepBook for true Sui limit orders

### Approach 3: Unified MCP Router
Create a unified SUI MCP tool that routes to appropriate functions based on operation type, similar to how we handle other MCP integrations.

## Installation & Setup

### 1. Install the MCP Server
```bash
npm install -g sui-mcp-server
# Or use npx directly without installation
```

### 2. Configure in Hermes
Add to `~/.hermes/config.yaml`:
```yaml
mcp:
  servers:
    sui-mcp-server:
      command: "npx"
      args: ["-y", "sui-mcp-server"]
      transport: "stdio"
      env: {}
```

### 3. Register with Hermes Tool System
Update `tools/mcp_tool.py` or create a new SUI-specific MCP tool registration.

## Usage Examples

### Enhanced Cetus Pool Analysis
```bash
# Get detailed Cetus pool information for SUI/USDC
hermes sui_mcp_cetus_get_pools --coinTypeA SUI --coinTypeB USDC --limit 10

# Get specific pool details
hermes sui_mcp_cetus_get_pool --poolId 0x123...
```

### DeepBook Limit Order Trading (True Sui Limit Orders)
```bash
# Get DeepBook pool info
hermes sui_mcp_deepbook_get_pool --poolId 0xdeepbook...

# Place limit order via DeepBook CLOB
hermes sui_mcp_deepbook_limit_order --poolId 0xdeepbook... --side BUY --price 0.50 --quantity 100
```

### Staking Operations
```bash
# Check staking opportunities
hermes sui_mcp_staking_get_validators

# Stake SUI with validator
hermes sui_mcp_staking_request_add_stake --wallet my_wallet --validator 0xvalidator... --amount 100
```

### SuiNS Domain Management
```bash
# Register a SuiNS domain
hermes sui_mcp_suins_register_name --name mytoken.sui --years 1

# Resolve domain to address
hermes sui_mcp_suins_resolve_name --name mytoken.sui
```

### Move Contract Interaction
```bash
# Call a Move function on a contract
hermes sui_mcp_move_call --wallet my_wallet --target 0xpackage::module::function --args "[1,2,3]"
```

## Benefits of Integration

### For Cetus DEX Enhancement:
- Access to real pool liquidity data and fee rates
- Ability to analyze and select optimal pools for trading
- Enhanced pool information for better trading decisions

### For True Sui Limit Orders:
- Access to DeepBook CLOB for genuine limit order trading (not simulated)
- Ability to place actual limit orders on Sui's central limit order book
- Better price discovery and execution quality

### For Advanced Strategies:
- Staking yield generation alongside trading
- SuiNS domain branding for tokens/projects
- Move contract interaction for custom strategies
- Comprehensive network analytics for market timing

### For Development:
- Leverages community-maintained, well-tested MCP server
- Reduces need to implement complex Sui-specific functionality from scratch
- Follows established MCP integration pattern in MemeTrader
- Easy to update as the MCP server evolves

## Testing & Verification

### Verify MCP Server is Working
```bash
# Test basic functionality
npx -y sui-mcp-server --help
# Should show: sui-mcp-server v0.4.0 running on devnet (stdio)

# Test initialization
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"roots":{"listChanged":true},"sampling":{}},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' | npx -y sui-mcp-server
```

### Test Key Functions
```bash
# Test wallet creation
echo '{"jsonrpc":"2.0","id":1,"method":"create_wallet","params":{"name":"testwallet"}}' | npx -y sui-mcp-server

# Test Cetus pools query
echo '{"jsonrpc":"2.0","id":1,"method":"cetus_get_pools","params":{"coinTypeA":"0x2::sui::SUI","coinTypeB":"0x6::usdc::USDC","limit":5}}' | npx -y sui-mcp-server

# Test DeepBook pool (if available on devnet)
echo '{"jsonrpc":"2.0","id":1,"method":"deepbook_get_pool","params":{"poolId":"0x1"}}' | npx -y sui-mcp-server
```

## Integration Roadmap

### Phase 1: Basic Integration (1-2 hours)
- Install and verify sui-mcp-server works
- Create basic wrapper tools for wallet management and simple queries
- Test core functionality

### Phase 2: Enhanced DEX Tools (2-4 hours)
- Create enhanced Cetus tools with pool analytics
- Create DeepBook limit order tools
- Create staking and SuiNS tools

### Phase 3: Strategy Integration (Optional)
- Integrate new capabilities into trading strategies
- Create example strategies using enhanced Sui capabilities
- Test combined DEX + staking + domain strategies

## Security Considerations
- MCP server runs locally via stdio - no network exposure
- Wallet keys managed in memory only (not persisted)
- Standard MCP safety practices apply
- No additional attack surface beyond existing MCP integrations

## Dependencies
- Node.js 18+ (for npx execution)
- sui-mcp-server NPM package (installed globally or via npx)
- No additional Python dependencies required

## Conclusion
Integrating ExpertVagabond's sui-mcp-server provides significant enhancement to MemeTrader's Sui and Cetus capabilities beyond basic swap functionality. It enables:
1. True limit order trading via DeepBook CLOB
2. Advanced Cetus pool analysis and selection
3. Staking yield generation
4. SuiNS domain management
5. Move contract interaction for custom strategies
6. Comprehensive network analytics

This integration would complement the existing limit order work on Raydium (CLMM) and Aerodrome (Slipstream) by providing genuine limit order capabilities on Sui via DeepBook, completing the limit order picture across all major chains supported by MemeTrader.

The MCP server is production-ready, well-documented, and follows the same integration pattern as our existing Analytics Hub MCP server, making it a straightforward enhancement to the system.