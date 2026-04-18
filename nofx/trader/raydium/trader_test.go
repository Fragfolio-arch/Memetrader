package raydium

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"nofx/trader/types"
)

func TestRaydiumTraderInterface(t *testing.T) {
	var _ types.Trader = (*RaydiumTrader)(nil)
}

func TestNewRaydiumTrader(t *testing.T) {
	trader := NewRaydiumTrader("", false)
	assert.NotNil(t, trader)
	
	trader = NewRaydiumTrader("test_key", true)
	assert.NotNil(t, trader)
}