package main

import (
	"fmt"
	"os"
	"sync"

	"github.com/panjf2000/ants/v2"
)

func wrapTaskFunc(i int, wg *sync.WaitGroup) func() {
	return func() {
		fmt.Println(i)
		wg.Done()
	}
}

func main() {
	defer ants.Release()

	var wg sync.WaitGroup

	// Use the pool with a function,
	// set 10 to the capacity of goroutine pool and 1 second for expired duration.
	p, err := ants.NewPool(10)
	if err != nil {
		os.Exit(1)
	}

	defer p.Release()
	// Submit tasks one by one.
	for i := 0; i < 10; i++ {
		wg.Add(1)
		_ = p.Submit(wrapTaskFunc(i, &wg))
	}
	wg.Wait()
}
