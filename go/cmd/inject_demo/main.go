package main

import (
	"errors"
	"fmt"
	"reflect"

	"github.com/pingcap/failpoint"
)

type Empty struct {
}

func Cmd() error {
	if val, _err_ := failpoint.Eval(FailpointName(Empty{}, "Cmd", "ErrorX")); _err_ == nil {
		if tmpstr, ok := val.(string); ok {
			return errors.New(tmpstr)
		}
	}
	return nil
}

func FailpointName(packageStruct any, funcName string, name string) string {
	return reflect.TypeOf(packageStruct).PkgPath() + ":" + funcName + ":" + name
}

func main() {
	// 激活故障点
	failpoint.Enable(FailpointName(Empty{}, "Cmd", "ErrorX"), "return(\"error when test\")")
	// 返回 hahah，相当于我们让 Cmd 函数返回我们想要的 error
	fmt.Println(Cmd())
	// 取消故障点
	failpoint.Disable(FailpointName(Empty{}, "Cmd", "ErrorX"))
	// 返回 nil
	fmt.Println(Cmd())
	fmt.Println(FailpointName(Empty{}, "Cmd", "ErrorX"))

}
