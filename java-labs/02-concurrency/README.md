# 模块 02：并发编程

> **核心问题**：多线程编程的正确性与性能平衡
> **学习目标**：掌握 Java 并发原语，能在生产环境设计高并发系统

## 三个核心示例

### 1. SynchronizedVsLock.java
**对比 synchronized 与 ReentrantLock**
- synchronized：JVM 层面，自动释放，不可中断
- ReentrantLock：API 层面，手动释放，可中断，支持公平锁

**面试题**：
- "synchronized 的锁升级过程？" → 无锁 → 偏向锁 → 轻量级锁 → 重量级锁
- "ReentrantLock 的公平锁和非公平锁区别？" → 公平锁按等待顺序，非公平锁允许插队

### 2. ThreadPoolTuning.java
**线程池核心参数调优**
- corePoolSize：核心线程数（即使空闲也保留）
- maximumPoolSize：最大线程数（队列满时创建）
- workQueue：任务队列（ArrayBlockingQueue、LinkedBlockingQueue）
- handler：拒绝策略（AbortPolicy、CallerRunsPolicy 等）

**面试题**：
- "如何设置线程池大小？" → CPU 密集型：N+1；IO 密集型：2N
- "线程池的 execute 流程？" → 核心线程 → 队列 → 最大线程 → 拒绝策略

### 3. DeadlockDetection.java
**死锁检测与避免**
- 死锁四条件：互斥、占有等待、不可剥夺、循环等待
- jstack 命令检测死锁
- 避免策略：锁排序、超时放弃、死锁检测

**面试题**：
- "如何手写一个死锁？" → 两个线程，两个锁，交叉获取
- "生产环境如何排查死锁？" → jstack <pid> | grep -i deadlock

## 运行方式

```bash
cd java-labs/02-concurrency/java
javac *.java
java SynchronizedVsLock
java ThreadPoolTuning
java DeadlockDetection
```

## 关键知识点

### 1. 锁的选择
| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单同步 | synchronized | JVM 优化好，代码简洁 |
| 需要中断 | ReentrantLock | 支持 lockInterruptibly() |
| 需要公平 | ReentrantLock(true) | 避免线程饥饿 |
| 读写分离 | ReadWriteLock | 读多写少场景性能更好 |

### 2. 线程池参数设置
```java
// CPU 密集型任务
int corePoolSize = Runtime.getRuntime().availableProcessors() + 1;

// IO 密集型任务
int corePoolSize = Runtime.getRuntime().availableProcessors() * 2;

// 混合类型（可配置化）
double cpuTime = 0.3;  // CPU 计算时间占比
double ioTime = 0.7;   // IO 等待时间占比
int corePoolSize = (int) (N * (1 + ioTime / cpuTime));
```

### 3. 并发工具类
- **CountDownLatch**：等待多个线程完成（主线程等待）
- **CyclicBarrier**：多个线程互相等待（所有线程到达后一起继续）
- **Semaphore**：控制并发访问的线程数（限流）
- **CompletableFuture**：异步编程，链式调用

## 面试题精选

**Q1：线程池的工作流程？**
```
1. 当前线程数 < corePoolSize → 创建核心线程
2. 当前线程数 >= corePoolSize → 任务放入队列
3. 队列满且线程数 < maximumPoolSize → 创建非核心线程
4. 队列满且线程数 = maximumPoolSize → 执行拒绝策略
```

**Q2：volatile 关键字的作用？**
- 可见性：一个线程修改后，其他线程立即可见
- 禁止指令重排：防止编译器/CPU 优化导致顺序错乱
- 不保证原子性：i++ 仍需 synchronized 或 AtomicInteger

**Q3：ThreadLocal 的原理与内存泄漏？**
- 原理：每个线程有自己的 ThreadLocalMap（Thread.threadLocals）
- 内存泄漏：ThreadLocal 被 GC，但 Entry 的 value 还在（弱引用 key，强引用 value）
- 解决：每次使用后 remove()

## 扩展阅读

- 《Java 并发编程实战》（Brian Goetz）
- JDK 源码：AbstractQueuedSynchronizer（AQS）
- 美团技术博客：线程池的监控与动态调参
