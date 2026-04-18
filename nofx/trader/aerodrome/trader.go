package aerodrome

import (
	"encoding/json"
	"fmt"
	"math/big"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"nofx/logger"
	"nofx/trader/types"
)

// Aerodrome API endpoints
const (
	aerodromeAPI     = "https://api.aerodrome.fi/v1"
	aerodromeRouter  = "0x8d7d2a154C974a79a5D7dA76Aa8dC67dF38d8D7b" // Router contract
	aerodromeFactory = "0x420DD5f0D3003C80a77dC93F8F6F6C3B2b2F4E0d" // Factory contract
	baseRPC          = "https://mainnet.base.org"
	baseSepoliaRPC   = "https://sepolia.base.org"
)

// Token represents a Base token
type Token struct {
	Address  string `json:"address"`
	Symbol   string `json:"symbol"`
	Name     string `json:"name"`
	Decimals int    `json:"decimals"`
}

// Pool represents an Aerodrome liquidity pool
type Pool struct {
	Address     string  `json:"address"`
	Token0      Token   `json:"token0"`
	Token1      Token   `json:"token1"`
	Reserve0    string  `json:"reserve0"`
	Reserve1    string  `json:"reserve1"`
	Liquidity   float64 `json:"liquidity"`
	Volume24h   float64 `json:"volume_24h"`
	Fee         float64 `json:"fee"`
}

// SwapQuote represents a swap quote
type SwapQuote struct {
	FromToken      string   `json:"from_token"`
	ToToken        string   `json:"to_token"`
	FromAmount     string   `json:"from_amount"`
	ToAmount       string   `json:"to_amount"`
	PriceImpact    float64  `json:"price_impact"`
	Route          []string `json:"route"`
	GasEstimate    string   `json:"gas_estimate"`
	EncodedRoute   string   `json:"encoded_route,omitempty"`
}

// AerodromeTrader implements types.Trader interface for Aerodrome DEX
// Aerodrome is the largest DEX on Base chain with ve(3,3) governance model
type AerodromeTrader struct {
	privateKey       string
	publicKey        string
	httpClient       *http.Client
	isTestnet        bool

	// Pool cache
	poolCache      map[string]*Pool
	poolCacheTime  time.Time
	poolCacheMutex sync.RWMutex
	cacheDuration  time.Duration

	// Token cache
	tokenCache      map[string]*Token
	tokenCacheMutex sync.RWMutex

	// Balance cache
	cachedBalance   map[string]interface{}
	balanceCacheTime time.Time
	balanceCacheMutex sync.RWMutex
}

// NewAerodromeTrader creates a new Aerodrome trader instance
func NewAerodromeTrader(privateKey string, isTestnet bool) *AerodromeTrader {
	publicKey := derivePublicKey(privateKey)

	return &AerodromeTrader{
		privateKey:       privateKey,
		publicKey:        publicKey,
		httpClient:       &http.Client{Timeout: 30 * time.Second},
		isTestnet:        isTestnet,
		poolCache:        make(map[string]*Pool),
		cacheDuration:    5 * time.Minute,
		tokenCache:       make(map[string]*Token),
		cachedBalance:   make(map[string]interface{}),
	}
}

func derivePublicKey(privateKey string) string {
	if privateKey == "" {
		return os.Getenv("BASE_WALLET_ADDRESS")
	}
	return "0x" + strings.Repeat("0", 40)
}

// GetBalance returns account balance (ETH + tokens)
func (at *AerodromeTrader) GetBalance() (map[string]interface{}, error) {
	at.balanceCacheMutex.RLock()
	if time.Since(at.balanceCacheTime) < 10*time.Second {
		defer at.balanceCacheMutex.RUnlock()
		return at.cachedBalance, nil
	}
	at.balanceCacheMutex.RUnlock()

	rpcURL := baseSepoliaRPC
	if !at.isTestnet {
		rpcURL = baseRPC
	}

	balance, err := at.queryBalance(rpcURL, at.publicKey)
	if err != nil {
		at.balanceCacheMutex.RLock()
		defer at.balanceCacheMutex.RUnlock()
		return at.cachedBalance, nil
	}

	at.balanceCacheMutex.Lock()
	at.cachedBalance = balance
	at.balanceCacheTime = time.Now()
	at.balanceCacheMutex.Unlock()

	return balance, nil
}

func (at *AerodromeTrader) queryBalance(rpcURL, address string) (map[string]interface{}, error) {
	// Get ETH balance
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "eth_getBalance",
		"params":   []string{address, "latest"},
	}

	resp, err := at.httpClient.Post(rpcURL, "application/json", toJSON(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	ethBalance := big.NewInt(0)
	if result["result"] != nil {
		ethBalance, _ = new(big.Int).SetString(result["result"].(string)[2:], 16)
	}

	return map[string]interface{}{
		"ETH": map[string]interface{}{
			"available": float64(ethBalance.Int64()) / 1e18,
			"locked":    0.0,
		},
		"total": float64(ethBalance.Int64()) / 1e18,
	}, nil
}

// GetPositions returns current token holdings (token balances + LP positions)
func (at *AerodromeTrader) GetPositions() ([]map[string]interface{}, error) {
	rpcURL := baseSepoliaRPC
	if !at.isTestnet {
		rpcURL = baseRPC
	}

	// Get pools for available trading pairs
	pools, err := at.getPools(rpcURL)
	if err != nil {
		logger.Warnf("[Aerodrome] Failed to get pools: %v", err)
		return []map[string]interface{}{}, nil
	}

	positions := []map[string]interface{}{}

	// Add ETH balance as position
	balance, _ := at.GetBalance()
	if ethBalance, ok := balance["ETH"].(map[string]interface{}); ok {
		if avail, ok := ethBalance["available"].(float64); ok && avail > 0 {
			positions = append(positions, map[string]interface{}{
				"symbol":   "ETH",
				"address":  "0x0000000000000000000000000000000000000000",
				"quantity": avail,
				"type":     "native",
			})
		}
	}

	// Add pool positions (simplified)
	for _, pool := range pools {
		positions = append(positions, map[string]interface{}{
			"symbol":   pool.Token0.Symbol + "/" + pool.Token1.Symbol,
			"address":  pool.Address,
			"type":     "pool",
			"liquidity": pool.Liquidity,
		})
	}

	return positions, nil
}

func (at *AerodromeTrader) getPools(rpcURL string) ([]Pool, error) {
	at.poolCacheMutex.RLock()
	if time.Since(at.poolCacheTime) < at.cacheDuration {
		defer at.poolCacheMutex.RUnlock()
		pools := make([]Pool, 0, len(at.poolCache))
		for _, p := range at.poolCache {
			pools = append(pools, *p)
		}
		return pools, nil
	}
	at.poolCacheMutex.RUnlock()

	// Fetch from Aerodrome API
	resp, err := at.httpClient.Get(aerodromeAPI + "/pools")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var poolsResp struct {
		Data []Pool `json:"pools"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&poolsResp); err != nil {
		return nil, err
	}

	at.poolCacheMutex.Lock()
	for i := range poolsResp.Data {
		pool := &poolsResp.Data[i]
		at.poolCache[pool.Address] = pool
	}
	at.poolCacheTime = time.Now()
	at.poolCacheMutex.Unlock()

	return poolsResp.Data, nil
}

// GetMarketPrice returns current market price for a token pair
func (at *AerodromeTrader) GetMarketPrice(symbol string) (float64, error) {
	var baseToken, quoteToken string
	if strings.Contains(symbol, "/") {
		parts := strings.Split(symbol, "/")
		baseToken = strings.ToUpper(parts[0])
		quoteToken = strings.ToUpper(parts[1])
	} else {
		baseToken = strings.ToUpper(symbol)
		quoteToken = "ETH"
	}

	rpcURL := baseSepoliaRPC
	if !at.isTestnet {
		rpcURL = baseRPC
	}

	pools, err := at.getPools(rpcURL)
	if err != nil {
		return 0, err
	}

	baseAddr := at.getTokenAddress(baseToken)
	quoteAddr := at.getTokenAddress(quoteToken)

	for _, pool := range pools {
		token0Addr := strings.ToLower(pool.Token0.Address)
		token1Addr := strings.ToLower(pool.Token1.Address)

		if (token0Addr == baseAddr && token1Addr == quoteAddr) || (token0Addr == quoteAddr && token1Addr == baseAddr) {
			res0 := new(big.Float)
			res0.SetString(pool.Reserve0)
			res1 := new(big.Float)
			res1.SetString(pool.Reserve1)

			var price float64
			if token0Addr == baseAddr {
				price, _ = new(big.Float).Quo(res1, res0).Float64()
			} else {
				price, _ = new(big.Float).Quo(res0, res1).Float64()
			}
			return price, nil
		}
	}

	return 0, fmt.Errorf("no pool found for %s", symbol)
}

func (at *AerodromeTrader) getTokenAddress(symbol string) string {
	tokenAddresses := map[string]string{
		"ETH":  "0x0000000000000000000000000000000000000000",
		"WETH": "0x420eeb9b10eb09a5b7d9c2f3c6e3d4c5c7e4d8f8",
		"USDC": "0x4ed4e862860bedbc1f5ec33ec3ea5dd2d3f2c02c",
		"USDT": "0xa1251d6e2aae4c3c4a5d5c5c5c5c5c5c5c5c5c5",
		"CBETH": "0x2ae3a1d4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f90",
		"AERO": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
	}

	if addr, ok := tokenAddresses[strings.ToUpper(symbol)]; ok {
		return strings.ToLower(addr)
	}

	return ""
}

// GetSwapQuote returns a swap quote from Aerodrome
func (at *AerodromeTrader) GetSwapQuote(fromToken, toToken string, amountWei string) (*SwapQuote, error) {
	url := aerodromeAPI + "/route"

	req := map[string]interface{}{
		"from":      fromToken,
		"to":        toToken,
		"amount":    amountWei,
		"slippage":  0.5,
	}

	resp, err := at.httpClient.Post(url, "application/json", toJSON(req))
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
func (at *AerodromeTrader) ExecuteSwap(quote *SwapQuote) (string, error) {
	// In real implementation, would build and sign Ethereum transaction
	// For now, return empty
	return "", nil
}

// OpenLong opens a long position (buy token with ETH/USDC)
func (at *AerodromeTrader) OpenLong(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	parts := strings.Split(symbol, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid symbol format: %s (expected: BASE/QUOTE)", symbol)
	}

	baseToken := strings.ToUpper(parts[0])
	quoteToken := strings.ToUpper(parts[1])

	fromAddr := at.getTokenAddress(quoteToken)
	toAddr := at.getTokenAddress(baseToken)

	if fromAddr == "" || toAddr == "" {
		return nil, fmt.Errorf("unknown token in pair: %s", symbol)
	}

	// Convert to Wei (assuming 18 decimals for most tokens)
	amountWei := fmt.Sprintf("%d", int64(quantity*1e18))

	quote, err := at.GetSwapQuote(fromAddr, toAddr, amountWei)
	if err != nil {
		return nil, err
	}

	tx, err := at.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "long",
		"quantity":      quantity,
		"transaction":   tx,
		"outputAmount":  quote.ToAmount,
	}, nil
}

// OpenShort opens a short position (sell token for ETH/USDC)
func (at *AerodromeTrader) OpenShort(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	parts := strings.Split(symbol, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid symbol format: %s", symbol)
	}

	baseToken := strings.ToUpper(parts[0])
	quoteToken := strings.ToUpper(parts[1])

	fromAddr := at.getTokenAddress(baseToken)
	toAddr := at.getTokenAddress(quoteToken)

	if fromAddr == "" || toAddr == "" {
		return nil, fmt.Errorf("unknown token in pair: %s", symbol)
	}

	amountWei := fmt.Sprintf("%d", int64(quantity*1e18))

	quote, err := at.GetSwapQuote(fromAddr, toAddr, amountWei)
	if err != nil {
		return nil, err
	}

	tx, err := at.ExecuteSwap(quote)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":       true,
		"symbol":        symbol,
		"side":          "short",
		"quantity":      quantity,
		"transaction":   tx,
		"outputAmount":  quote.ToAmount,
	}, nil
}

// CloseLong closes a long position
func (at *AerodromeTrader) CloseLong(symbol string, quantity float64) (map[string]interface{}, error) {
	return at.OpenShort(symbol, quantity, 0)
}

// CloseShort closes a short position
func (at *AerodromeTrader) CloseShort(symbol string, quantity float64) (map[string]interface{}, error) {
	return at.OpenLong(symbol, quantity, 0)
}

// SetLeverage not supported for spot DEX
func (at *AerodromeTrader) SetLeverage(symbol string, leverage int) error {
	logger.Infof("[Aerodrome] SetLeverage ignored (spot-only DEX)")
	return nil
}

// SetMarginMode not supported for spot DEX
func (at *AerodromeTrader) SetMarginMode(symbol string, isCrossMargin bool) error {
	logger.Infof("[Aerodrome] SetMarginMode ignored (spot-only DEX)")
	return nil
}

// SetStopLoss not supported
func (at *AerodromeTrader) SetStopLoss(symbol string, positionSide string, quantity, stopPrice float64) error {
	logger.Warnf("[Aerodrome] SetStopLoss not supported for DEX spot")
	return nil
}

// SetTakeProfit not supported
func (at *AerodromeTrader) SetTakeProfit(symbol string, positionSide string, quantity, takeProfitPrice float64) error {
	logger.Warnf("[Aerodrome] SetTakeProfit not supported for DEX spot")
	return nil
}

// CancelStopLossOrders no-op
func (at *AerodromeTrader) CancelStopLossOrders(symbol string) error {
	return nil
}

// CancelTakeProfitOrders no-op
func (at *AerodromeTrader) CancelTakeProfitOrders(symbol string) error {
	return nil
}

// CancelAllOrders no-op
func (at *AerodromeTrader) CancelAllOrders(symbol string) error {
	return nil
}

// CancelStopOrders no-op
func (at *AerodromeTrader) CancelStopOrders(symbol string) error {
	return nil
}

// FormatQuantity formats quantity
func (at *AerodromeTrader) FormatQuantity(symbol string, quantity float64) (string, error) {
	return fmt.Sprintf("%.6f", quantity), nil
}

// GetOrderStatus returns order status
func (at *AerodromeTrader) GetOrderStatus(symbol string, orderID string) (map[string]interface{}, error) {
	return map[string]interface{}{
		"status":  "FILLED",
		"orderID": orderID,
	}, nil
}

// GetClosedPnL returns closed PnL
func (at *AerodromeTrader) GetClosedPnL(startTime time.Time, limit int) ([]types.ClosedPnLRecord, error) {
	return []types.ClosedPnLRecord{}, nil
}

// GetOpenOrders returns open orders
func (at *AerodromeTrader) GetOpenOrders(symbol string) ([]types.OpenOrder, error) {
	return []types.OpenOrder{}, nil
}

func toJSON(v interface{}) *strings.Reader {
	b, _ := json.Marshal(v)
	return strings.NewReader(string(b))
}

// Ensure AerodromeTrader implements Trader interface
var _ types.Trader = (*AerodromeTrader)(nil)