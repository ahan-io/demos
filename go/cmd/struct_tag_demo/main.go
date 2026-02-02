package main

import (
	"fmt"
	"reflect"
)

type User struct {
	Name  string `json:"name" db:"user_name"`
	Age   int    `json:"age" db:"user_age"`
	Email string `json:"email" db:"-"`
}

func main() {
	field, found := reflect.TypeOf(User{}).FieldByName("Name")
	if !found {
		return
	}
	jsonTag := field.Tag.Get("json")
	fmt.Println(jsonTag)
}
