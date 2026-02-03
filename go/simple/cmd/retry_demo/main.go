package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/avast/retry-go/v4"
)

func main() {
	// 尝试执行的代码，默认10次
	err := retry.Do(func() error {
		fmt.Println("Trying...")
		return errors.New("temporary error")
	})
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	// 自定义重试次数和延迟
	err = retry.Do(
		func() error {
			return errors.New("an error occurred")
		},
		retry.Attempts(5),                 // 尝试 5 次
		retry.DelayType(retry.FixedDelay), // 使用固定延迟
		retry.Delay(2*time.Second),        // 每次重试之间等待 2 秒
	)

	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	// 使用条件来控制重试
	err = retry.Do(
		func() error {
			return errors.New("non-retriable error")
		},
		retry.RetryIf(func(err error) bool {
			// 仅当错误符合条件时才重试
			return err.Error() == "temporary error"
		}),
	)
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	// 指数回退策略
	err = retry.Do(
		func() error {
			return errors.New("an error")
		},
		retry.DelayType(retry.BackOffDelay), // 使用指数回退延迟
	)
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// 使用上下文控制
	err = retry.Do(
		func() error {
			return errors.New("operation failed")
		},
		retry.Context(ctx), // 使用上下文控制超时
	)
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	// 自定义错误处理函数
	err = retry.Do(
		func() error {
			return errors.New("error example")
		},
		retry.OnRetry(func(n uint, err error) {
			fmt.Printf("Attempt %d: %v\n", n+1, err)
		}),
	)
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}

	err = retry.Do(
		func() error {
			return errors.New("example error")
		},
		retry.Attempts(3),
		retry.Delay(1*time.Second),
		retry.MaxJitter(500*time.Millisecond), // 增加抖动
	)
	if err != nil {
		fmt.Printf("Final error: %v\n", err)
	}
}
