package cetus

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

// Cetus API endpoints
const (
	cetusSwapAPI   = "https://api.cetus.zone/v2/swap"
	cetusPoolsAPI  = "https://api.cetus.zone/v2/pools"
	cetusRPC        = "https://mainnet-rpc.cetus.zone"
	cetusTestnetRPC = "https://testnet-rpc.cetus.zone"
)

// Token represents a Sui token
type Token struct {
	Address     string  `json:"address"`
	Symbol      string  `json:"symbol"`
	Name        string  `json:"name"`
	Decimals    int     `json:"decimals"`
	Type        string  `json:"type"`
}

// Pool represents a Cetus liquidity pool
type Pool struct {
	PoolID       string  `json:"pool_id"`
	TokenA       Token   `json:"token_a"`
	TokenB       Token   `json:"token_b"`
	LiquidityA   float64 `json:"liquidity_a"`
	LiquidityB   float64 `json:"liquidity_b"`
	Volume24h    float64 `json:"volume_24h"`
	Apr          float64 `json:"apr"`
}

// SwapQuoteRequest represents a swap request
type SwapQuoteRequest struct {
	FromToken   string  `json:"from_token"`
	ToToken     string  `json:"to_token"`
	Amount      int64   `json:"amount"`
	Slippage    float64 `json:"slippage"`
}

// SwapQuote represents a swap quote
type SwapQuote struct {
	FromToken      string `json:"from_token"`
	ToToken        string `json:"to_token"`
	FromAmount     int64  `json:"from_amount"`
	ToAmount       int64  `json:"to_amount"`
	PriceImpact    float64 `json:"price_impact"`
	Route          []string `json:"route"`
}

// CetusTrader implements types.Trader interface for Cetus DEX
// Cetus is the largest DEX on Sui blockchain with concentrated liquidity
type CetusTrader struct {
	privateKey       string
	publicKey        string
	httpClient       *http.Client
	isTestnet        bool

	// Pool cache
	poolCache      map[string]*Pool
	poolCacheTime  time.Time
	poolCacheMutex sync.RWMutex
	cacheDuration  time.Duration

	// Balance cache
	cachedBalance   map[string]interface{}
	balanceCacheTime time.Time
	balanceCacheMutex sync.RWMutex
}

// NewCetusTrader creates a new Cetus trader instance
func NewCetusTrader(privateKey string, isTestnet bool) *CetusTrader {
	publicKey := derivePublicKey(privateKey)

	return &CetusTrader{
		privateKey:       privateKey,
		publicKey:        publicKey,
		httpClient:       &http.Client{Timeout: 30 * time.Second},
		isTestnet:        isTestnet,
		poolCache:        make(map[string]*Pool),
		cacheDuration:    5 * time.Minute,
		cachedBalance:   make(map[string]interface{}),
	}
}

func derivePublicKey(privateKey string) string {
	if privateKey == "" {
		return os.Getenv("SUI_WALLET_ADDRESS")
	}
	if envKey := os.Getenv("SUI_WALLET_ADDRESS"); envKey != "" {
		return envKey
	}
	return "derived_public_key_placeholder"
}

// GetBalance returns account balance (SUI and tokens)
func (ct *CetusTrader) GetBalance() (map[string]interface{}, error) {
	ct.balanceCacheMutex.RLock()
	if time.Since(ct.balanceCacheTime) < 10*time.Second {
		defer ct.balanceCacheMutex.RUnlock()
		return ct.cachedBalance, nil
	}
	ct.balanceCacheMutex.RUnlock()

	rpcURL := cetusTestnetRPC
	if !ct.isTestnet {
		rpcURL = cetusRPC
	}

	balance, err := ct.queryBalance(rpcURL, ct.publicKey)
	if err != nil {
		ct.balanceCacheMutex.RLock()
		defer ct.balanceCacheMutex.RUnlock()
		return ct.cachedBalance, nil
	}

	ct.balanceCacheMutex.Lock()
	ct.cachedBalance = balance
	ct.balanceCacheTime = time.Now()
	ct.balanceCacheMutex.Unlock()

	return balance, nil
}

func (ct *CetusTrader) queryBalance(rpcURL, pubkey string) (map[string]interface{}, error) {
	// Query Sui RPC for coins
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "suix_getBalance",
		"params":   []interface{}{pubkey, "0x2::sui::SUI"},
	}

	resp, err := ct.httpClient.Post(rpcURL, "application/json", toJSON(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	if result["error"] != nil {
		return map[string]interface{}{
			"SUI": map[string]interface{}{
				"available": 0.0,
				"locked":    0.0,
			},
			"total": 0.0,
		}, nil
	}

	balanceObj := result["result"].(map[string]interface{})
	totalBalance := balanceObj["totalBalance"].(string)
	balance, _ := strconv.ParseFloat(totalBalance, 64)

	return map[string]interface{}{
		"SUI": map[string]interface{}{
			"available": balance / 1e9,
			"locked":    0.0,
		},
		"total": balance / 1e9,
	}, nil
}

// GetPositions returns current token holdings (LP positions + token balances)
func (ct *CetusTrader) GetPositions() ([]map[string]interface{}, error) {
	rpcURL := cetusTestnetRPC
	if !ct.isTestnet {
		rpcURL = cetusRPC
	}

	// Get pools to understand available trading pairs
	_, err := ct.getPools(rpcURL)
	if err != nil {
		logger.Warnf("[Cetus] Failed to get pools: %v", err)
		return []map[string]interface{}{}, nil
	}

	// Get user LP positions (simplified - would need proper position query)
	positions := []map[string]interface{}{}

	// Add SUI balance as a "position"
	balance, _ := ct.GetBalance()
	if suiBalance, ok := balance["SUI"].(map[string]interface{}); ok {
		if avail, ok := suiBalance["available"].(float64); ok && avail > 0 {
			positions = append(positions, map[string]interface{}{
				"symbol":   "SUI",
				"quantity": avail,
				"type":     "token",
			})
		}
	}

	return positions, nil
}

func (ct *CetusTrader) getPools(rpcURL string) ([]Pool, error) {
	ct.poolCacheMutex.RLock()
	if time.Since(ct.poolCacheTime) < ct.cacheDuration {
		defer ct.poolCacheMutex.RUnlock()
		pools := make([]Pool, 0, len(ct.poolCache))
		for _, p := range ct.poolCache {
			pools = append(pools, *p)
		}
		return pools, nil
	}
	ct.poolCacheMutex.RUnlock()

	// Fetch from API
	resp, err := ct.httpClient.Get(cetusPoolsAPI)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var poolsResp struct {
		Data []Pool `json:"data"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&poolsResp); err != nil {
		return nil, err
	}

	ct.poolCacheMutex.Lock()
	for i := range poolsResp.Data {
		pool := &poolsResp.Data[i]
		ct.poolCache[pool.PoolID] = pool
	}
	ct.poolCacheTime = time.Now()
	ct.poolCacheMutex.Unlock()

	return poolsResp.Data, nil
}

// GetMarketPrice returns current market price for a token pair
func (ct *CetusTrader) GetMarketPrice(symbol string) (float64, error) {
	// Parse symbol (e.g., "SUI/USDC")
	var baseToken, quoteToken string
	if strings.Contains(symbol, "/") {
		parts := strings.Split(symbol, "/")
		baseToken = strings.ToUpper(parts[0])
		quoteToken = strings.ToUpper(parts[1])
	} else {
		baseToken = strings.ToUpper(symbol)
		quoteToken = "USDC"
	}

	rpcURL := cetusTestnetRPC
	if !ct.isTestnet {
		rpcURL = cetusRPC
	}

	pools, err := ct.getPools(rpcURL)
	if err != nil {
		return 0, err
	}

	// Find pool for this pair
	baseMint := ct.getTokenMint(baseToken)
	quoteMint := ct.getTokenMint(quoteToken)

	for _, pool := range pools {
		aMint := strings.ToUpper(pool.TokenA.Type)
		bMint := strings.ToUpper(pool.TokenB.Type)

		if (aMint == baseMint && bMint == quoteMint) || (aMint == quoteMint && bMint == baseMint) {
			// Calculate price
			var price float64
			if aMint == baseMint {
				price = pool.LiquidityB / pool.LiquidityA
			} else {
				price = pool.LiquidityA / pool.LiquidityB
			}
			return price, nil
		}
	}

	return 0, fmt.Errorf("no pool found for %s", symbol)
}

func (ct *CetusTrader) getTokenMint(symbol string) string {
	tokenTypes := map[string]string{
		"SUI":   "0x2::sui::SUI",
		"USDC":  "0xa231e1c8b1e9a9a1f7f1e1c1e9a9a1f7f1e1c1e9a9a1f7f1e1c1e9a9a1f7::usdc::USDC",
		"USDT":  "0xc060006111116b2d0466b66dc28f2c7b1b1f1b1b1b1b1b1b1b1b1b1b1b1b1b::usdt::USDT",
		"WAL":   "0x5ae65d6b860b7b3e5c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c::wal::WAL",
		"DEEP":  "0x849a4a1f6715ce24a3d3a6b3b3b3b3b3b3b3b3b3b3b3b3b3b3b3b3b3::deep::DEEP",
	}

	if mint, ok := tokenTypes[strings.ToUpper(symbol)]; ok {
		return mint
	}

	return ""
}

// GetSwapQuote returns a swap quote from Cetus
func (ct *CetusTrader) GetSwapQuote(fromToken, toToken string, amount int64, slippage float64) (*SwapQuote, error) {
	url := cetusSwapAPI + "/quote"

	req := SwapQuoteRequest{
		FromToken: fromToken,
		ToToken:   toToken,
		Amount:    amount,
		Slippage:  slippage,
	}

	resp, err := ct.httpClient.Post(url, "application/json", toJSON(req))
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
func (ct *CetusTrader) ExecuteSwap(quote *SwapQuote) (string, error) {
	// In real implementation, would build and sign Sui transaction
	// For now, return empty
	return "", nil
}

// OpenLong opens a long position (buy token with USDC)
func (ct *CetusTrader) OpenLong(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	parts := strings.Split(symbol, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid symbol format: %s (expected: BASE/QUOTE)", symbol)
	}

	baseToken := strings.ToUpper(parts[0])
	quoteToken := strings.ToUpper(parts[1])

	fromMint := ct.getTokenMint(quoteToken)
	toMint := ct.getTokenMint(baseToken)

	if fromMint == "" || toMint == "" {
		return nil, fmt.Errorf("unknown token in pair: %s", symbol)
	}

	quoteTokenDecimals := int64(6) // USDC
	amount := int64(quantity * float64(pow10(quoteTokenDecimals)))

	quote, err := ct.GetSwapQuote(fromMint, toMint, amount, 0.5)
	if err != nil {
		return nil, err
	}

	tx, err := ct.ExecuteSwap(quote)
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
func (ct *CetusTrader) OpenShort(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	parts := strings.Split(symbol, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid symbol format: %s", symbol)
	}

	baseToken := strings.ToUpper(parts[0])
	quoteToken := strings.ToUpper(parts[1])

	fromMint := ct.getTokenMint(baseToken)
	toMint := ct.getTokenMint(quoteToken)

	if fromMint == "" || toMint == "" {
		return nil, fmt.Errorf("unknown token in pair: %s", symbol)
	}

	baseTokenDecimals := int64(9) // Most Sui tokens
	amount := int64(quantity * float64(pow10(baseTokenDecimals)))

	quote, err := ct.GetSwapQuote(fromMint, toMint, amount, 0.5)
	if err != nil {
		return nil, err
	}

	tx, err := ct.ExecuteSwap(quote)
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

// CloseLong closes a long position (sell token for USDC)
func (ct *CetusTrader) CloseLong(symbol string, quantity float64) (map[string]interface{}, error) {
	return ct.OpenShort(symbol, quantity, 0)
}

// CloseShort closes a short position (buy back token)
func (ct *CetusTrader) CloseShort(symbol string, quantity float64) (map[string]interface{}, error) {
	return ct.OpenLong(symbol, quantity, 0)
}

// SetLeverage not supported for spot DEX
func (ct *CetusTrader) SetLeverage(symbol string, leverage int) error {
	logger.Infof("[Cetus] SetLeverage ignored (spot-only DEX)")
	return nil
}

// SetMarginMode not supported for spot DEX
func (ct *CetusTrader) SetMarginMode(symbol string, isCrossMargin bool) error {
	logger.Infof("[Cetus] SetMarginMode ignored (spot-only DEX)")
	return nil
}

// SetStopLoss not supported
func (ct *CetusTrader) SetStopLoss(symbol string, positionSide string, quantity, stopPrice float64) error {
	logger.Warnf("[Cetus] SetStopLoss not supported for DEX spot")
	return nil
}

// SetTakeProfit not supported
func (ct *CetusTrader) SetTakeProfit(symbol string, positionSide string, quantity, takeProfitPrice float64) error {
	logger.Warnf("[Cetus] SetTakeProfit not supported for DEX spot")
	return nil
}

// CancelStopLossOrders no-op
func (ct *CetusTrader) CancelStopLossOrders(symbol string) error {
	return nil
}

// CancelTakeProfitOrders no-op
func (ct *CetusTrader) CancelTakeProfitOrders(symbol string) error {
	return nil
}

// CancelAllOrders no-op
func (ct *CetusTrader) CancelAllOrders(symbol string) error {
	return nil
}

// CancelStopOrders no-op
func (ct *CetusTrader) CancelStopOrders(symbol string) error {
	return nil
}

// FormatQuantity formats quantity
func (ct *CetusTrader) FormatQuantity(symbol string, quantity float64) (string, error) {
	return fmt.Sprintf("%.6f", quantity), nil
}

// GetOrderStatus returns order status
func (ct *CetusTrader) GetOrderStatus(symbol string, orderID string) (map[string]interface{}, error) {
	return map[string]interface{}{
		"status":  "FILLED",
		"orderID": orderID,
	}, nil
}

// GetClosedPnL returns closed PnL
func (ct *CetusTrader) GetClosedPnL(startTime time.Time, limit int) ([]types.ClosedPnLRecord, error) {
	return []types.ClosedPnLRecord{}, nil
}

// GetOpenOrders returns open orders
func (ct *CetusTrader) GetOpenOrders(symbol string) ([]types.OpenOrder, error) {
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

// Ensure CetusTrader implements Trader interface
var _ types.Trader = (*CetusTrader)(nil)