package aerodrome

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"nofx/trader/types"
)

func TestAerodromeTraderInterface(t *testing.T) {
	var _ types.Trader = (*AerodromeTrader)(nil)
}

func TestNewAerodromeTrader(t *testing.T) {
	trader := NewAerodromeTrader("", false)
	assert.NotNil(t, trader)
	
	trader = NewAerodromeTrader("test_key", true)
	assert.NotNil(t, trader)
}