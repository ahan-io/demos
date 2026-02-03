package errno

type ErrorCode uint32

// 自定义自己的错误类型，包括错误码、错误描述等
type Error struct {
	Code   ErrorCode
	Msg    string
	Detail string
}

func NewError(code ErrorCode, msg string) *Error {
	return &Error{Code: code, Msg: msg, Detail: ""}
}

// Error implements error interface.
func (e *Error) Error() string {
	return e.Msg
}
