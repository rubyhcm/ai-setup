# 📚 Bộ Câu Hỏi & Đáp Án - Senior Go Engineer Interview

Với tư cách là một CTO/Architect, mình đánh giá cao việc tuyển dụng Senior qua khả năng hiểu "tại sao" (why) hơn là "cái gì" (what). Một Senior Go Engineer thực thụ không chỉ viết code chạy được, mà phải viết code hiệu quả, dễ bảo trì và hiểu rõ cơ chế vận hành bên dưới của runtime.

**67 câu hỏi chất lượng cao** với đáp án chi tiết ở **Principal-level**, tập trung vào **tư duy hệ thống, concurrency, performance, và Go internals**.

## 📖 Cách sử dụng

- **Junior → Mid**: hỏi phần I + II cơ bản
- **Senior**: phải trả lời sâu phần II, III, IV
- **Principal**: phải làm tốt phần V + system design + trade-offs

### Legend:
- ✅ **Expected**: Những điểm cần có
- ❌ **Red flags**: Dấu hiệu yếu
- 🔥 **Senior+**: Điểm cộng senior
- 💡 **Mechanism/Example**: Cơ chế & ví dụ
- 🎯 **Production Insight**: Kinh nghiệm thực tế

---

## 🧠 I. Go Runtime & Internals (12 câu)

### 1. GMP Scheduler

**❓ Câu hỏi:**
Giải thích cơ chế của **G, M, P model**. Tại sao Go lại cần scheduler riêng mà không dùng trực tiếp OS threads? Điều gì xảy ra khi tạo một goroutine?

**✅ Expected**
- G (Goroutine): lightweight task (~2KB stack, growable)
- M (Machine): OS thread
- P (Processor): logical scheduler (giữ run queue + context)
- M phải có P mới chạy được G
- Work stealing giữa các P khi run queue rỗng

**💡 Mechanism**
1. `go func()` → tạo G và push vào **local run queue của P**
2. M gắn với P → lấy G từ queue để execute
3. Nếu queue rỗng → **work stealing từ P khác** hoặc global queue
4. Syscall block → M detach khỏi P → P chạy G khác

**🎯 Production Insight**
- Go dùng **M:N scheduling** để tạo hàng triệu Goroutine mà không bị overhead context switch như OS Thread (2MB vs 2KB)
- Long CPU-bound loop → cần `runtime.Gosched()` hoặc break để yield
- Scheduling ở user space → latency optimization tốt hơn OS scheduler

**❌ Red flags**
- "goroutine = thread nhẹ" (sai lầm khái niệm)
- Không biết P là gì

**🔥 Senior+**
- Nhắc đến run queue (local/global)
- Hiểu syscall/blocking ảnh hưởng scheduler như thế nào

---

### 2. Preemption

**❓ Câu hỏi:**
Giải thích cơ chế `preemption` trong Go scheduler. Phiên bản Go 1.14 đã cải thiện điều này như thế nào?

**✅ Expected**
- Trước 1.14: cooperative preemption (chỉ ngắt tại function call)
- Từ 1.14: **asynchronous preemption** (signal-based)
- Tránh goroutine chiếm CPU lâu

**🎯 Production Insight**
- Go ≥1.14 có thể ngắt vòng lặp vô hạn mà không cần function call
- Cải thiện fairness và latency cho concurrent workload

---

### 3. Garbage Collector (GC)

**❓ Câu hỏi:**
Cách thức hoạt động của GC trong Go (tri-color marking, Pacing, Write Barrier, STW phases)? Go làm thế nào để giảm thiểu "Stop the World"?

**✅ Expected**
- Concurrent mark & sweep
- **Tri-color marking** (white/grey/black objects)
- STW rất ngắn (~sub-ms) chỉ ở initial mark + mark termination
- Write barrier đảm bảo correctness khi mutator chạy song song

**💡 Mechanism**
- White: chưa scan
- Grey: đang scan
- Black: đã scan xong
- Write barrier track pointer changes trong concurrent phase

**🎯 Production Insight**
- Go ưu tiên **latency over throughput**
- GOGC điều chỉnh trade-off giữa GC frequency và memory usage

**❌ Red flags**
- "GC pause lâu" (kiến thức cũ, trước Go 1.5)
- Không biết concurrent GC

**🔥 Senior+**
- Mention write barrier chi tiết
- Hiểu trade-off latency vs throughput
- Biết tune GOGC, GOMEMLIMIT

---

### 4. GC Tuning

**❓ Câu hỏi:**
Khi nào Go trigger GC? Làm sao để tune GC?

**✅ Expected**
- Trigger khi heap growth > GOGC threshold
- Formula: `next_gc = live_heap * (1 + GOGC/100)`
- Default GOGC=100 (trigger khi heap gấp đôi)

**💡 Tuning Strategy**
- GOGC thấp → GC thường xuyên → latency ổn định, memory thấp
- GOGC cao → ít GC → memory cao hơn, throughput tốt hơn
- GOMEMLIMIT (Go 1.19+): soft limit để GC aggressive khi gần limit

**🎯 Production Insight**
- Container environment: set GOMEMLIMIT = 90% container limit
- Latency-sensitive: GOGC=50-75
- Batch processing: GOGC=200-400

---

### 5. Escape Analysis

**❓ Câu hỏi:**
Cơ chế **Escape Analysis** hoạt động như thế nào? Cho ví dụ thực tế.

**✅ Expected**
- Compiler quyết định Stack vs Heap allocation
- Escape khi: return pointer, closure capture, interface boxing, size quá lớn
- Tool: `go build -gcflags="-m"`

**💡 Mechanism**
- Nếu compiler không chắc lifetime → heap (an toàn hơn)
- Stack: fast allocation/deallocation, no GC
- Heap: slower, GC managed

**🎯 Production Insight**
- Interface conversion = hidden allocation
- Pointer return từ function thường escape
- Optimize hot path bằng cách giảm escape

**❌ Red flags**
- "new() thì heap, var thì stack" (hoàn toàn sai)

**🔥 Senior+**
- Biết đọc compiler output `-m`
- Optimize allocation based on escape analysis

---

### 6. Stack vs Heap

**❓ Câu hỏi:**
Sự khác biệt giữa Stack và Heap allocation. Go quyết định allocation như thế nào?

**✅ Expected**

| Aspect | Stack | Heap |
|--------|-------|------|
| Speed | Fast | Slow |
| Management | Auto (LIFO) | GC |
| Size | Small (growable) | Large |
| Lifetime | Function scope | Until GC |

**💡 Go Special**
- Stack tự động grow (contiguous stack, copy-on-grow)
- Initial stack ~2KB → có thể grow đến GB nếu cần

**🎯 Production Insight**
- Stack allocation không cần GC → performance win
- Goroutine many → stack memory accumulation

---

### 7. Memory Alignment

**❓ Câu hỏi:**
**Memory Alignment** và padding trong `struct` là gì? Tại sao thứ tự khai báo field lại quan trọng?

**✅ Expected**
- CPU đọc memory theo word (8-byte trên 64-bit)
- Padding để align fields
- Thứ tự field ảnh hưởng struct size

**💡 Example**
```go
// BAD: 24 bytes (bool + 7 padding + int64 + int64)
type A struct {
    b bool   // 1 byte + 7 padding
    x int64  // 8 bytes
    y int64  // 8 bytes
}

// GOOD: 17 bytes → align to 24 (int64 + int64 + bool)
type B struct {
    x int64  // 8 bytes
    y int64  // 8 bytes
    b bool   // 1 byte
}
```

**🎯 Production Insight**
- Sắp xếp field từ lớn → nhỏ để minimize padding
- Affects cache locality và memory usage
- Critical cho high-volume data structures

**❌ Red flags**
- Chưa từng nghe về memory alignment

**🔥 Senior+**
- Hiểu cache line (64 bytes)
- Biết false sharing issue

---

### 8. Zero Value

**❓ Câu hỏi:**
Triết lý zero value trong Go và tại sao nó mạnh mẽ?

**✅ Expected**
- Every type usable ngay khi declare
- No "null pointer exception" cho zero value types

**💡 Example**
```go
var m sync.Mutex  // Usable ngay
var b bytes.Buffer  // Usable ngay
var wg sync.WaitGroup  // Usable ngay
```

**🎯 Impact**
- API đơn giản hơn (ít constructor)
- Safe by default
- Ít initialization bugs

---

### 9. Defer

**❓ Câu hỏi:**
Giải thích cách defer được implement internally. Cost implications?

**✅ Expected**
- LIFO stack execution
- Trước đây: allocate defer object
- Go 1.13+: inline defer optimization (fast path)

**💡 Cost**
```go
// BAD: defer in loop
for i := 0; i < 1e6; i++ {
    defer f()  // Allocate 1M defer objects
}

// GOOD: manual cleanup
for i := 0; i < 1e6; i++ {
    f()
}
```

**❌ Red flags**
- Nghĩ defer "free" (không có cost)

**🔥 Senior+**
- Hiểu trade-off readability vs performance
- Biết khi nào tránh defer trong hot path

---

### 10. Memory Leak

**❓ Câu hỏi:**
Memory leak trong Go thường xảy ra ở đâu? (Goroutines treo, Slice references, Time.Ticker)

**✅ Expected**
- Goroutines treo (blocked channel, no cancel context)
- Slice giữ reference tới large underlying array
- `time.Ticker` không stop
- Circular references với finalizers

**💡 Example**
```go
// Leak: goroutine blocked forever
ch := make(chan int)
go func() {
    ch <- 1  // No receiver
}()

// Fix: always have receiver or use context
ctx, cancel := context.WithTimeout(context.Background(), time.Second)
defer cancel()
```

**🎯 Production Insight**
- Detect: `pprof` goroutine profile, `runtime.NumGoroutine()`
- Always use context for goroutine lifecycle
- Stop tickers: `defer ticker.Stop()`

---

### 11. Slice Internals

**❓ Câu hỏi:**
Tại sao `slice` lại có `len` và `cap`? Điều gì xảy ra với underlying array khi `append` vượt quá `cap`?

**✅ Expected**
- `len`: số phần tử hiện tại
- `cap`: sức chứa underlying array
- `append` quá cap → allocate new array (thường 2x)

**💡 Optimization**
```go
// BAD: multiple reallocations
var s []int
for i := 0; i < 1000; i++ {
    s = append(s, i)
}

// GOOD: pre-allocate
s := make([]int, 0, 1000)
for i := 0; i < 1000; i++ {
    s = append(s, i)
}
```

**🎯 Production Insight**
- Avoid slice growth trong hot path
- Use `make([]T, len, cap)` khi biết trước size

---

### 12. Map Internals

**❓ Câu hỏi:**
Cơ chế hoạt động của `map` trong Go (Hash buckets, Evacuation). Tại sao `map` không concurrency-safe?

**✅ Expected**
- Hash table với buckets (8 key-value pairs per bucket)
- Incremental evacuation khi grow
- **NOT concurrency-safe** (fatal error, not panic)

**💡 Mechanism**
- Load factor cao → trigger grow
- Evacuation diễn ra dần (incremental) để tránh lag
- Concurrent read+write → fatal error (không recover được)

**🎯 Production Insight**
- Use `sync.Map` cho concurrent access (read-heavy workload)
- Hoặc protect map với `sync.RWMutex`

**❌ Red flags**
- Không biết map có evacuation mechanism

---

## ⚙️ II. Concurrency & Parallelism (12 câu)

### 13. Concurrency vs Parallelism

**❓ Câu hỏi:**
Sự khác biệt giữa concurrency và parallelism trong Go?

**✅ Expected**
- Concurrency: program structure (dealing with multiple things at once)
- Parallelism: execution (doing multiple things at once)
- Concurrency enables parallelism

**💡 Rob Pike's Definition**
- Concurrency is about **composition**
- Parallelism is about **execution**

---

### 14. Channel vs Mutex

**❓ Câu hỏi:**
Channel vs mutex – khi nào dùng cái nào?

**✅ Expected**

| Aspect | Channel | Mutex |
|--------|---------|-------|
| Purpose | Communication | Protect shared memory |
| Cost | Higher | Lower |
| Use case | Pipeline, signaling | State sharing |

**💡 Go Proverb**
- "Share memory by communicating" (channel)
- "Don't communicate by sharing memory" (mutex - avoid)

**🎯 Production Insight**
- State sharing → mutex (faster)
- Pipeline/Worker pattern → channel (cleaner)
- Channel cost > mutex → don't over-use

**❌ Red flags**
- "channel always better" (dogmatic)

**🔥 Senior+**
- Biết khi nào dùng đúng abstraction
- Measure performance impact

---

### 15. Buffered vs Unbuffered Channels

**❓ Câu hỏi:**
Sự khác biệt về mặt vận hành, performance và real-world use cases?

**✅ Expected**
- Unbuffered: synchronization point (sender/receiver must meet)
- Buffered: async, decoupling, throughput

**💡 Use Cases**
- Unbuffered: signaling, strict ordering
- Buffered (size=1): latest value
- Buffered (size=N): bounded queue, backpressure

**🎯 Real-world**
- Logging system → buffered (high throughput)
- RPC request/response → unbuffered (sync)
- Worker queue → buffered (smooth traffic)

---

### 16. Closed Channels

**❓ Câu hỏi:**
Điều gì xảy ra khi gửi dữ liệu vào một `closed channel`? Và nhận từ một `closed channel`?

**✅ Expected**
- Send to closed channel → **panic**
- Receive from closed channel → zero value + `ok=false`
- Close closed channel → panic

**💡 Pattern**
```go
// Sender closes
ch := make(chan int)
go func() {
    defer close(ch)
    for i := 0; i < 10; i++ {
        ch <- i
    }
}()

// Receiver detects close
for v := range ch {
    fmt.Println(v)
}
```

**🎯 Production Insight**
- **Only sender should close** channel
- Use `range` to detect close automatically

---

### 17. Goroutine Leaks

**❓ Câu hỏi:**
Common goroutine leaks là gì? Cách phát hiện và debug trong production?

**✅ Expected**
- Blocked channel send/recv without timeout
- Missing context cancel
- Infinite loop without exit condition
- HTTP request without timeout

**💡 Detection**
```go
// Use pprof
import _ "net/http/pprof"
// Access /debug/pprof/goroutine

// Or programmatic
fmt.Println(runtime.NumGoroutine())
```

**🎯 Production Insight**
- Always use context for lifecycle management
- Set timeouts for all I/O operations
- Monitor goroutine count in production

**❌ Red flags**
- Không biết goroutine leak exists

**🔥 Senior+**
- Context-driven lifecycle design
- Automatic leak detection với pprof

---

### 18. Race Condition

**❓ Câu hỏi:**
Cách phát hiện và xử lý **Race Condition** trong môi trường production?

**✅ Expected**
- Detect: `go run -race` hoặc `go test -race`
- Fix: mutex, atomic operations, hoặc channel

**💡 Example**
```go
// Race
var counter int
for i := 0; i < 100; i++ {
    go func() { counter++ }()
}

// Fix 1: Mutex
var mu sync.Mutex
for i := 0; i < 100; i++ {
    go func() {
        mu.Lock()
        counter++
        mu.Unlock()
    }()
}

// Fix 2: Atomic
var counter int64
for i := 0; i < 100; i++ {
    go func() {
        atomic.AddInt64(&counter, 1)
    }()
}
```

**🎯 Production Insight**
- Run `-race` in CI/CD
- Race detector has runtime overhead (~10x slower)

---

### 19. Context Package

**❓ Câu hỏi:**
Giải thích sâu về `context` package (cancelation, timeout, propagation). Tại sao không nên dùng `context.Value` cho tham số quan trọng?

**✅ Expected**
- Cancelation propagation
- Deadline/timeout management
- Request-scoped values (minimal use)

**💡 Context Tree**
```go
ctx := context.Background()
ctx1, cancel1 := context.WithTimeout(ctx, 5*time.Second)
ctx2, cancel2 := context.WithCancel(ctx1)
// Canceling ctx1 → cancels ctx2
```

**🎯 Anti-patterns**
- Dùng cho business data (type safety loss)
- Store large objects
- Use for function parameters (ngoại trừ request scope)

**❌ Red flags**
- Nhét mọi thứ vào context.Value

**🔥 Senior+**
- Context tree design cho complex flows
- Pass through layers properly

---

### 20. Worker Pool

**❓ Câu hỏi:**
Cách thiết kế **Worker Pool pattern**. Khi nào nên dùng và làm sao để kiểm soát số lượng goroutine hiệu quả?

**✅ Expected**
```go
jobs := make(chan Job, 100)
results := make(chan Result, 100)

// Create workers
for i := 0; i < numWorkers; i++ {
    go worker(jobs, results)
}

// Send jobs
go func() {
    for _, job := range allJobs {
        jobs <- job
    }
    close(jobs)
}()
```

**🎯 Worker Count Strategy**
- CPU-bound → `runtime.NumCPU()`
- I/O-bound → higher (10x - 100x cores)
- Test to find optimal number

**🔥 Senior+**
- Dynamic worker pool adjustment
- Graceful shutdown với context

---

### 21. Select Statement

**❓ Câu hỏi:**
Select statement fairness là gì? Có pitfalls nào?

**✅ Expected**
- Pseudo-random selection khi multiple cases ready
- Không guarantee fairness
- `default` case prevents blocking

**💡 Pitfall**
```go
// Can cause starvation
for {
    select {
    case <-highPriority:
        // This might starve lowPriority
    case <-lowPriority:
    }
}
```

**❌ Red flags**
- Nghĩ select deterministic

**🔥 Senior+**
- Biết starvation issue và cách fix (priority queuing)

---

### 22. Backpressure

**❓ Câu hỏi:**
Cách xử lý backpressure trong hệ thống Go?

**✅ Expected**
- Bounded queue/channel
- Rate limiting
- Drop policy (reject or shed load)
- Circuit breaker

**💡 Strategies**
```go
// 1. Bounded channel
jobs := make(chan Job, 1000)

// 2. Non-blocking send với select
select {
case jobs <- job:
    // Sent
default:
    // Drop or retry later
}

// 3. Rate limiting
limiter := rate.NewLimiter(100, 10) // 100 req/s, burst 10
limiter.Wait(ctx)
```

**🎯 Production Insight**
- Load shedding better than cascading failure
- Monitor queue depth

**🔥 Senior+**
- Circuit breaker pattern
- Adaptive rate limiting

---

### 23. sync.Mutex vs sync.RWMutex

**❓ Câu hỏi:**
Sự khác biệt và khi nào dùng cái nào để tối ưu?

**✅ Expected**
- Mutex: exclusive lock (1 writer OR 0 readers)
- RWMutex: multiple readers OR 1 writer
- RWMutex overhead cao hơn Mutex

**💡 When to Use**
- Read-heavy workload (90%+) → RWMutex
- Write-heavy or balanced → Mutex (simpler, faster)

**🎯 Benchmark First**
- RWMutex không phải lúc nào cũng nhanh hơn
- Lock contention cao → consider sharding

---

### 24. When to Avoid Goroutines

**❓ Câu hỏi:**
Khi nào không nên sử dụng goroutines?

**✅ Expected**
- Short tasks (overhead > benefit)
- High frequency calls (millions/sec)
- Sequential faster (no parallelism opportunity)
- Memory constrained (stack memory)

**💡 Example**
```go
// BAD: goroutine overhead > work
for i := 0; i < 1000; i++ {
    go func() { x++ }()  // Tiny work
}

// GOOD: batch work
const batchSize = 100
for i := 0; i < 1000; i += batchSize {
    go processBatch(i, batchSize)
}
```

---

## 🧩 III. Language Design & Patterns (10 câu)

### 25. Composition vs Inheritance

**❓ Câu hỏi:**
Tại sao Go không có `inheritance` mà lại dùng `composition`/embedding?

**✅ Expected**
- Tránh tight coupling
- Favor composition over inheritance
- Embedding cho code reuse

**💡 Embedding**
```go
type Base struct{}
func (b Base) Method() {}

type Child struct {
    Base  // Embedding (not inheritance)
}
// child.Method() works (method promotion)
```

**🎯 Benefit**
- Flat structure, easy to understand
- Avoid diamond problem
- Explicit dependencies

---

### 26. Interface

**❓ Câu hỏi:**
Interface trong Go – implicit vs explicit implementation? Duck Typing là gì?

**✅ Expected**
- Implicit satisfaction (duck typing)
- Small interfaces preferred (1-3 methods)
- "Accept interfaces, return structs"

**💡 Interface Internals**
- **iface**: 2 pointers (tab + data)
  - tab: type metadata + method table
  - data: actual value
- **eface** (empty interface): simpler (type + data)

**🎯 Design Principle**
- Interface defined by **consumer**, not producer
- Small interfaces more composable

**❌ Red flags**
- Large interfaces (10+ methods)
- Interface to mock everything

**🔥 Senior+**
- "Accept interface, return struct" pattern
- Interface segregation principle

---

### 27. Empty Interface

**❓ Câu hỏi:**
`interface{}`/`any` thực chất là gì bên dưới (eface/iface)? Tại sao nên tránh abuse empty interfaces?

**✅ Expected**
- Type-unsafe container
- Runtime type assertion needed
- Performance cost (allocation + indirection)

**💡 Use Sparingly**
```go
// OK uses
func Printf(format string, args ...interface{})
func MarshalJSON(v interface{})

// Avoid
type Config map[string]interface{}  // Lose type safety
```

**❌ Red flags**
- Abuse empty interface everywhere

**🔥 Senior+**
- Prefer generics (Go 1.18+) over empty interface

---

### 28. Pointer vs Value Receiver

**❓ Câu hỏi:**
Khi nào nên dùng con trỏ và khi nào nên dùng giá trị trong method receiver?

**✅ Expected**

| Use Pointer When | Use Value When |
|------------------|----------------|
| Modify receiver | Small immutable |
| Large struct | Primitive types |
| Consistency | Value semantics |

**💡 Rule**
- Một method dùng pointer → all methods nên dùng pointer

---

### 29. Functional Options Pattern

**❓ Câu hỏi:**
Tại sao pattern này phổ biến trong việc khởi tạo cấu hình object?

**✅ Expected**
```go
type Server struct {
    timeout time.Duration
    maxConn int
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func NewServer(opts ...Option) *Server {
    s := &Server{timeout: 30*time.Second}
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage
srv := NewServer(
    WithTimeout(10*time.Second),
    WithMaxConn(100),
)
```

**🎯 Benefits**
- Backward compatible
- Clear intent
- Defaults + overrides

---

### 30. Clean API Design

**❓ Câu hỏi:**
Cách thiết kế clean APIs trong Go (idiomatic Go)? Tại sao "Accept interfaces, return structs"?

**✅ Expected**
- Input as interface → flexible, mockable
- Output as struct → explicit, type-safe

**💡 Example**
```go
// Input interface (flexible)
type Storer interface {
    Store(key, val string) error
}

// Return struct (explicit)
func NewCache() *Cache { return &Cache{} }
```

**🎯 Benefit**
- Consumer can mock inputs easily
- Producer provides stable concrete output

---

### 31. Error Handling Philosophy

**❓ Câu hỏi:**
Triết lý "Errors are values". Tại sao không dùng `try-catch`?

**✅ Expected**
- Explicit error return (no exceptions)
- "Errors are values" → can be handled programmatically
- Check immediately

**💡 Wrapping**
```go
if err != nil {
    return fmt.Errorf("failed to process: %w", err)
}
```

**❌ Red flags**
- Ignore errors (`_ = err`)
- Generic error messages

**🔥 Senior+**
- Wrap với context (`%w` preserves error chain)
- Custom error types cho business logic

---

### 32. Error Types

**❓ Câu hỏi:**
Sự khác biệt giữa `errors.Is`, `errors.As`, sentinel error, wrapped error và custom error?

**✅ Expected**
- `errors.Is`: check sentinel error
- `errors.As`: type assertion to specific error type
- `%w` for wrapping (Go 1.13+)

**💡 Example**
```go
// Sentinel
var ErrNotFound = errors.New("not found")

if errors.Is(err, ErrNotFound) {}

// Custom type
type ValidationError struct { Field string }

var ve *ValidationError
if errors.As(err, &ve) {
    fmt.Println(ve.Field)
}
```

---

### 33. Panic & Recovery

**❓ Câu hỏi:**
Khi nào được phép dùng `panic`? Cách phục hồi từ `panic` trong một goroutine?

**✅ Expected**
- Panic cho unrecoverable errors only
- Recover chỉ trong defer
- Library không nên panic (return error)

**💡 Pattern**
```go
func safeCall() (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic: %v", r)
        }
    }()
    riskyOperation()
    return nil
}
```

---

### 34. Dependency Injection

**❓ Câu hỏi:**
DI trong Go không cần frameworks. Có nên dùng `Wire` hay `Uber Dig` không?

**✅ Expected**
- Constructor injection (manual)
- Interface-based decoupling
- Avoid global singletons

**💡 Example**
```go
type Service struct {
    repo Repository
    cache Cache
}

func NewService(repo Repository, cache Cache) *Service {
    return &Service{repo: repo, cache: cache}
}
```

**🎯 Framework?**
- Manual DI sufficient cho most projects
- Wire/Dig cho large codebases (reduce boilerplate)

**❌ Red flags**
- Global singleton variables

---

### 35. Project Structure

**❓ Câu hỏi:**
Cách cấu trúc một large Go project (Project Layout, Clean Architecture)?

**✅ Expected**
- `/cmd`: main applications
- `/internal`: private code
- `/pkg`: public libraries
- Domain-driven structure for business logic

**💡 Example**
```
project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── user/
│   ├── order/
│   └── payment/
└── pkg/
    └── api/
```

**❌ Red flags**
- Copy "clean architecture" without understanding

**🔥 Senior+**
- Structure theo domain (not layers)
- Avoid over-engineering

---

## 🚀 IV. Performance & Optimization (12 câu)

### 36. Profiling

**❓ Câu hỏi:**
Cách profile Go application? CPU vs memory profiling tools (pprof)?

**✅ Expected**
- CPU profile: hotspots (sampling)
- Heap profile: memory allocation
- Goroutine profile: leak detection
- Access: `/debug/pprof` endpoint

**💡 Usage**
```go
import _ "net/http/pprof"
go func() {
    http.ListenAndServe(":6060", nil)
}()

// View
go tool pprof http://localhost:6060/debug/pprof/profile
go tool pprof http://localhost:6060/debug/pprof/heap
```

**🎯 Workflow**
1. Measure (don't guess)
2. Profile to find hotspot
3. Optimize
4. Measure again

**🔥 Senior+**
- Flamegraph visualization
- Continuous profiling in production

---

### 37. High Memory Allocation

**❓ Câu hỏi:**
Nguyên nhân gây high memory allocation? Cách giảm thiểu allocation trong hot path?

**✅ Expected**
- JSON encoding/decoding (reflection)
- Slice growth (append without pre-allocation)
- Interface conversion
- String concatenation (use `strings.Builder`)

**💡 Detection**
```bash
go test -bench=. -benchmem
# Shows allocations per operation
```

---

### 38. GC Pressure

**❓ Câu hỏi:**
Cách giảm GC pressure?

**✅ Expected**
- Reuse objects (`sync.Pool`)
- Pre-allocate slices
- Avoid unnecessary allocations
- Use pointers wisely

**💡 Example**
```go
// BAD
for _, item := range items {
    result = append(result, expensive(item))
}

// GOOD
result := make([]Result, 0, len(items))
var buf bytes.Buffer
for _, item := range items {
    result = append(result, expensive(item, &buf))
    buf.Reset()
}
```

---

### 39. sync.Pool

**❓ Câu hỏi:**
Cách sử dụng `sync.Pool` để tái sử dụng đối tượng và giảm áp lực lên GC?

**✅ Expected**
- Temporary object reuse
- Reduce allocation pressure
- Pool cleared on each GC cycle

**💡 Usage**
```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

buf := bufferPool.Get().(*bytes.Buffer)
defer func() {
    buf.Reset()
    bufferPool.Put(buf)
}()
```

**❌ Red flags**
- Dùng như cache (objects evicted by GC)

**🔥 Senior+**
- Hiểu GC interaction (Pool cleared at GC)

---

### 40. Inlining

**❓ Câu hỏi:**
**Inlining** trong Go là gì? Nó giúp tăng tốc chương trình như thế nào?

**✅ Expected**
- Compiler replaces function call với function body
- Giảm call overhead
- Enable better optimizations (escape analysis)

**💡 Check**
```bash
go build -gcflags="-m"
# Shows inlining decisions
```

**🎯 Benefit**
- ~10ns saved per call
- Better for small, hot functions

---

### 41. JSON Optimization

**❓ Câu hỏi:**
So sánh hiệu năng `JSON encoding/decoding` tiêu chuẩn vs `easyjson`/`jsoniter`. Cách optimize?

**✅ Expected**
- Standard `encoding/json`: slow (reflection)
- `easyjson`: code generation → 2-3x faster
- `jsoniter`: drop-in replacement
- Reuse encoder/decoder

**💡 Optimization**
```go
// Reuse encoder
var encoderPool = sync.Pool{
    New: func() interface{} {
        return json.NewEncoder(nil)
    },
}
```

---

### 42. String/Byte Conversion

**❓ Câu hỏi:**
Tại sao `[]byte` ↔ `string` conversion tốn kém? Cách xử lý zero-copy?

**✅ Expected**
- `[]byte` ↔ `string` causes copy (strings immutable)
- Cost: O(n) memory + CPU

**💡 Zero-copy (unsafe)**
```go
import "unsafe"

func bytesToString(b []byte) string {
    return *(*string)(unsafe.Pointer(&b))
}
// ⚠️ Dangerous: b must not be modified
```

**🎯 Safe Alternative**
- Use `[]byte` throughout pipeline
- Convert to string only at final output

---

### 43. Benchmarking

**❓ Câu hỏi:**
Cách viết benchmark đúng cách. Ý nghĩa của `b.N` và `b.ReportAllocs()`?

**✅ Expected**
```go
func BenchmarkFoo(b *testing.B) {
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        Foo()
    }
}

// Run
go test -bench=. -benchmem
```

**💡 b.N**
- Auto-adjusted for statistical significance
- Run enough iterations for stable result

**🔥 Senior+**
- Compare before/after với benchstat
- Report allocations (`b.ReportAllocs()`)

---

### 44. Reflection

**❓ Câu hỏi:**
Reflection cost trong Go – khi nào acceptable?

**✅ Expected**
- Slow (dynamic type lookup)
- Bypasses compiler optimizations
- Use when: serialization, ORM, DI

**💡 Acceptable Use**
- One-time initialization
- Non-hot path
- When type safety needs flexibility

---

### 45. False Sharing

**❓ Câu hỏi:**
False sharing là gì và cách tránh?

**✅ Expected**
- Multiple threads modify different variables on same cache line (64 bytes)
- Causes cache invalidation ping-pong
- Huge performance degradation

**💡 Fix**
```go
// BAD
type Counter struct {
    a int64
    b int64
}

// GOOD: pad to separate cache lines
type Counter struct {
    a int64
    _ [7]int64  // Padding (64 bytes)
    b int64
}
```

---

### 46. Low-latency Services

**❓ Câu hỏi:**
Cách thiết kế low-latency Go services?

**✅ Expected**
- Minimize allocations (stack allocation preferred)
- Avoid blocking operations
- Pre-allocate resources
- Use `sync.Pool` for temp objects
- Profile regularly

**🎯 Techniques**
- Object pooling
- Lock-free data structures (atomic)
- Reduce GC pauses (GOGC tuning)

---

### 47. BCE

**❓ Câu hỏi:**
Giải thích về **Bounds Check Elimination**.

**✅ Expected**
- Compiler removes array bounds check khi chứng minh safe
- Significant speedup trong tight loops

**💡 Help Compiler**
```go
// Compiler can't eliminate check
for i := 0; i < len(a); i++ {
    x := a[i]
}

// Hint compiler
_ = a[n-1]  // Bounds check hint
for i := 0; i < n; i++ {
    x := a[i]  // No check needed
}
```

---

### 48. Docker Optimization

**❓ Câu hỏi:**
Tối ưu Docker Image cho Go (Multi-stage build, Distroless images, static vs dynamic linking)?

**✅ Expected**
- Multi-stage build
- Distroless/Alpine base
- Static linking (CGO_ENABLED=0)

**💡 Dockerfile**
```dockerfile
# Stage 1: Build
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o server

# Stage 2: Run
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/server /
CMD ["/server"]
```

**🎯 Result**
- ~1GB → ~20MB image size

---

## 🌐 V. Backend System Design with Go (14 câu)

### 49. High-throughput HTTP Service

**❓ Câu hỏi:**
Cách xây dựng high-throughput HTTP service trong Go?

**✅ Expected**
- HTTP keep-alive enabled
- Connection reuse
- Tune `http.Transport`:
  - MaxIdleConns
  - MaxIdleConnsPerHost
  - IdleConnTimeout

**💡 Configuration**
```go
transport := &http.Transport{
    MaxIdleConns:        100,
    MaxIdleConnsPerHost: 10,
    IdleConnTimeout:     90 * time.Second,
}
client := &http.Client{Transport: transport}
```

**🎯 Production**
- Monitor connection pool metrics
- Set timeouts (avoid hanging)

---

### 50. Framework Trade-offs

**❓ Câu hỏi:**
`net/http` vs frameworks (Gin, Fiber) – trade-offs?

**✅ Expected**

| net/http | Frameworks |
|----------|------------|
| Standard, stable | Feature-rich |
| Low overhead | Higher overhead |
| Verbose | Concise |

**🎯 Decision**
- Simple service → `net/http` + router (chi/gorilla)
- Complex REST API → Gin (middleware, validation)
- Ultra performance → Fiber (fasthttp)

**🔥 Senior+**
- Benchmark actual workload
- Consider team familiarity

---

### 51. Middleware

**❓ Câu hỏi:**
Cách implement **Middleware** trong Go HTTP server mà không dùng framework?

**✅ Expected**
```go
func middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Before
        log.Println("Request:", r.URL)

        next.ServeHTTP(w, r)

        // After
        log.Println("Response sent")
    })
}

// Chain
handler = middleware(handler)
```

**🎯 Common Middleware**
- Logging
- Auth
- Recovery (panic)
- CORS
- Rate limiting

---

### 52. Graceful Shutdown

**❓ Câu hỏi:**
Cách implement **Graceful Shutdown** cho HTTP Server hoặc Worker?

**✅ Expected**
```go
srv := &http.Server{Addr: ":8080"}

go func() {
    if err := srv.ListenAndServe(); err != http.ErrServerClosed {
        log.Fatal(err)
    }
}()

// Wait for interrupt
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

// Shutdown với timeout
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
if err := srv.Shutdown(ctx); err != nil {
    log.Fatal("Shutdown error:", err)
}
```

**🎯 Key Points**
- Drain in-flight requests
- Timeout for shutdown (prevent hang)
- Signal workers to stop

---

### 53. WebSocket Scaling

**❓ Câu hỏi:**
Làm thế nào để xử lý hàng nghìn kết nối WebSocket đồng thời?

**✅ Expected**
- Use `nhooyr.io/websocket` or `gorilla/websocket`
- One goroutine per connection (read + write)
- Bounded buffer for broadcasts
- Heartbeat/ping to detect dead connections

**💡 Architecture**
```go
type Hub struct {
    clients map[*Client]bool
    broadcast chan []byte
}

func (h *Hub) run() {
    for msg := range h.broadcast {
        for client := range h.clients {
            select {
            case client.send <- msg:
            default:
                close(client.send)
                delete(h.clients, client)
            }
        }
    }
}
```

**🎯 Scale**
- Limit goroutines (connection pool)
- Use pub/sub (Redis) for multi-instance broadcast

---

### 54. OS Signals

**❓ Câu hỏi:**
Go xử lý các tín hiệu hệ điều hành (OS Signals) như thế nào?

**✅ Expected**
```go
import (
    "os"
    "os/signal"
    "syscall"
)

sigs := make(chan os.Signal, 1)
signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

go func() {
    sig := <-sigs
    log.Println("Received signal:", sig)
    // Cleanup
    os.Exit(0)
}()
```

**🎯 Common Signals**
- SIGINT (Ctrl+C)
- SIGTERM (graceful shutdown)
- SIGHUP (reload config)

---

### 55. Distributed Tracing

**❓ Câu hỏi:**
Cách triển khai Distributed Tracing (OpenTelemetry) trong microservices?

**✅ Expected**
- Propagate `trace_id` + `span_id` via context
- HTTP: inject/extract headers (W3C Trace Context)
- gRPC: metadata propagation

**💡 Example**
```go
import "go.opentelemetry.io/otel"

tracer := otel.Tracer("my-service")
ctx, span := tracer.Start(ctx, "operation-name")
defer span.End()

// Propagate ctx to downstream calls
```

**🎯 Benefit**
- End-to-end request tracking
- Performance bottleneck identification

---

### 56. Retry & Circuit Breaker

**❓ Câu hỏi:**
Chiến lược retry và circuit breaker. Cách đảm bảo idempotency?

**✅ Expected**
- Retry: exponential backoff + jitter
- Circuit breaker: fail fast when downstream unhealthy
- Idempotency for safe retry

**💡 Exponential Backoff**
```go
backoff := time.Second
for i := 0; i < maxRetries; i++ {
    if err := call(); err == nil {
        return nil
    }
    time.Sleep(backoff + jitter())
    backoff *= 2
}
```

**🎯 Circuit Breaker States**
- Closed: normal operation
- Open: fail fast (downstream error)
- Half-open: test recovery

**❌ Red flags**
- Retry mọi thứ (non-idempotent operations)

**🔥 Senior+**
- Use `sony/gobreaker`
- Adaptive timeout

---

### 57. Connection Pooling

**❓ Câu hỏi:**
Xử lý **Database Connection Pool** đúng cách (MaxOpenConns, MaxIdleConns)?

**✅ Expected**
```go
db.SetMaxOpenConns(25)     // Max connections to DB
db.SetMaxIdleConns(25)     // Keep alive
db.SetConnMaxLifetime(5*time.Minute)  // Recycle connections
```

**🎯 Tuning**
- MaxOpenConns: DB capacity / # of app instances
- MaxIdleConns = MaxOpenConns (avoid reconnection)
- Monitor: in-use, idle, wait count

---

### 58. Database/SQL vs ORM

**❓ Câu hỏi:**
`database/sql` vs ORM như `GORM` – trade-offs?

**✅ Expected**

| database/sql | GORM |
|--------------|------|
| Explicit queries | Auto-generated |
| Performance | Convenience |
| Full control | Less control |

**🎯 Decision**
- Simple CRUD → GORM (fast development)
- Complex queries/optimization → `sqlx` or raw SQL
- High performance → prepared statements + raw SQL

**🔥 Senior+**
- Measure query performance
- N+1 problem awareness

---

### 59. Context for DB

**❓ Câu hỏi:**
Cách sử dụng `context` để cancel các query Database chạy quá lâu?

**✅ Expected**
```go
ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
defer cancel()

rows, err := db.QueryContext(ctx, "SELECT * FROM users")
// Query canceled if > 2s
```

**🎯 Production**
- Always set timeout for DB operations
- Context cancellation propagates to driver

---

### 60. gRPC vs REST

**❓ Câu hỏi:**
Ưu và nhược điểm của Protobuf/gRPC so với JSON/REST?

**✅ Expected**

| gRPC | REST |
|------|------|
| HTTP/2, binary (Protobuf) | HTTP/1.1, JSON |
| Type-safe contract | Flexible |
| Bidirectional streaming | Request/response |
| Internal microservices | Public APIs |

**🎯 When gRPC**
- High performance internal services
- Strong typing requirement
- Streaming support needed

**🎯 When REST**
- Public-facing API
- Browser compatibility
- Simplicity priority

---

### 61. Message Queue Idempotency

**❓ Câu hỏi:**
Làm sao đảm bảo **Idempotency** khi xử lý Message Queue (Kafka/RabbitMQ)?

**✅ Expected**
- Store `request_id` (or message offset) in DB/Redis
- Check before processing: "already processed?"
- Use transaction to ensure atomicity

**💡 Pattern**
```go
func processMessage(msg Message) error {
    tx := db.Begin()

    // Check idempotency
    var exists bool
    tx.Get(&exists, "SELECT EXISTS(SELECT 1 FROM processed WHERE id = ?)", msg.ID)
    if exists {
        return nil  // Already processed
    }

    // Process
    if err := doWork(msg); err != nil {
        tx.Rollback()
        return err
    }

    // Mark as processed
    tx.Exec("INSERT INTO processed (id) VALUES (?)", msg.ID)
    return tx.Commit()
}
```

**🎯 Critical For**
- Payment processing
- Inventory updates
- Any non-idempotent operation

---

### 62. Horizontal Scaling

**❓ Câu hỏi:**
Cách thiết kế Go service cho horizontal scaling?

**✅ Expected**
- Stateless services (no local state)
- Externalize session (Redis)
- Database connection pool sizing
- Load balancer configuration

**🎯 Checklist**
- No local file storage (use S3/blob)
- No in-memory cache (use Redis)
- Database can handle increased connections

---

### 63. Config Management

**❓ Câu hỏi:**
Cách quản lý configuration trong Go apps?

**✅ Expected**
- Environment variables (12-factor app)
- Config files (YAML/JSON) for complex settings
- Secrets management (Vault, k8s secrets)

**💡 Pattern**
```go
type Config struct {
    Port     int    `env:"PORT" default:"8080"`
    DBHost   string `env:"DB_HOST" required:"true"`
    LogLevel string `env:"LOG_LEVEL" default:"info"`
}

// Load from env
cfg := Config{}
env.Parse(&cfg)
```

---

### 64. Observability

**❓ Câu hỏi:**
Cách đảm bảo observability (logs, metrics, tracing)?

**✅ Expected**
- **Logs**: structured logging (JSON), contextual info
- **Metrics**: Prometheus (counters, gauges, histograms)
- **Tracing**: OpenTelemetry (distributed tracing)

**💡 Three Pillars**
```go
// Logging
log.Info().Str("user_id", id).Msg("User logged in")

// Metrics
requestCount.Inc()
requestDuration.Observe(duration)

// Tracing
ctx, span := tracer.Start(ctx, "db-query")
defer span.End()
```

**🎯 Production**
- Correlate logs/metrics/traces via trace_id
- SLI/SLO monitoring

---

### 65. API Versioning

**❓ Câu hỏi:**
Cách xử lý versioning và backward compatibility trong APIs?

**✅ Expected**
- URL versioning: `/v1/users`, `/v2/users`
- Header versioning: `Accept: application/vnd.api.v2+json`
- Backward compatibility in minor versions

**💡 Deprecation Strategy**
- Announce deprecation early
- Provide migration guide
- Support 2 versions in parallel

---

### 66. Testing

**❓ Câu hỏi:**
Viết Unit Test cho code có Database/External API interaction (Mock/Interface)?

**✅ Expected**
- Define interface for dependencies
- Mock implementation for testing
- Use `gomock` or manual mocks

**💡 Example**
```go
type UserRepo interface {
    GetUser(id int) (*User, error)
}

type MockRepo struct{}
func (m *MockRepo) GetUser(id int) (*User, error) {
    return &User{ID: id}, nil
}

func TestService(t *testing.T) {
    repo := &MockRepo{}
    svc := NewService(repo)
    // Test svc without real DB
}
```

---

### 67. Dependencies

**❓ Câu hỏi:**
Quản lý dependencies với `go mod` (vai trò của `go.sum` và `vendor`)?

**✅ Expected**
- `go.mod`: dependency versions
- `go.sum`: cryptographic hashes (security)
- `vendor/`: optional vendoring (offline builds)

**💡 Commands**
```bash
go mod init
go mod tidy      # Add missing, remove unused
go mod vendor    # Copy deps to vendor/
```

**🎯 Security**
- `go.sum` prevents tampering
- Review dependencies (license, vulnerabilities)

---

## 🎯 Bonus – "Killer Questions"

### "Design 1M requests/sec System"

**❓ Câu hỏi:**
Design a system to process **1M requests/sec** using Go. Bottlenecks?

**🔥 Senior+ Approach**
1. **Load balancer**: nginx/envoy (TLS termination)
2. **App layer**: stateless Go services (horizontal scale)
3. **Caching**: Redis (hot data)
4. **Database**: read replicas, connection pooling
5. **Bottlenecks**:
   - Network bandwidth
   - Database connections
   - Lock contention

**🎯 Optimization**
- Keep-alive connections
- Minimize allocations
- Async processing (queue for writes)

---

### "CPU 100% but low throughput"

**❓ Câu hỏi:**
Debug a production issue: **CPU 100% but low throughput**

**🔥 Senior+ Approach**
1. `pprof` CPU profile → identify hotspot
2. Flamegraph visualization
3. Check goroutine count (`runtime.NumGoroutine()`)
4. Fix root cause (not symptom)

**✅ Expected Root Causes**
- Lock contention (mutex blocking)
- GC pressure (thrashing)
- Inefficient algorithm in hot path
- Goroutine explosion

**❌ Red flags**
- "Server yếu, cần upgrade hardware"

---

### "Goroutine leak after deploy"

**❓ Câu hỏi:**
A service has **goroutine leak after deploy** – how do you trace it?

**🔥 Senior+ Approach**
1. `curl /debug/pprof/goroutine?debug=2` → stack traces
2. Identify blocked goroutines (channel, select, mutex)
3. Root cause: missing context cancel, no timeout
4. Fix: proper lifecycle management

**🎯 Prevention**
- Context-driven lifecycle
- Always set timeouts
- Monitor goroutine count in production

---

### "Design Rate Limiter"

**❓ Câu hỏi:**
Design a **rate limiter** in Go (token bucket vs leaky bucket)

**🔥 Senior+ Approach - Token Bucket**
```go
type TokenBucket struct {
    tokens    float64
    capacity  float64
    rate      float64  // tokens per second
    lastTime  time.Time
    mu        sync.Mutex
}

func (tb *TokenBucket) Allow() bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(tb.lastTime).Seconds()
    tb.tokens = min(tb.capacity, tb.tokens + elapsed*tb.rate)
    tb.lastTime = now

    if tb.tokens >= 1 {
        tb.tokens--
        return true
    }
    return false
}
```

**Trade-offs**
- Token bucket: allows bursts
- Leaky bucket: smooth rate
- Sliding window: accurate but complex

---

### "Optimize p99 latency"

**❓ Câu hỏi:**
Optimize a slow API (p99 latency problem)

**🔥 Senior+ Approach**
1. **Measure**: pprof, tracing, metrics
2. **Identify**:
   - Slow DB queries
   - GC pauses
   - Lock contention
   - Inefficient serialization
3. **Optimize**:
   - Add indexes
   - Cache hot data
   - Reduce allocations
   - Use connection pooling
4. **Validate**: measure p99 again

---

## 📊 Tổng kết cách chấm Senior

| Level | Dấu hiệu |
|-------|----------|
| ❌ Fake Senior | Nói khái niệm, không thực tế, không biết trade-offs |
| ⚠️ Mid | Biết dùng nhưng không hiểu sâu, không debug được |
| ✅ Senior | Hiểu mechanism, trade-offs, debug production issues |
| 🔥 Principal | Design systems, optimize, production mindset, mentor others |

### Senior thật phải:
- Giải thích được **WHY** (not just WHAT)
- Biết **trade-offs** của mỗi approach
- **Debug** production issues efficiently
- **Measure** before optimize
- **Design** cho scale & maintainability

### Kinh nghiệm cho người phỏng vấn:
Đối với một Senior, đừng chỉ nghe họ trả lời lý thuyết. Hãy yêu cầu họ:
- **Vẽ sơ đồ** (Scheduler, Memory model, System architecture)
- **Viết code** trên bảng trắng (Worker pool, Rate limiter)
- **Debug scenarios** (Memory leak, High CPU, Race conditions)
- **Design systems** (1M req/s, Distributed systems)
- **Explain trade-offs** (ORM vs SQL, Channel vs Mutex, gRPC vs REST)
