# 定义变量
BUILD_TIME := $(shell date "+%F %T")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-parse HEAD)
TAG := $(shell echo $(GIT_BRANCH) | rev | cut -d '/' -f1 | rev)

GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
BIN_NAME ?= hello

all: build

build: 
	mkdir -p output
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/html_to_image cmd/html_to_image/main.go
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/${BIN_NAME} cmd/hello/main.go
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/context_demo cmd/context_demo/main.go
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/inject_demo cmd/inject_demo/main.go
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/pool_demo cmd/pool_demo/pool_demo.go
	CGO_ENABLED=0 go build -ldflags="-s -w -X 'main.BuildTime=${BUILD_TIME}' -X 'main.GitBranch=${GIT_BRANCH}' -X 'main.GitCommit=${GIT_COMMIT}'" -o output/struct_tag_demo cmd/struct_tag_demo/main.go

clean: 
	rm -rf output

test: 
	$(GOTEST) -v -cover ./...

run:
	$(GOBUILD) -o $(BIN_NAME) -v ./...
	./$(BIN_NAME)
