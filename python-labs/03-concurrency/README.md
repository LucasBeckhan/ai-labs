# 模块 03：并发编程

> **目标**：掌握 Python 并发编程的三种模型，理解适用场景和性能特点

## 核心概念

### 1. 并发 vs 并行

- **并发（Concurrency）**：多个任务交替执行（单核也能实现）
- **并行（Parallelism）**：多个任务同时执行（需要多核）

Python 的三种并发模型：
1. **多线程（threading）**：并发，受 GIL 限制
2. **多进程（multiprocessing）**：并行，绕过 GIL
3. **异步编程（asyncio）**：并发，适合 IO 密集型

### 2. GIL（全局解释器锁）

**什么是 GIL？**
- CPython 的全局锁，同一时刻只有一个线程执行 Python 字节码
- 保证内存安全，但限制了多线程的并行能力

**GIL 的影响**：
```
CPU 密集型（计算）：
  - 多线程：无法并行，甚至更慢（线程切换开销）
  - 多进程：真正并行，充分利用多核 ✓

IO 密集型（网络/文件）：
  - 多线程：等待 IO 时释放 GIL，可以并发 ✓
  - 异步：更轻量，单线程处理大量连接 ✓
```

### 3. 线程（threading）

```python
import threading

def worker(name):
    print(f"Thread {name} 开始")
    time.sleep(2)
    print(f"Thread {name} 结束")

# 创建线程
t1 = threading.Thread(target=worker, args=("A",))
t2 = threading.Thread(target=worker, args=("B",))

# 启动线程
t1.start()
t2.start()

# 等待完成
t1.join()
t2.join()
```

**线程同步**：
- `Lock`：互斥锁
- `RLock`：可重入锁
- `Condition`：条件变量
- `Semaphore`：信号量
- `Event`：事件标志

### 4. 进程（multiprocessing）

```python
from multiprocessing import Process

def worker(name):
    print(f"Process {name} 开始")
    time.sleep(2)
    print(f"Process {name} 结束")

# 创建进程
p1 = Process(target=worker, args=("A",))
p2 = Process(target=worker, args=("B",))

# 启动进程
p1.start()
p2.start()

# 等待完成
p1.join()
p2.join()
```

**进程间通信**：
- `Queue`：队列
- `Pipe`：管道
- `Value`/`Array`：共享内存
- `Manager`：共享对象

### 5. 异步编程（asyncio）

```python
import asyncio

async def worker(name):
    print(f"Task {name} 开始")
    await asyncio.sleep(2)  # 非阻塞等待
    print(f"Task {name} 结束")

# 创建任务
async def main():
    task1 = asyncio.create_task(worker("A"))
    task2 = asyncio.create_task(worker("B"))
    
    # 并发执行
    await asyncio.gather(task1, task2)

asyncio.run(main())
```

**核心概念**：
- `async/await`：协程语法
- `asyncio.run()`：运行协程
- `asyncio.gather()`：并发执行多个协程
- `asyncio.create_task()`：创建任务

## 面试题

### Q1: Python 多线程为什么不能利用多核？

**答案**：
- GIL（全局解释器锁）限制：同一时刻只有一个线程执行 Python 字节码
- 多线程只能实现并发（交替执行），不能实现并行（同时执行）
- IO 操作时释放 GIL，所以 IO 密集型任务多线程有效
- CPU 密集型任务应该用多进程

### Q2: 线程池和进程池怎么用？

**答案**：
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# 线程池
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(func, data)

# 进程池
with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(func, data)
```

### Q3: asyncio 和多线程的区别？

**答案**：
```
多线程：
  - 操作系统调度线程
  - 线程切换开销大（上下文切换）
  - 适合少量并发任务

asyncio：
  - 用户态协程调度
  - 协程切换开销小（只保存状态）
  - 适合大量 IO 并发（如 Web 服务器）
```

### Q4: 如何避免死锁？

**答案**：
1. **固定顺序**：所有线程按相同顺序获取锁
2. **超时机制**：`lock.acquire(timeout=5)`
3. **避免嵌套**：不要在一个锁内获取另一个锁
4. **使用上下文管理器**：`with lock:` 自动释放

### Q5: 什么时候用多线程、多进程、异步？

**答案**：
```
CPU 密集型（计算、图像处理）：
  → 多进程（绕过 GIL，真正并行）

IO 密集型（网络请求、文件读写）：
  → 多线程（简单）或 asyncio（高性能）

大量并发连接（Web 服务器、爬虫）：
  → asyncio（单线程处理万级连接）
```

## 示例文件

### 1. threading_demo.py
- 基础线程创建与同步
- Lock/RLock/Condition 使用
- 线程池（ThreadPoolExecutor）
- 生产者-消费者模式

### 2. multiprocessing_demo.py
- 基础进程创建
- 进程间通信（Queue/Pipe）
- 进程池（ProcessPoolExecutor）
- CPU 密集型任务并行化

### 3. asyncio_demo.py
- 协程基础（async/await）
- 并发执行（gather）
- 异步 IO（aiohttp 示例）
- 异步与同步混合

## 运行示例

```bash
cd 03-concurrency
python3 threading_demo.py
python3 multiprocessing_demo.py
python3 asyncio_demo.py
```

## 性能对比

| 场景 | 多线程 | 多进程 | asyncio |
|------|--------|--------|---------|
| CPU 密集（计算 100 万次） | 慢（GIL） | **快（并行）** | 慢 |
| IO 密集（100 次网络请求） | 快 | 快 | **最快** |
| 内存占用 | 中 | 高 | **低** |
| 编程复杂度 | 中 | 高 | 中高 |

## 最佳实践

1. **IO 密集型优先用 asyncio**：性能更好，资源占用更少
2. **CPU 密集型用多进程**：`ProcessPoolExecutor`
3. **线程安全**：共享数据必须加锁
4. **避免死锁**：固定锁顺序，使用超时
5. **使用上下文管理器**：`with lock:` 自动释放
6. **限制并发数**：使用信号量或线程池/进程池

## 学习路线

```
1. 理解 GIL 的影响
2. 掌握多线程基础（threading）
3. 学习多进程（multiprocessing）
4. 掌握异步编程（asyncio）
5. 根据场景选择合适的模型
```

## 扩展阅读

- [Python 官方文档 - threading](https://docs.python.org/3/library/threading.html)
- [Python 官方文档 - multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
- [Python 官方文档 - asyncio](https://docs.python.org/3/library/asyncio.html)
- [Real Python - Async IO](https://realpython.com/async-io-python/)
