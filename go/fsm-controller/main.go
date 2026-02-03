package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ================= 类型定义 =================

type State string

const (
	StateCreating State = "Creating"
	StateRunning  State = "Running"
	StateDeleting State = "Deleting"
	StateFailed   State = "Failed"
	StateUnknown  State = "Unknown"
)

// Resource 代表我们要管控的资源
type Resource struct {
	ID        string
	Status    State
	UpdatedAt time.Time
}

// ================= 模拟数据库 (Store) =================

type MockDB struct {
	sync.RWMutex
	data map[string]*Resource
}

func (db *MockDB) GetAll() []*Resource {
	db.RLock()
	defer db.RUnlock()
	res := make([]*Resource, 0, len(db.data))
	for _, v := range db.data {
		res = append(res, v)
	}
	return res
}

func (db *MockDB) UpdateStatus(id string, status State) {
	db.Lock()
	defer db.Unlock()
	if r, ok := db.data[id]; ok {
		r.Status = status
		r.UpdatedAt = time.Now()
		fmt.Printf("[DB] Resource %s status updated to %s\n", id, status)
	}
}

// ================= 控制器 (Controller) =================

type Controller struct {
	db       *MockDB
	notifyCh chan string   // 用于接收外部通知的 Channel
	interval time.Duration // 轮询周期
}

func NewController(db *MockDB) *Controller {
	return &Controller{
		db:       db,
		notifyCh: make(chan string, 10),
		interval: 5 * time.Second,
	}
}

// Notify 外部调用，通知 Controller 某个资源变了
func (c *Controller) Notify(id string) {
	c.notifyCh <- id
}

// Run 启动控制器
func (c *Controller) Run(ctx context.Context) {
	fmt.Println("🚀 Controller started...")

	// 启动周期性扫描
	ticker := time.NewTicker(c.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			fmt.Println("🔍 Periodic scanning all resources...")
			c.reconcileAll()
		case id := <-c.notifyCh:
			fmt.Printf("⚡ Event received for resource: %s\n", id)
			c.reconcileOne(id)
		}
	}
}

// reconcileAll 扫描所有资源
func (c *Controller) reconcileAll() {
	resources := c.db.GetAll()
	for _, r := range resources {
		c.processState(r)
	}
}

// reconcileOne 处理单个资源
func (c *Controller) reconcileOne(id string) {
	// 实际场景下会从 DB 查出最新状态
	c.db.RLock()
	r, ok := c.db.data[id]
	c.db.RUnlock()
	if ok {
		c.processState(r)
	}
}

// processState 状态机核心逻辑：根据当前状态执行预期操作
func (c *Controller) processState(r *Resource) {
	switch r.Status {
	case StateCreating:
		fmt.Printf("🛠️  Handling CREATING for %s: Allocating infrastructure...\n", r.ID)
		// 模拟操作成功后跳转到 Running
		c.db.UpdateStatus(r.ID, StateRunning)

	case StateRunning:
		fmt.Printf("🟢 Handling RUNNING for %s: Health checking...\n", r.ID)
		// 如果检查失败，可以转为 Failed

	case StateDeleting:
		fmt.Printf("🗑️  Handling DELETING for %s: Releasing resources...\n", r.ID)
		// 模拟删除完成后移出 DB
		c.db.Lock()
		delete(c.db.data, r.ID)
		c.db.Unlock()
		fmt.Printf("✅ Resource %s deleted.\n", r.ID)

	case StateFailed:
		fmt.Printf("❌ Handling FAILED for %s: Triggering alert or retry...\n", r.ID)

	default:
		fmt.Printf("❓ Unknown state for %s\n", r.ID)
	}
}

// ================= 入口函数 =================

func main() {
	// 1. 初始化模拟数据
	db := &MockDB{
		data: map[string]*Resource{
			"res-1": {ID: "res-1", Status: StateCreating, UpdatedAt: time.Now()},
			"res-2": {ID: "res-2", Status: StateRunning, UpdatedAt: time.Now()},
		},
	}

	// 2. 初始化控制器
	ctrl := NewController(db)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 3. 异步启动控制器
	go ctrl.Run(ctx)

	// 4. 模拟外部干预
	time.Sleep(2 * time.Second)
	fmt.Println("\n--- External User action: Delete res-2 ---")
	db.UpdateStatus("res-2", StateDeleting)
	ctrl.Notify("res-2") // 立即通知控制器，不用等下个 5s 周期

	// 让程序运行一段时间观察输出
	time.Sleep(10 * time.Second)
	fmt.Println("Terminating demo...")
}
