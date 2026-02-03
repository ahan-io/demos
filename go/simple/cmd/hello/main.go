package main

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"syscall"
	"time"

	"github.com/avast/retry-go"
)

func Retry_demo() {
	err := retry.Do(
		func() error {
			_, err := http.Get("http://example.com")
			return err
		},
		retry.Delay(time.Second),
		retry.Attempts(3),
		retry.DelayType(retry.FixedDelay),
	)
	if err != nil {
		fmt.Println("请求失败：", err)
	} else {
		fmt.Println("请求成功")
	}

	err = retry.Do(
		func() error {
			_, err := http.Get("http://notexisthhahaha.com")
			return err
		},
		retry.Delay(time.Second),
		retry.Attempts(3),
		retry.DelayType(retry.FixedDelay),
	)
	if err != nil {
		fmt.Println("请求失败：", err)
	} else {
		fmt.Println("请求成功")
	}

}

func CalculateDirSpaceDemo() {
	var stat syscall.Statfs_t
	executable, err := os.Executable()
	if err != nil {
		panic(err)
	}

	// 获取当前文件所在的目录
	dir := filepath.Dir(executable)
	err = syscall.Statfs(dir, &stat)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

	// 计算剩余空间
	availableSpace := stat.Bavail * uint64(stat.Bsize)

	fmt.Printf("Available space in %s: %d bytes\n", dir, availableSpace)
}

func main() {
	// Get a greeting message and print it.

	Retry_demo()
	CalculateDirSpaceDemo()
	fmt.Println("All Demo completed.")

}
