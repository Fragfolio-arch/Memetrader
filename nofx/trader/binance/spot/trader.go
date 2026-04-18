package spot

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"nofx/logger"
	"nofx/trader/types"

	"github.com/adshao/go-binance/v2"
)

// SpotTrader Binance spot trader
type SpotTrader struct {
	client *binance.Client

	// Balance cache
	cachedBalance     map[string]interface{}
	balanceCacheTime  time.Time
	balanceCacheMutex sync.RWMutex

	// Position cache (for spot, positions are just asset balances)
	cachedBalances    map[string]interface{}
	balancesCacheTime time.Time
	balancesCacheMutex sync.RWMutex

	// Trading pair precision cache (symbol -> stepSize)
	stepSizeCache     map[string]float64
	stepSizeCacheMutex sync.RWMutex

	// Cache duration (15 seconds)
	cacheDuration time.Duration
}

// NewSpotTrader creates a spot trader
func NewSpotTrader(apiKey, secretKey string) *SpotTrader {
	client := binance.NewClient(apiKey, secretKey)
	trader := &SpotTrader{
		client:        client,
		cacheDuration: 15 * time.Second,
		stepSizeCache: make(map[string]float64),
	}
	return trader
}

// getSymbolFormat converts standard symbol to Binance format (e.g. BTCUSDT)
func (t *SpotTrader) getSymbolFormat(symbol string) string {
	return strings.ToUpper(strings.ReplaceAll(symbol, "/", ""))
}

// getBaseAndQuote extracts base and quote currencies from symbol
func (t *SpotTrader) getBaseAndQuote(symbol string) (base, quote string) {
	symbol = t.getSymbolFormat(symbol)
	// Try to split by common quote currencies
	for _, quoteCurrency := range []string{"USDT", "BUSD", "USDC", "BTC", "ETH"} {
		if strings.HasSuffix(symbol, quoteCurrency) {
			base := strings.TrimSuffix(symbol, quoteCurrency)
			if base != "" {
				return base, quoteCurrency
			}
		}
	}
	// Default fallback
	return symbol, "USDT"
}

// getStepSize retrieves the step size for a trading pair
func (t *SpotTrader) getStepSize(symbol string) float64 {
	// Check cache first
	t.stepSizeCacheMutex.RLock()
	if step, ok := t.stepSizeCache[symbol]; ok {
		t.stepSizeCacheMutex.RUnlock()
		return step
	}
	t.stepSizeCacheMutex.RUnlock()

	// Call public API directly to get exchange information
	url := fmt.Sprintf("https://api.binance.com/api/v3/exchangeInfo?symbol=%s", t.getSymbolFormat(symbol))
	resp, err := http.Get(url)
	if err != nil {
		logger.Infof("⚠️ [Binance Spot] Failed to get exchange info for %s: %v", symbol, err)
		return 0.000001 // Default to very small step
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		logger.Infof("⚠️ [Binance Spot] Failed to read exchange info for %s: %v", symbol, err)
		return 0.000001
	}

	var result struct {
		Symbols []struct {
			Symbol string `json:"symbol"`
			Filters []struct {
				FilterType string `json:"filterType"`
				StepSize   string `json:"stepSize"`
			} `json:"filters"`
		} `json:"symbols"`
	}

	if err := json.Unmarshal(body, &result); err != nil {
		logger.Infof("⚠️ [Binance Spot] Failed to parse exchange info for %s: %v", symbol, err)
		return 0.000001
	}

	if len(result.Symbols) == 0 {
		logger.Infof("⚠️ [Binance Spot] No symbol info found for %s", symbol)
		return 0.000001
	}

	// Find LOT_SIZE filter
	var stepSize string
	for _, filter := range result.Symbols[0].Filters {
		if filter.FilterType == "LOT_SIZE" {
			stepSize = filter.StepSize
			break
		}
	}

	if stepSize == "" {
		logger.Infof("⚠️ [Binance Spot] LOT_SIZE filter not found for %s", symbol)
		return 0.000001
	}

	step, err := strconv.ParseFloat(stepSize, 64)
	if err != nil {
		logger.Infof("⚠️ [Binance Spot] Failed to parse step size for %s: %v", symbol, err)
		return 0.000001
	}

	// Cache result
	t.stepSizeCacheMutex.Lock()
	t.stepSizeCache[symbol] = step
	t.stepSizeCacheMutex.Unlock()

	logger.Infof("📊 [Binance Spot] %s stepSize: %v", symbol, step)
	return step
}

// GetBalance Get account balance
func (t *SpotTrader) GetBalance() (map[string]interface{}, error) {
	t.balanceCacheMutex.RLock()
	if len(t.cachedBalance) > 0 && time.Since(t.balanceCacheTime) < t.cacheDuration {
		defer t.balanceCacheMutex.RUnlock()
		return t.cachedBalance, nil
	}
	t.balanceCacheMutex.RUnlock()

	resp, err := t.client.NewGetAccountService().Do(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to get account balance: %w", err)
	}

	balances := make(map[string]interface{})
	for _, balance := range resp.Balances {
		free, _ := strconv.ParseFloat(balance.Free, 64)
		locked, _ := strconv.ParseFloat(balance.Locked, 64)
		total := free + locked
		if total > 0 {
			balances[balance.Asset] = total
		}
	}

	t.balanceCacheMutex.Lock()
	t.cachedBalance = balances
	t.balanceCacheTime = time.Now()
	t.balanceCacheMutex.Unlock()

	return balances, nil
}

// GetPositions Get all positions (for spot, this returns asset balances with value > 0)
func (t *SpotTrader) GetPositions() ([]map[string]interface{}, error) {
	balances, err := t.GetBalance()
	if err != nil {
		return nil, err
	}

	var positions []map[string]interface{}
	for asset, quantity := range balances {
		if quantity.(float64) > 0 {
			position := map[string]interface{}{
				"symbol": asset,
				"quantity": quantity,
				"side": "LONG", // Spot only has long positions
				"entryPrice": 0.0, // Not applicable for spot in this context
				"markPrice": 0.0, // Not applicable for spot in this context
				"unrealizedPnl": 0.0, // Not tracked for spot
				"positionValue": 0.0, // Not tracked for spot
				"leverage": 1, // Spot doesn't use leverage
				"marginType": "spot",
				"isolatedWallet": 0.0, // Not applicable for spot
			}
			positions = append(positions, position)
		}
	}

	return positions, nil
}

// OpenLong Open long position (buy)
func (t *SpotTrader) OpenLong(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	// For spot trading, leverage is ignored (always 1x)
	if leverage != 1 {
		logger.Infof("⚠️ [Binance Spot] Leverage ignored for spot trading (forced to 1x)")
	}

	quantityStr := strconv.FormatFloat(quantity, 'f', 8, 64) // 8 decimal places precision for quantity
	symbolFormatted := t.getSymbolFormat(symbol)

	resp, err := t.client.NewCreateOrderService().
		Symbol(symbolFormatted).
		Side(binance.SideTypeBuy).
		Type(binance.OrderTypeMarket).
		Quantity(quantityStr).
		Do(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to place buy order: %w", err)
	}

	return map[string]interface{}{
		"orderId": resp.OrderID,
		"symbol":  symbol,
		"side":    "BUY",
		"status":  strings.ToUpper(string(resp.Status)),
	}, nil
}

// OpenShort Open short position (not supported on spot)
func (t *SpotTrader) OpenShort(symbol string, quantity float64, leverage int) (map[string]interface{}, error) {
	return nil, fmt.Errorf("short selling is not supported on spot markets")
}

// CloseLong Close long position (sell)
func (t *SpotTrader) CloseLong(symbol string, quantity float64) (map[string]interface{}, error) {
	quantityStr := strconv.FormatFloat(quantity, 'f', 8, 64)
	symbolFormatted := t.getSymbolFormat(symbol)

	resp, err := t.client.NewCreateOrderService().
		Symbol(symbolFormatted).
		Side(binance.SideTypeSell).
		Type(binance.OrderTypeMarket).
		Quantity(quantityStr).
		Do(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to place sell order: %w", err)
	}

	return map[string]interface{}{
		"orderId": resp.OrderID,
		"symbol":  symbol,
		"side":    "SELL",
		"status":  strings.ToUpper(string(resp.Status)),
	}, nil
}

// CloseShort Close short position (not supported on spot)
func (t *SpotTrader) CloseShort(symbol string, quantity float64) (map[string]interface{}, error) {
	return nil, fmt.Errorf("short selling is not supported on spot markets")
}

// SetLeverage Set leverage (no-op for spot)
func (t *SpotTrader) SetLeverage(symbol string, leverage int) error {
	logger.Infof("⚠️ [Binance Spot] SetLeverage ignored (spot trading uses 1x leverage)")
	return nil
}

// SetMarginMode Set position mode (no-op for spot)
func (t *SpotTrader) SetMarginMode(symbol string, isCrossMargin bool) error {
	logger.Infof("⚠️ [Binance Spot] SetMarginMode ignored (spot trading doesn't use margin modes)")
	return nil
}

// GetMarketPrice Get market price
func (t *SpotTrader) GetMarketPrice(symbol string) (float64, error) {
	prices, err := t.client.NewListPricesService().
		Symbol(t.getSymbolFormat(symbol)).
		Do(context.Background())
	if err != nil {
		return 0, fmt.Errorf("failed to get market price: %w", err)
	}
	
	if len(prices) == 0 {
		return 0, fmt.Errorf("price not found for symbol %s", symbol)
	}
	
	price, err := strconv.ParseFloat(prices[0].Price, 64)
	if err != nil {
		return 0, fmt.Errorf("failed to parse price: %w", err)
	}
	
	return price, nil
}

// SetStopLoss Set stop-loss order (using OCO or separate order)
func (t *SpotTrader) SetStopLoss(symbol string, positionSide string, quantity, stopPrice float64) error {
	// For simplicity, we'll create a separate stop-loss order
	// In practice, you might want to use OCO orders
	quantityStr := strconv.FormatFloat(quantity, 'f', 8, 64)
	stopPriceStr := strconv.FormatFloat(stopPrice, 'f', 8, 64)

	_, err := t.client.NewCreateOrderService().
		Symbol(t.getSymbolFormat(symbol)).
		Side(binance.SideTypeSell).
		Type(binance.OrderTypeStopLoss).
		Quantity(quantityStr).
		StopPrice(stopPriceStr).
		Do(context.Background())
	if err != nil {
		return fmt.Errorf("failed to set stop-loss order: %w", err)
	}
	return nil
}

// SetTakeProfit Set take-profit order
func (t *SpotTrader) SetTakeProfit(symbol string, positionSide string, quantity, takeProfitPrice float64) error {
	// For simplicity, we'll create a separate take-profit order
	quantityStr := strconv.FormatFloat(quantity, 'f', 8, 64)
	takeProfitPriceStr := strconv.FormatFloat(takeProfitPrice, 'f', 8, 64)
	symbolFormatted := t.getSymbolFormat(symbol)

	_, err := t.client.NewCreateOrderService().
		Symbol(symbolFormatted).
		Side(binance.SideTypeSell).
		Type(binance.OrderTypeTakeProfit).
		Quantity(quantityStr).
		StopPrice(takeProfitPriceStr).
		Do(context.Background())
	if err != nil {
		return fmt.Errorf("failed to set take-profit order: %w", err)
	}
	return nil
}

// CancelStopLossOrders Cancel only stop-loss orders
func (t *SpotTrader) CancelStopLossOrders(symbol string) error {
	// Note: Binance API doesn't have a direct way to cancel only stop-loss orders
	// We would need to get all open orders and filter by type
	// For now, return error indicating limitation
	return fmt.Errorf("individual stop-loss order cancellation not implemented for Binance spot")
}

// CancelTakeProfitOrders Cancel only take-profit orders
func (t *SpotTrader) CancelTakeProfitOrders(symbol string) error {
	// Note: Binance API doesn't have a direct way to cancel only take-profit orders
	// We would need to get all open orders and filter by type
	// For now, return error indicating limitation
	return fmt.Errorf("individual take-profit order cancellation not implemented for Binance spot")
}

// CancelAllOrders Cancel all pending orders for this symbol
func (t *SpotTrader) CancelAllOrders(symbol string) error {
	symbolFormatted := t.getSymbolFormat(symbol)
	_, err := t.client.NewCancelOpenOrdersService().
		Symbol(symbolFormatted).
		Do(context.Background())
	if err != nil {
		return fmt.Errorf("failed to cancel all orders: %w", err)
	}
	return nil
}

// CancelStopOrders Cancel stop-loss/take-profit orders for this symbol
func (t *SpotTrader) CancelStopOrders(symbol string) error {
	// Similar to above, would need to filter orders by type
	return fmt.Errorf("conditional order cancellation not implemented for Binance spot")
}

// FormatQuantity Format quantity to correct precision
func (t *SpotTrader) FormatQuantity(symbol string, quantity float64) (string, error) {
	stepSize := t.getStepSize(symbol)
	if stepSize <= 0 {
		return "", fmt.Errorf("invalid step size for symbol %s", symbol)
	}

	// Calculate precision from step size
	precision := 0
	if stepSize < 1 {
		stepStr := strconv.FormatFloat(stepSize, 'f', -1, 64)
		if idx := strings.Index(stepStr, "."); idx >= 0 {
			precision = len(stepStr) - idx - 1
		}
	}

	// Round down to nearest step
	step := math.Floor(quantity/stepSize) * stepSize
	format := fmt.Sprintf("%%.%df", precision)
	return fmt.Sprintf(format, step), nil
}

// GetOrderStatus Get order status
func (t *SpotTrader) GetOrderStatus(symbol string, orderID string) (map[string]interface{}, error) {
	symbolFormatted := t.getSymbolFormat(symbol)
	orderIDInt, err := strconv.ParseInt(orderID, 10, 64)
	if err != nil {
		return nil, fmt.Errorf("invalid order ID: %w", err)
	}

	resp, err := t.client.NewGetOrderService().
		Symbol(symbolFormatted).
		OrderID(orderIDInt).
		Do(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to get order status: %w", err)
	}

	price, _ := strconv.ParseFloat(resp.Price, 64)

	return map[string]interface{}{
		"status":      strings.ToUpper(string(resp.Status)),
		"avgPrice":    price,
		"executedQty": 0.0, // Spot API doesn't return executed quantity in getOrder, would need separate query
		"commission":  0.0, // Spot API doesn't return commission in getOrder, would need separate query
		"orderId":     resp.OrderID,
	}, nil
}

// GetClosedPnL Get closed position PnL records from exchange
// Note: For spot, we don't have traditional PnL records like futures
// This would need to be implemented based on trade history
func (t *SpotTrader) GetClosedPnL(startTime time.Time, limit int) ([]types.ClosedPnLRecord, error) {
	// This is a simplified implementation - in practice you'd need to
	// get trade history and calculate PnL from buy/sell pairs
	return []types.ClosedPnLRecord{}, nil
}

// GetOpenOrders Get open/pending orders from exchange
func (t *SpotTrader) GetOpenOrders(symbol string) ([]types.OpenOrder, error) {
	symbolFormatted := t.getSymbolFormat(symbol)
	orders, err := t.client.NewListOpenOrdersService().
		Symbol(symbolFormatted).
		Do(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to get open orders: %w", err)
	}

	var result []types.OpenOrder
	for _, order := range orders {
		side := "BUY"
		if order.Side == binance.SideTypeSell {
			side = "SELL"
		}

		positionSide := "LONG"
		if side == "SELL" {
			positionSide = "SHORT" // For tracking purposes in spot
		}

		price, _ := strconv.ParseFloat(order.Price, 64)
		quantity, _ := strconv.ParseFloat(order.OrigQuantity, 64)

		result = append(result, types.OpenOrder{
			OrderID:      strconv.FormatInt(order.OrderID, 10),
			Symbol:       symbol,
			Side:         side,
			PositionSide: positionSide,
			Type:         string(order.Type),
			Price:        price,
			StopPrice:    0, // Spot orders don't have stop prices in the same way as futures
			Quantity:     quantity,
			Status:       string(order.Status),
		})
	}

	return result, nil
}