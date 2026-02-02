package main

import (
	"context"
	"fmt"
	"time"
)

func funcWithContext(ctx context.Context) {
	for {
		select {
		case x, ok := <-ctx.Done():
			fmt.Println("context2 is over,%v,%v", x, ok)
			return
		default:
			time.Sleep(1 * time.Second)
			fmt.Println("context2 running")
		}
	}
}

func funcWithContextValue(ctx context.Context) {
	for {
		select {
		case x, ok := <-ctx.Done():
			fmt.Println("context3 is over,%v,%v", x, ok)
			return
		default:
			fmt.Println("key:%s, value:%v", "key", ctx.Value("value"))
			time.Sleep(1 * time.Second)
			fmt.Println("context3 running")
		}
	}
}

func main() {
	// 带超时的context
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	go handle(ctx, 500*time.Millisecond)
	select {
	case <-ctx.Done():
		fmt.Println("main", ctx.Err())
	}

	// 不带超时的context
	ctx2, cancel2 := context.WithCancel(context.Background())
	defer cancel2()
	go funcWithContext(ctx2)
	go funcWithContext(ctx2)
	go funcWithContext(ctx2)
	time.Sleep(5 * time.Second)
	cancel2()
	// 预期是3个协程都退出
	time.Sleep(2 * time.Second)

	// 携带各种上下文的context
	ctx3 := context.WithValue(ctx2, "key", "value")
	go funcWithContextValue(ctx3)
	go funcWithContextValue(ctx3)
	fmt.Println("new to routines done")
	time.Sleep(3 * time.Second)

}

func handle(ctx context.Context, duration time.Duration) {
	select {
	case <-ctx.Done():
		fmt.Println("handle", ctx.Err())
	case <-time.After(duration):
		fmt.Println("process request with", duration)
	}
}
