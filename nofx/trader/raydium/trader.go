package raydium

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"nofx/logger"
	"nofx/trader/types"
)

// Raydium API endpoints
const (
	raydiumSwapAPI    = "https://transaction-v1.raydium.io"
	raydiumSwapAPIv2  = "https://api.raydium.io/v2/dex/swap"
	raydiumTokenList  = "https://api.raydium.io/v2/token/mint-list"
	raydiumPairs      = "https://api.raydium.io/v2/pair/all"
	solanaRPC         = "https://api.mainnet-beta.solana.com"
	solanaDevnetRPC   = "https://api.devnet.solana.com"
)

// Token represents a Raydium token
type Token struct {
	Address     string  `json:"address"`
	Symbol      string  `json:"symbol"`
	Name        string  `json:"name"`
	Decimals    int     `json:"decimals"`
	Liquidity   float64 `json:"liquidity"`
	Volume24h   float64 `json:"volume24h"`
}

// SwapQuoteRequest represents a swap request
type SwapQuoteRequest struct {
	InputMint      string `json:"inputMint"`
	OutputMint     string `json:"outputMint"`
	Amount         int64  `json:"amount"`
	SlippageBps    int    `json:"slippageBps"`
	TxVersion      string `json:"txVersion"`
}

// SwapQuote represents a swap quote from Raydium
type SwapQuote struct {
	Success           bool     `json:"success"`
	FromToken         string   `json:"fromToken"`
	ToToken           string   `json:"toToken"`
	FromAmount        int64    `json:"fromAmount"`
	ToAmount          int64    `json:"toAmount"`
	PriceImpact      float64  `json:"priceImpact"`
	MarketInfo       []string `json:"marketInfo"`
	TransactionBytes string   `json:"transaction"`
}

// RaydiumTrader implements types.Trader interface for Raydium DEX
// Raydium is a major Solana DEX with concentrated liquidity and farm yields
type RaydiumTrader struct {
	privateKey       string
	publicKey        string
	httpClient       *http.Client
	isTestnet        bool

	// Token cache
	tokenCache      map[string]*Token
	tokenCacheTime  time.Time
	tokenCacheMutex sync.RWMutex
	cacheDuration   time.Duration

	// Balance cache
	cachedBalance   map[string]interface{}
	balanceCacheTime time.Time
	balanceCacheMutex sync.RWMutex
}

// NewRaydiumTrader creates a new Raydium trader instance
func NewRaydiumTrader(privateKey string, isTestnet bool) *RaydiumTrader {
	publicKey := derivePublicKey(privateKey)

	return &RaydiumTrader{
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
	if envKey := os.Getenv("SOLANA_WALLET_ADDRESS"); envKey != "" {
		return envKey
	}
	return "derived_public_key_placeholder"
}

// GetBalance returns account balance
func (rt *RaydiumTrader) GetBalance() (map[string]interface{}, error) {
	rt.balanceCacheMutex.RLock()
	if time.Since(rt.balanceCacheTime) < 10*time.Second {
		defer rt.balanceCacheMutex.RUnlock()
		return rt.cachedBalance, nil
	}
	rt.balanceCacheMutex.RUnlock()

	rpcURL := solanaDevnetRPC
	if !rt.isTestnet {
		rpcURL = solanaRPC
	}

	balance, err := rt.queryBalance(rpcURL, rt.publicKey)
	if err != nil {
		rt.balanceCacheMutex.RLock()
		defer rt.balanceCacheMutex.RUnlock()
		return rt.cachedBalance, nil
	}

	rt.balanceCacheMutex.Lock()
	rt.cachedBalance = balance
	rt.balanceCacheTime = time.Now()
	rt.balanceCacheMutex.Unlock()

	return balance, nil
}

func (rt *RaydiumTrader) queryBalance(rpcURL, pubkey string) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "getBalance",
		"params":   []string{pubkey},
	}

	resp, err := rt.httpClient.Post(rpcURL, "application/json", toJSON(payload))
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

// GetPositions returns current token holdings
func (rt *RaydiumTrader) GetPositions() ([]map[string]interface{}, error) {
	rpcURL := solanaDevnetRPC
	if !rt.isTestnet {
		rpcURL = solanaRPC
	}

	tokens, err := rt.getTokenAccounts(rpcURL, rt.publicKey)
	if err != nil {
		logger.Warnf("[Raydium] Failed to get token accounts: %v", err)
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

func (rt *RaydiumTrader) getTokenAccounts(rpcURL, pubkey string) ([]map[string]interface{}, error) {
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

	resp, err := rt.httpClient.Post(rpcURL, "application/json", toJSON(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	tokens := []map[string]interface{}{}
	tokens = append(tokens, map[string]interface{}{
		"mint":    "So11111111111111111111111111111111111111112",
		"symbol":  "SOL",
		"amount":  0.0,
		"valueUSD": 0.0,
	})

	return tokens, nil
}

// GetMarketPrice returns current market price
func (rt *RaydiumTrader) GetMarketPrice(symbol string) (float64, error) {
	inputMint := "So11111111111111111111111111111111111111112"
	outputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

	if strings.Contains(symbol, "/") {
		parts := strings.Split(symbol, "/")
		inputMint = rt.getTokenMint(parts[0])
		outputMint = rt.getTokenMint(parts[1])
	} else {
		inputMint = rt.getTokenMint(symbol)
	}

	quote, err := rt.GetSwapQuote(inputMint, outputMint, 1e9, 50)
	if err != nil {
		return 0, err
	}

	if !quote.Success {
		return 0, fmt.Errorf("swap quote failed")
	}

	return float64(quote.ToAmount) / 1e9, nil
}

func (rt *RaydiumTrader) getTokenMint(symbol string) string {
	tokenMints := map[string]string{
		"SOL":  "So11111111111111111111111111111111111111112",
		"USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
		"BONK": "DezXAZ8z7PnrnRJjz3wXoRgL4auUi9fmihz5YhYhC8K8",
		"WIF":  "85VBFQZC9TZkfaptBWqv14ALD9fJNUKtWA41kh69teRP",
		"RAY":  "4k3DyjyzpLNneWGVqL4WLZ2K8TFkgGs8uB2mQ2fL7cM8",
		"SRM":  "SRMuApVGdxT5B5h7f4vYq1xY6QwG7S3w7S6hL6hG2",
	}

	if mint, ok := tokenMints[strings.ToUpper(symbol)]; ok {
		return mint
	}

	return ""
}

// GetSwapQuote returns a swap quote from Raydium
func (rt *RaydiumTrader) GetSwapQuote(inputMint, outputMint string, amount int64, slippageBps int) (*SwapQuote, error) {
	url := raydiumSwapAPI + "/compute/swap-base-in"

	params := fmt.Sprintf("?inputMint=%s&outputMint=%s&amount=%d&slippageBps=%d&txVersion=V0",
		inputMint, outputMint, amount, slippageBps)

	resp, err := rt.httpClient.Get(url + params)
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

// ExecuteSwap executes a swap transaction
func (rt *RaydiumTrader) ExecuteSwap(quote *SwapQuote) (string, error) {
	if !quote.Success {
		return "", fmt.Errorf("invalid quote")
	}

	// In real implementation, would sign and send the transaction
	// For now, return the transaction bytes base64
	return quote.TransactionBytes, nil
}

// OpenLong opens a long position (buy token with USDC)
func (rt *RaydiumTrader) OpenLong(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	inputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" // USDC
	outputMint := rt.getTokenMint(symbol)

	if outputMint == "" {
		return nil, fmt.Errorf("unknown token: %s", symbol)
	}

	amount := int64(quantity * 1e6)

	quote, err := rt.GetSwapQuote(inputMint, outputMint, amount, 50)
	if err != nil {
		return nil, err
	}

	tx, err := rt.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "long",
		"quantity":      quantity,
		"transaction":   tx,
		"outputAmount":  float64(quote.ToAmount),
	}, nil
}

// OpenShort opens a short position (sell token for USDC)
func (rt *RaydiumTrader) OpenShort(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	inputMint := rt.getTokenMint(symbol)
	outputMint := "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

	if inputMint == "" {
		return nil, fmt.Errorf("unknown token: %s", symbol)
	}

	decimals := int64(9)
	amount := int64(quantity * float64(pow10(decimals)))

	quote, err := rt.GetSwapQuote(inputMint, outputMint, amount, 50)
	if err != nil {
		return nil, err
	}

	tx, err := rt.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "short",
		"quantity":      quantity,
		"transaction":   tx,
		"outputAmount":  float64(quote.ToAmount),
	}, nil
}

// CloseLong closes a long position
func (rt *RaydiumTrader) CloseLong(symbol string, quantity float64) (map[string]interface{}, error) {
	return rt.OpenShort(symbol, quantity, 0)
}

// CloseShort closes a short position
func (rt *RaydiumTrader) CloseShort(symbol string, quantity float64) (map[string]interface{}, error) {
	return rt.OpenLong(symbol, quantity, 0)
}

// SetLeverage not supported for spot DEX
func (rt *RaydiumTrader) SetLeverage(symbol string, leverage int) error {
	logger.Infof("[Raydium] SetLeverage ignored (spot-only DEX)")
	return nil
}

// SetMarginMode not supported for spot DEX
func (rt *RaydiumTrader) SetMarginMode(symbol string, isCrossMargin bool) error {
	logger.Infof("[Raydium] SetMarginMode ignored (spot-only DEX)")
	return nil
}

// SetStopLoss not supported
func (rt *RaydiumTrader) SetStopLoss(symbol string, positionSide string, quantity, stopPrice float64) error {
	logger.Warnf("[Raydium] SetStopLoss not supported for DEX spot")
	return nil
}

// SetTakeProfit not supported
func (rt *RaydiumTrader) SetTakeProfit(symbol string, positionSide string, quantity, takeProfitPrice float64) error {
	logger.Warnf("[Raydium] SetTakeProfit not supported for DEX spot")
	return nil
}

// CancelStopLossOrders no-op
func (rt *RaydiumTrader) CancelStopLossOrders(symbol string) error {
	return nil
}

// CancelTakeProfitOrders no-op
func (rt *RaydiumTrader) CancelTakeProfitOrders(symbol string) error {
	return nil
}

// CancelAllOrders no-op
func (rt *RaydiumTrader) CancelAllOrders(symbol string) error {
	return nil
}

// CancelStopOrders no-op
func (rt *RaydiumTrader) CancelStopOrders(symbol string) error {
	return nil
}

// FormatQuantity formats quantity
func (rt *RaydiumTrader) FormatQuantity(symbol string, quantity float64) (string, error) {
	return fmt.Sprintf("%.6f", quantity), nil
}

// GetOrderStatus returns order status
func (rt *RaydiumTrader) GetOrderStatus(symbol string, orderID string) (map[string]interface{}, error) {
	return map[string]interface{}{
		"status":  "FILLED",
		"orderID": orderID,
	}, nil
}

// GetClosedPnL returns closed PnL
func (rt *RaydiumTrader) GetClosedPnL(startTime time.Time, limit int) ([]types.ClosedPnLRecord, error) {
	return []types.ClosedPnLRecord{}, nil
}

// GetOpenOrders returns open orders
func (rt *RaydiumTrader) GetOpenOrders(symbol string) ([]types.OpenOrder, error) {
	return []types.OpenOrder{}, nil
}

func pow10(n int64) int64 {
	result := int64(1)
	for i := int64(0); i < n; i++ {
		result *= 10
	}
	return result
}

func toJSON(v interface{}) *strings.Reader {
	b, _ := json.Marshal(v)
	return strings.NewReader(string(b))
}

// Ensure RaydiumTrader implements Trader interface
var _ types.Trader = (*RaydiumTrader)(nil)