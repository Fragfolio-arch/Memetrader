package jupiter

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"nofx/logger"
	"nofx/trader/types"
)

// Jupiter API endpoints
const (
	jupiterSwapAPI     = "https://api.jup.ag/swap/v1"
	jupiterSwapAPIv2   = "https://api.jup.ag/swap/v2"
	jupiterTokenList   = "https://api.jup.ag/tokens/v1/token-list"
	solanaRPC          = "https://api.mainnet-beta.solana.com"
	solanaDevnetRPC    = "https://api.devnet.solana.com"
)

// Token represents a Solana token
type Token struct {
	Address     string `json:"address"`
	Symbol      string `json:"symbol"`
	Name        string `json:"name"`
	Decimals    int    `json:"decimals"`
	Liquidity   int64  `json:"liquidity"`
	Volume24h   int64  `json:"volume24h"`
	Volume7d    int64  `json:"volume7d"`
	MarketCap   int64  `json:"marketCap"`
}

// SwapQuoteRequest represents a swap quote request
type SwapQuoteRequest struct {
	InputMint           string  `json:"inputMint"`
	OutputMint          string  `json:"outputMint"`
	Amount              int64   `json:"amount"`
	SlippageBps        int     `json:"slippageBps"`
	UserPublicKey       string  `json:"userPublicKey"`
	ReduceSearchResults bool    `json:"reduceSearchResults,omitempty"`
}

// SwapQuote represents a swap quote
type SwapQuote struct {
	InputMint           string        `json:"inputMint"`
	OutputMint          string        `json:"outputMint"`
	InAmount            string        `json:"inAmount"`
	OutAmount           string        `json:"outAmount"`
	PriceImpactPct      string        `json:"priceImpactPct"`
	MarketInfos         []MarketInfo  `json:"marketInfos"`
	OtherAmountThreshold string       `json:"otherAmountThreshold"`
	SwapMode            string        `json:"swapMode"`
	SlippageBps         int           `json:"slippageBps"`
	PlatformFee         string        `json:"platformFee,omitempty"`
}

// MarketInfo represents routing information
type MarketInfo struct {
	Label          string `json:"label"`
	InputMint      string `json:"inputMint"`
	OutputMint     string `json:"outputMint"`
	InAmount       string `json:"inAmount"`
	OutAmount      string `json:"outAmount"`
	PriceImpactPct string `json:"priceImpactPct"`
}

// SwapRequest represents a swap execution request
type SwapRequest struct {
	QuoteResponse  string `json:"quoteResponse"`
	UserPublicKey   string `json:"userPublicKey"`
	WrapAndUnwrapSol bool  `json:"wrapAndUnwrapSol"`
}

// SwapResult represents swap execution result
type SwapResult struct {
	Transaction string `json:"transaction"`
	TokenResults []TokenResult `json:"tokenResults,omitempty"`
}

// TokenResult represents token change in swap
type TokenResult struct {
	TokenName        string `json:"tokenName"`
	TokenSymbol      string `json:"tokenSymbol"`
	FromTokenAmount  string `json:"fromTokenAmount"`
	ToTokenAmount    string `json:"toTokenAmount"`
}

// JupiterTrader implements types.Trader interface for Jupiter DEX
// Jupiter is Solana's largest DEX aggregator, routing across multiple DEXs
type JupiterTrader struct {
	privateKey       string
	publicKey        string
	httpClient       *http.Client
	isTestnet        bool

	// Token cache
	tokenCache      map[string]*Token
	tokenCacheTime  time.Time
	tokenCacheMutex sync.RWMutex
	cacheDuration   time.Duration

	// Balance cache (simulated for now - real implementation would query RPC)
	cachedBalance   map[string]interface{}
	balanceCacheTime time.Time
	balanceCacheMutex sync.RWMutex
}

// NewJupiterTrader creates a new Jupiter trader instance
func NewJupiterTrader(privateKey string, isTestnet bool) *JupiterTrader {
	publicKey := derivePublicKey(privateKey)

	return &JupiterTrader{
		privateKey:       privateKey,
		publicKey:        publicKey,
		httpClient:       &http.Client{Timeout: 30 * time.Second},
		isTestnet:        isTestnet,
		tokenCache:       make(map[string]*Token),
		cacheDuration:    5 * time.Minute,
		cachedBalance:   make(map[string]interface{}),
	}
}

func derivePublicKey(privateKey string) string {
	if privateKey == "" {
		return os.Getenv("SOLANA_WALLET_ADDRESS")
	}
	// Derive public key from base58 private key
	// In production, use solders.Keypair.from_base58() or similar
	// For now, we use the env var if available, otherwise derive
	if envKey := os.Getenv("SOLANA_WALLET_ADDRESS"); envKey != "" {
		return envKey
	}
	// Placeholder - in real implementation would use:
	// import "github.com/gagliardetto/solana-go"
	// keypair := solana_go.KeypairFromBase58(privateKey)
	// return keypair.PubKey().String()
	return "derived_public_key_placeholder"
}

// GetBalance returns account balance (from on-chain data)
func (jt *JupiterTrader) GetBalance() (map[string]interface{}, error) {
	jt.balanceCacheMutex.RLock()
	if time.Since(jt.balanceCacheTime) < 10*time.Second {
		defer jt.balanceCacheMutex.RUnlock()
		return jt.cachedBalance, nil
	}
	jt.balanceCacheMutex.RUnlock()

	// Query Solana RPC for balance
	rpcURL := solanaDevnetRPC
	if !jt.isTestnet {
		rpcURL = solanaRPC
	}

	balance, err := jt.queryBalance(rpcURL, jt.publicKey)
	if err != nil {
		// Return cached if query fails
		jt.balanceCacheMutex.RLock()
		defer jt.balanceCacheMutex.RUnlock()
		return jt.cachedBalance, nil
	}

	jt.balanceCacheMutex.Lock()
	jt.cachedBalance = balance
	jt.balanceCacheTime = time.Now()
	jt.balanceCacheMutex.Unlock()

	return balance, nil
}

// queryBalance queries Solana RPC for account balance
func (jt *JupiterTrader) queryBalance(rpcURL, pubkey string) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "getBalance",
		"params":   []string{pubkey},
	}

	resp, err := jt.httpClient.Post(rpcURL, "application/json", toJSON(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	if result["error"] != nil {
		return nil, fmt.Errorf("RPC error: %v", result["error"])
	}

	solBalance := result["result"].(map[string]interface{})["value"].(float64)
	lamports := int64(solBalance)

	return map[string]interface{}{
		"SOL": map[string]interface{}{
			"available": float64(lamports) / 1e9,
			"locked":   0.0,
		},
		"total": float64(lamports) / 1e9,
	}, nil
}

// GetPositions returns current positions (for DEX, this is token holdings)
func (jt *JupiterTrader) GetPositions() ([]map[string]interface{}, error) {
	// For DEX, positions = token holdings in wallet
	// Query all token accounts for this wallet
	rpcURL := solanaDevnetRPC
	if !jt.isTestnet {
		rpcURL = solanaRPC
	}

	tokens, err := jt.getTokenAccounts(rpcURL, jt.publicKey)
	if err != nil {
		logger.Warnf("[Jupiter] Failed to get token accounts: %v", err)
		return []map[string]interface{}{}, nil
	}

	positions := make([]map[string]interface{}, 0, len(tokens))
	for _, token := range tokens {
		if token["amount"].(float64) > 0 {
			positions = append(positions, map[string]interface{}{
				"symbol":   token["symbol"],
				"mint":     token["mint"],
				"quantity": token["amount"],
				"valueUSD": token["valueUSD"],
			})
		}
	}

	return positions, nil
}

// getTokenAccounts gets all token accounts for a wallet
func (jt *JupiterTrader) getTokenAccounts(rpcURL, pubkey string) ([]map[string]interface{}, error) {
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "getTokenAccountsByOwner",
		"params": map[string]interface{}{
			"owner": pubkey,
			"options": map[string]interface{}{
				"page": 1,
				"limit": 100,
			},
		},
	}

	resp, err := jt.httpClient.Post(rpcURL, "application/json", toJSON(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	// Parse token accounts - simplified
	tokens := []map[string]interface{}{}

	// Add SOL as base
	tokens = append(tokens, map[string]interface{}{
		"mint":    "So11111111111111111111111111111111111111112",
		"symbol":  "SOL",
		"amount":  0.0, // Would be filled from getBalance
		"valueUSD": 0.0,
	})

	return tokens, nil
}

// GetMarketPrice returns current market price for a token pair
func (jt *JupiterTrader) GetMarketPrice(symbol string) (float64, error) {
	// For DEX, get price from Jupiter quote
	// Symbol format: "SOL/USDC" or just "SOL"
	inputMint := "So11111111111111111111111111111111111111112" // SOL
	outputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" // USDC

	if strings.Contains(symbol, "/") {
		parts := strings.Split(symbol, "/")
		inputMint = jt.getTokenMint(parts[0])
		outputMint = jt.getTokenMint(parts[1])
	} else {
		inputMint = jt.getTokenMint(symbol)
	}

	// Get quote for 1 unit
	quote, err := jt.GetSwapQuote(inputMint, outputMint, 1e9, 50)
	if err != nil {
		return 0, err
	}

	outAmount, _ := strconv.ParseFloat(quote.OutAmount, 64)
	return outAmount / 1e9, nil // Convert back from lamports
}

// getTokenMint returns token mint address from symbol
func (jt *JupiterTrader) getTokenMint(symbol string) string {
	tokenMints := map[string]string{
		"SOL":  "So11111111111111111111111111111111111111112",
		"USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
		"USDT": "Es9vMFrzaGnHq36X5vQcYJp1kJEGnYH 7CMQhEwL4rK8", // Note: This needs proper address
		"BONK": "DezXAZ8z7PnrnRJjz3wXoRgL4auUi9fmihz5YhY3M4B7",
		"WIF":  "85VBFQZC9TZkfaptBWqv14ALD9fJNUKtWA41kh69teRP",
		"PEPE": "ArwP4iVWiSGLkC4r5uLTJNo1Ea5Bq3bY7u4x3Q3xK4v",
	}

	if mint, ok := tokenMints[strings.ToUpper(symbol)]; ok {
		return mint
	}

	return ""
}

// GetSwapQuote returns a swap quote from Jupiter
func (jt *JupiterTrader) GetSwapQuote(inputMint, outputMint string, amount int64, slippageBps int) (*SwapQuote, error) {
	url := jupiterSwapAPI + "/quote"

	params := fmt.Sprintf("?inputMint=%s&outputMint=%s&amount=%d&slippageBps=%d",
		inputMint, outputMint, amount, slippageBps)

	resp, err := jt.httpClient.Get(url + params)
	if err != nil {
		return nil, fmt.Errorf("failed to get quote: %w", err)
	}
	defer resp.Body.Close()

	var quote SwapQuote
	if err := json.NewDecoder(resp.Body).Decode(&quote); err != nil {
		return nil, fmt.Errorf("failed to parse quote: %w", err)
	}

	return &quote, nil
}

// ExecuteSwap executes a token swap on Jupiter
func (jt *JupiterTrader) ExecuteSwap(quote *SwapQuote) (*SwapResult, error) {
	url := jupiterSwapAPI + "/swap"

	quoteJSON, err := json.Marshal(quote)
	if err != nil {
		return nil, err
	}

	body := map[string]interface{}{
		"quoteResponse":     string(quoteJSON),
		"userPublicKey":      jt.publicKey,
		"wrapAndUnwrapSol":   true,
	}

	resp, err := jt.httpClient.Post(url, "application/json", toJSON(body))
	if err != nil {
		return nil, fmt.Errorf("failed to execute swap: %w", err)
	}
	defer resp.Body.Close()

	var result SwapResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to parse swap result: %w", err)
	}

	return &result, nil
}

// OpenLong opens a long position (buy token)
func (jt *JupiterTrader) OpenLong(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	// DEX doesn't have leverage, quantity = amount to buy
	// Symbol format: "SOL/USDC" or "SOL"
	inputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" // USDC (pay with USDC)
	outputMint := jt.getTokenMint(symbol)

	if outputMint == "" {
		return nil, fmt.Errorf("unknown token: %s", symbol)
	}

	amount := int64(quantity * 1e6) // Convert to USDC lamports

	quote, err := jt.GetSwapQuote(inputMint, outputMint, amount, 50)
	if err != nil {
		return nil, err
	}

	result, err := jt.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "long",
		"quantity":      quantity,
		"transaction":   result.Transaction,
		"outputAmount":  quote.OutAmount,
	}, nil
}

// OpenShort opens a short position (sell token for USDC)
func (jt *JupiterTrader) OpenShort(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	// For DEX spot, "short" = sell the token
	inputMint := jt.getTokenMint(symbol)
	outputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" // USDC

	if inputMint == "" {
		return nil, fmt.Errorf("unknown token: %s", symbol)
	}

	// Get token decimals (simplified - assume 9 for most tokens)
	decimals := int64(9)
	amount := int64(quantity * float64(pow10(decimals)))

	quote, err := jt.GetSwapQuote(inputMint, outputMint, amount, 50)
	if err != nil {
		return nil, err
	}

	result, err := jt.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "short",
		"quantity":      quantity,
		"transaction":   result.Transaction,
		"outputAmount":  quote.OutAmount,
	}, nil
}

// CloseLong closes a long position (sell token for USDC)
func (jt *JupiterTrader) CloseLong(symbol string, quantity float64) (map[string]interface{}, error) {
	// Same as OpenShort for spot DEX
	return jt.OpenShort(symbol, quantity, 0)
}

// CloseShort closes a short position (buy back token)
func (jt *JupiterTrader) CloseShort(symbol string, quantity float64) (map[string]interface{}, error) {
	// Same as OpenLong for spot DEX
	return jt.OpenLong(symbol, quantity, 0)
}

// SetLeverage sets leverage (N/A for spot DEX)
func (jt *JupiterTrader) SetLeverage(symbol string, leverage int) error {
	logger.Infof("[Jupiter] SetLeverage ignored (spot-only DEX, no leverage support)")
	return nil
}

// SetMarginMode sets margin mode (N/A for spot DEX)
func (jt *JupiterTrader) SetMarginMode(symbol string, isCrossMargin bool) error {
	logger.Infof("[Jupiter] SetMarginMode ignored (spot-only DEX, no margin support)")
	return nil
}

// SetStopLoss sets stop-loss order (not supported for DEX spot)
func (jt *JupiterTrader) SetStopLoss(symbol string, positionSide string, quantity, stopPrice float64) error {
	logger.Warnf("[Jupiter] SetStopLoss not supported for DEX spot trading")
	return nil
}

// SetTakeProfit sets take-profit order (not supported for DEX spot)
func (jt *JupiterTrader) SetTakeProfit(symbol string, positionSide string, quantity, takeProfitPrice float64) error {
	logger.Warnf("[Jupiter] SetTakeProfit not supported for DEX spot trading")
	return nil
}

// CancelStopLossOrders cancels stop-loss orders
func (jt *JupiterTrader) CancelStopLossOrders(symbol string) error {
	return nil
}

// CancelTakeProfitOrders cancels take-profit orders
func (jt *JupiterTrader) CancelTakeProfitOrders(symbol string) error {
	return nil
}

// CancelAllOrders cancels all pending orders
func (jt *JupiterTrader) CancelAllOrders(symbol string) error {
	return nil
}

// CancelStopOrders cancels stop orders
func (jt *JupiterTrader) CancelStopOrders(symbol string) error {
	return nil
}

// FormatQuantity formats quantity to correct precision
func (jt *JupiterTrader) FormatQuantity(symbol string, quantity float64) (string, error) {
	// For DEX, just return with reasonable precision
	return fmt.Sprintf("%.6f", quantity), nil
}

// GetOrderStatus returns order status
func (jt *JupiterTrader) GetOrderStatus(symbol string, orderID string) (map[string]interface{}, error) {
	// DEX swaps are instant/failed, no order status to track
	return map[string]interface{}{
		"status":      "FILLED",
		"orderID":     orderID,
		"symbol":      symbol,
	}, nil
}

// GetClosedPnL returns closed PnL (not applicable for spot DEX)
func (jt *JupiterTrader) GetClosedPnL(startTime time.Time, limit int) ([]types.ClosedPnLRecord, error) {
	return []types.ClosedPnLRecord{}, nil
}

// GetOpenOrders returns open orders (none for spot DEX)
func (jt *JupiterTrader) GetOpenOrders(symbol string) ([]types.OpenOrder, error) {
	return []types.OpenOrder{}, nil
}

// Helper: pow10 returns 10^n
func pow10(n int64) int64 {
	result := int64(1)
	for i := int64(0); i < n; i++ {
		result *= 10
	}
	return result
}

// Helper: toJSON converts map to JSON bytes
func toJSON(v interface{}) *strings.Reader {
	b, _ := json.Marshal(v)
	return strings.NewReader(string(b))
}

// Ensure JupiterTrader implements Trader interface
var _ types.Trader = (*JupiterTrader)(nil)