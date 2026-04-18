package jupiter

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"nofx/trader/types"
)

func TestJupiterTraderInterface(t *testing.T) {
	var _ types.Trader = (*JupiterTrader)(nil)
}

func TestNewJupiterTrader(t *testing.T) {
	trader := NewJupiterTrader("", false)
	assert.NotNil(t, trader)
	
	trader = NewJupiterTrader("test_key", true)
	assert.NotNil(t, trader)
}