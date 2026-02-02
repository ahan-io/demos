package util

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAdd(t *testing.T) {
	// Setup

	defer func() {
		// Teardown
		fmt.Println("TestAdd finished")
	}()

	if !assert.Equal(t, 4, Add(1, 2)) {
		return
	}
	assert.Equal(t, 3, Add(1, 2))
	fmt.Println("here")
}

func TestExit(t *testing.T) {
	// Setup

	defer func() {
		// Teardown
		fmt.Println("TestExit finished")
	}()

	require.Equal(t, 3, 2)
}
