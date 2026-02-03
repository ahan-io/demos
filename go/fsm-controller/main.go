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
	// TODO 在实际项目中，这里还需要判断前置状态是否满足要求，即状态机的流转是否是合理的。
	if r, ok := db.data[id]; ok {
		r.Status = status
		r.UpdatedAt = time.Now()
		fmt.Printf("[DB] Resource %s status updated to %s\n", id, status)
	}
}

// ================= 控制器 (Controller) =================

type workerEntry struct {
	state  State
	cancel context.CancelFunc
}

type Controller struct {
	db       *MockDB
	notifyCh chan string   // 用于接收外部通知的 Channel
	interval time.Duration // 轮询周期
	mu       sync.Mutex
	workers  map[string]*workerEntry
}

func NewController(db *MockDB) *Controller {
	return &Controller{
		db:       db,
		notifyCh: make(chan string, 10),
		interval: 5 * time.Second,
		workers:  make(map[string]*workerEntry),
	}
}

func needAsync(state State) bool {
	switch state {
	case StateCreating, StateDeleting:
		return true
	default:
		return false
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
			c.reconcileAll(ctx)
		case id := <-c.notifyCh:
			fmt.Printf("⚡ Event received for resource: %s\n", id)
			c.reconcileOne(ctx, id)
		}
	}
}

// reconcileAll 扫描所有资源
func (c *Controller) reconcileAll(ctx context.Context) {
	resources := c.db.GetAll()
	for _, r := range resources {
		c.processState(ctx, r)
	}
}

// reconcileOne 处理单个资源
func (c *Controller) reconcileOne(ctx context.Context, id string) {
	// 实际场景下会从 DB 查出最新状态
	c.db.RLock()
	r, ok := c.db.data[id]
	c.db.RUnlock()
	if ok {
		c.processState(ctx, r)
	}
}

// processState 状态机核心逻辑：根据当前状态执行预期操作
func (c *Controller) processState(ctx context.Context, r *Resource) {
	if needAsync(r.Status) {
		c.ensureWorker(ctx, r.ID, r.Status)
		return
	}

	switch r.Status {
	case StateRunning:
		fmt.Printf("🟢 Handling RUNNING for %s: Health checking...\n", r.ID)
		// 如果检查失败，可以转为 Failed

	case StateFailed:
		fmt.Printf("❌ Handling FAILED for %s: Triggering alert or retry...\n", r.ID)

	default:
		fmt.Printf("❓ Unknown state for %s\n", r.ID)
	}
}

func (c *Controller) ensureWorker(ctx context.Context, id string, state State) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if entry, ok := c.workers[id]; ok {
		if entry.state == state {
			fmt.Printf("⏭️  Worker already running for %s (%s)\n", id, state)
			return
		}

		// 状态变化，取消旧 worker
		// 如果已经资源已经有一个 worker 正在另外一个状态，为了避免冲突，我们调用 cancel 尽力取消后，等待 worker 结束，不启动新的协程。
		fmt.Printf("🔄 State changed for %s: cancel %s worker\n", id, entry.state)
		entry.cancel()
		fmt.Printf("🚧 Wait for the worker of %s, it is running for state %s\n", id, entry.state)
		return
	}

	ctx, cancel := context.WithCancel(ctx)
	c.workers[id] = &workerEntry{
		state:  state,
		cancel: cancel,
	}

	fmt.Printf("🚧 Starting %s worker for %s\n", state, id)
	go c.resourceWorker(ctx, id, state)
}

func (c *Controller) resourceWorker(ctx context.Context, id string, state State) {
	defer func() {
		c.mu.Lock()
		delete(c.workers, id)
		c.mu.Unlock()
		fmt.Printf("🧹 Worker for %s (%s) exited\n", id, state)
	}()

	switch state {

	case StateCreating:
		fmt.Printf("🛠️  Creating resource %s...\n", id)
		select {
		case <-time.After(4 * time.Second):
			c.db.UpdateStatus(id, StateRunning)
			fmt.Printf("✅ Resource %s created\n", id)

		case <-ctx.Done():
			fmt.Printf("⚠️  Creating worker for %s canceled\n", id)
			return
		}

	case StateDeleting:
		fmt.Printf("🗑️  Deleting resource %s...\n", id)
		select {
		case <-time.After(5 * time.Second):
			c.db.Lock()
			delete(c.db.data, id)
			c.db.Unlock()
			fmt.Printf("✅ Resource %s deleted\n", id)

		case <-ctx.Done():
			fmt.Printf("⚠️  Deleting worker for %s canceled\n", id)
			return
		}
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
	time.Sleep(60 * time.Second)
	fmt.Println("Terminating demo...")
}
