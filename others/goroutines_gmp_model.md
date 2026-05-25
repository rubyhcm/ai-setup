# How Goroutines Work in Go: Understanding the G-M-P Model

## 1. What is a Goroutine?
- A goroutine is a lightweight thread managed by the Go runtime.
- Unlike traditional OS threads, goroutines are much more lightweight and have smaller memory footprints. You can create thousands (or even millions) of goroutines within a single program because they are efficiently scheduled and managed by the Go runtime.

## 2. How to Create a Goroutine
You can launch a new goroutine using the `go` keyword followed by a function call.

Example:
```go
package main

import (
    "fmt"
    "time"
)

func sayHello() {
    fmt.Println("Hello goroutine!")
}

func main() {
    go sayHello()
    fmt.Println("Hello main!")
    time.Sleep(time.Second)
}
```

Output:
```
Hello main!
Hello goroutine!
```

- Here, `sayHello()` runs concurrently with the `main` function because it was started as a goroutine.
- The `main` function will not wait for the goroutine to complete unless explicitly instructed.

## 3. Goroutine Scheduler
- Go has its own scheduler, which is part of the Go runtime. The scheduler multiplexes many goroutines onto a smaller number of OS threads. 
- The Go scheduler uses a work-stealing algorithm to distribute goroutines across available OS threads efficiently.

## 4. Goroutine Execution Model
Goroutines work as part of the G-M-P model:
- **G:** Goroutine — the individual lightweight thread of execution.
- **M:** Machine — represents an OS thread.
- **P:** Processor — an abstraction of CPU resources needed to execute goroutines.

Here’s how they interact:
- Goroutines (G) are scheduled to run on processors (P).
- A processor (P) binds to an OS thread (M) to execute goroutines.
- The Go runtime dynamically manages multiple goroutines across a pool of OS threads.
- If a goroutine gets blocked (e.g., waiting for I/O), the scheduler parks it and schedules another runnable goroutine on the processor.

## 5. Goroutine Stack
- Goroutines start with a small stack (usually 2 KB) compared to OS threads (commonly 1 MB).
- **Dynamic Stack Growth:** The stack of a goroutine is dynamically resized as needed. When the stack space is insufficient, Go allocates a new, larger memory block, copies the existing stack data over to the new block, and frees the old one. This efficient memory allocation allows millions of goroutines to coexist without the risk of stack overflow or memory waste.

## 6. Concurrency vs. Parallelism
- Goroutines enable concurrency, meaning multiple tasks can be in progress at the same time.
- True parallelism (running on multiple CPUs) happens when the Go runtime uses multiple OS threads across multiple CPU cores (enabled using `GOMAXPROCS`).

## 7. Synchronization Between Goroutines
To coordinate between goroutines, Go provides:

**a. Channels:** Used for safe communication and data exchange.
```go
ch := make(chan string)
go func() {
    ch <- "Hello from goroutine!"
}()
msg := <-ch
fmt.Println(msg)
```

**b. WaitGroup:** Waits for multiple goroutines to complete.
```go
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    fmt.Println("Work done!")
}()
wg.Wait()
```

**c. Mutex:** Ensures mutual exclusion when accessing shared resources.

## 8. Blocking and Preemption
- Goroutines yield control back to the scheduler when: 	
  a. They are blocked (e.g., on I/O or channel operations).
  b. The Go scheduler decides to preempt them (preemption happens in newer Go versions).
- This cooperative behavior ensures that goroutines share CPU resources efficiently.

**Why Are Goroutines Efficient?**
a. Small memory footprint: 2 KB initial stack.
b. Dynamic stack growth: Only use as much memory as needed.
c. Multiplexing: Many goroutines run on a few OS threads.
d. Managed scheduling: Go runtime handles goroutine scheduling.

## 9. Additional Advantages of Goroutines
- **Cheaper and Flexible Stack:** Goroutines are much cheaper compared to OS threads. They start with a very small stack (usually 2KB) that can dynamically grow or shrink depending on the application's needs, whereas OS thread stacks are typically fixed in size.
- **Faster Startup Time:** Starting a new Goroutine is significantly faster than creating a new OS thread.
- **Safe Communication:** Inter-goroutine communication using Channels is extremely safe, avoiding many common concurrency pitfalls like race conditions.
- **M:N Multiplexing (Not 1:1):** Goroutines and OS threads do not have a 1:1 relationship. **Correction:** A single Goroutine *does not* run simultaneously on multiple OS threads. Instead, thousands of Goroutines are multiplexed onto a smaller set of OS threads (M:N model). A Goroutine runs on exactly one OS thread at any single point in time, though it may yield control and resume on a different thread later.

## 10. Deep Dive into the G-M-P Model (Mechanics & Analogies)
To better understand how G, M, and P work together, consider this mental model:
- **G (Goroutine) = The Work:** The task that needs to be done. It is not a unit of execution itself but a unit of work. It is extremely lightweight, has a small stack that can grow or shrink, and is not permanently bound to any specific thread.
- **M (Machine / OS Thread) = The Worker:** The actual OS thread managed by the Operating System. It runs on the CPU. A single M can only execute one G at a time.
- **P (Processor) = The Work Permit (Context):** Represents the right or capability to run Go code. It holds a local run queue of Goroutines. For an M to execute Go code, it **must** acquire a P.

### How they interact:
- **M + P -> Runs Go Code:** An available worker (M) gets a permit (P) to start executing the tasks (G) from P's local queue.
- A single P can have many Gs queued up.
- A single M executes exactly one G at any particular time.

### GOMAXPROCS and Parallelism:
- `GOMAXPROCS` defines the number of **P**s (Permits), which defaults to the number of CPU cores.
- It determines the maximum **parallelism** (how many Goroutines can truly run at the exact same time).
- *Misconceptions:* `GOMAXPROCS` does NOT dictate the number of Goroutines or OS threads. M does not always equal the number of cores. Increasing `GOMAXPROCS` means increasing the number of Goroutines that can run in parallel.

### Finding Work (Local Queue, Global Queue, and Stealing):
- Each P has its own **Local Run Queue** of Goroutines. When a new G is created, it is primarily added here. If the local queue becomes full, excess Gs are pushed to the **Global Run Queue**.
- When an M (running on a P) finishes executing all Goroutines in its local queue and becomes idle, it attempts to find work in the following order:
  1. It tries to **"steal"** Goroutines from the local queue of another P (Work Stealing).
  2. If unsuccessful, it checks the **Global Run Queue**.
  3. If still empty, it checks the **Network Poller** for any Goroutines that have finished waiting for I/O.
- This balances the load across CPU cores and strictly avoids idle CPUs.

### Handling Blocking Syscalls vs Network I/O:
Depending on the type of blocking operation, Go handles it differently to maintain high concurrency:
- **Blocking Syscalls (e.g., File I/O, CGO):**
  1. It detaches the blocked M (along with its blocking G) from the P.
  2. It assigns the P to a different, newly awakened or created M.
  3. The new M continues executing the other Goroutines in the P's queue.
- **Network I/O (Network Poller):**
  For network operations (like `http.Get` or socket reads), Go does **not** block the OS thread. Instead, the Goroutine is put to sleep and the I/O event is registered with the **Network Poller** (using epoll, kqueue, or IOCP). The M is immediately freed to execute other Goroutines. Once the network I/O completes, the Network Poller wakes up the Goroutine and places it back into the run queue.
- This decoupling ensures that a blocking operation does not block the other Goroutines waiting in the queue, making Go extremely resilient compared to other runtimes.

## Summary
- Goroutines are lightweight, managed threads used for concurrency.
- The Go scheduler maps goroutines onto OS threads dynamically.
- Go’s runtime makes goroutines memory- and CPU-efficient, allowing programs to scale to thousands of concurrent tasks.

## References
- https://www.linkedin.com/pulse/go-runtime-architecture-%C4%91i%E1%BB%81u-l%C3%A0m-n%C3%AAn-s%E1%BB%A9c-m%E1%BA%A1nh-th%E1%BA%ADt-s%E1%BB%B1-thanh-vo-hqw8c/
