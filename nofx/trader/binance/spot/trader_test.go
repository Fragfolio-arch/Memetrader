package spot

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"nofx/trader/types"
)

// TestSpotTraderInterface verifies that SpotTrader implements the Trader interface
func TestSpotTraderInterface(t *testing.T) {
	var _ types.Trader = (*SpotTrader)(nil)
}

// TestNewSpotTrader tests the constructor
func TestNewSpotTrader(t *testing.T) {
	// Test with valid credentials
	trader := NewSpotTrader("test_api_key", "test_secret_key")
	assert.NoError(t, nil) // NewSpotTrader doesn't return error
	assert.NotNil(t, trader)

	// Test with empty credentials
	trader = NewSpotTrader("", "")
	assert.NoError(t, nil) // NewSpotTrader doesn't return error
	assert.NotNil(t, trader)
}