package cetus

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"nofx/trader/types"
)

func TestCetusTraderInterface(t *testing.T) {
	var _ types.Trader = (*CetusTrader)(nil)
}

func TestNewCetusTrader(t *testing.T) {
	trader := NewCetusTrader("", false)
	assert.NotNil(t, trader)
	
	trader = NewCetusTrader("test_key", true)
	assert.NotNil(t, trader)
}