#!/usr/bin/env python3
"""
多线程编程演示

演示内容：
1. 基础线程创建与启动
2. 线程同步（Lock, RLock, Condition）
3. 线程池（ThreadPoolExecutor）
4. 生产者-消费者模式
5. GIL 的影响演示
"""

import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed


def demo_basic_thread():
    """基础线程创建与启动"""
    print("=" * 60)
    print("1. 基础线程创建与启动")
    print("=" * 60)
    
    # 方式 1：使用函数
    def worker(name, duration):
        print(f"[{threading.current_thread().name}] 线程 {name} 开始")
        time.sleep(duration)
        print(f"[{threading.current_thread().name}] 线程 {name} 结束")
    
    print("创建两个线程：")
    t1 = threading.Thread(target=worker, args=("A", 2), name="Thread-1")
    t2 = threading.Thread(target=worker, args=("B", 1), name="Thread-2")
    
    t1.start()
    t2.start()
    
    print("主线程继续执行...")
    
    t1.join()  # 等待 t1 完成
    t2.join()  # 等待 t2 完成
    print("所有线程完成\n")
    
    # 方式 2：继承 Thread 类
    class MyThread(threading.Thread):
        def __init__(self, name, duration):
            super().__init__(name=name)
            self.duration = duration
        
        def run(self):
            print(f"[{self.name}] 开始执行 {self.duration} 秒")
            time.sleep(self.duration)
            print(f"[{self.name}] 执行完成")
    
    print("使用 Thread 子类：")
    t3 = MyThread("CustomThread", 1)
    t3.start()
    t3.join()
    print()


def demo_lock():
    """线程锁（Lock）"""
    print("=" * 60)
    print("2. 线程锁（Lock）")
    print("=" * 60)
    
    # 没有锁的情况：竞态条件
    counter_without_lock = 0
    
    def increment_without_lock():
        nonlocal counter_without_lock
        for _ in range(100000):
            counter_without_lock += 1  # 非原子操作
    
    threads = []
    for _ in range(10):
        t = threading.Thread(target=increment_without_lock)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"无锁情况：10 个线程各增 100000 次")
    print(f"预期结果: 1000000")
    print(f"实际结果: {counter_without_lock}（竞态条件导致丢失）\n")
    
    # 使用锁保护
    counter_with_lock = 0
    lock = threading.Lock()
    
    def increment_with_lock():
        nonlocal counter_with_lock
        for _ in range(100000):
            with lock:  # 自动获取和释放锁
                counter_with_lock += 1
    
    threads = []
    for _ in range(10):
        t = threading.Thread(target=increment_with_lock)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"有锁情况：10 个线程各增 100000 次")
    print(f"预期结果: 1000000")
    print(f"实际结果: {counter_with_lock}（锁保证正确性）\n")


def demo_rlock():
    """可重入锁（RLock）"""
    print("=" * 60)
    print("3. 可重入锁（RLock）")
    print("=" * 60)
    
    print("普通 Lock 不能在同一线程中多次获取（会死锁）：")
    lock = threading.Lock()
    lock.acquire()
    print("  第一次获取锁: 成功")
    # lock.acquire()  # 这会导致死锁！
    lock.release()
    print("  释放锁\n")
    
    print("RLock 允许同一线程多次获取：")
    rlock = threading.RLock()
    
    def recursive_function(n):
        with rlock:
            print(f"  递归层级 {n}")
            if n > 0:
                recursive_function(n - 1)
    
    recursive_function(3)
    print("  ✓ RLock 支持递归调用\n")


def demo_condition():
    """条件变量（Condition）"""
    print("=" * 60)
    print("4. 条件变量（Condition）")
    print("=" * 60)
    
    condition = threading.Condition()
    data_ready = False
    shared_data = []
    
    def producer():
        nonlocal data_ready
        print("[生产者] 准备数据...")
        time.sleep(1)
        
        with condition:
            shared_data.extend([1, 2, 3])
            data_ready = True
            print("[生产者] 数据准备完成，通知消费者")
            condition.notify()
    
    def consumer():
        nonlocal data_ready
        print("[消费者] 等待数据...")
        
        with condition:
            condition.wait()  # 等待通知
            print(f"[消费者] 收到数据: {shared_data}")
    
    t1 = threading.Thread(target=consumer)
    t2 = threading.Thread(target=producer)
    
    t1.start()
    time.sleep(0.1)  # 确保消费者先等待
    t2.start()
    
    t1.join()
    t2.join()
    print()


def demo_thread_pool():
    """线程池（ThreadPoolExecutor）"""
    print("=" * 60)
    print("5. 线程池（ThreadPoolExecutor）")
    print("=" * 60)
    
    def task(n):
        time.sleep(0.5)
        return n * n
    
    print("使用 ThreadPoolExecutor 并发执行任务：")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 方式 1：submit + as_completed
        futures = [executor.submit(task, i) for i in range(8)]
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    
    elapsed = time.time() - start
    print(f"  8 个任务，4 个工作线程")
    print(f"  结果: {sorted(results)}")
    print(f"  耗时: {elapsed:.2f} 秒（串行需要 4 秒）\n")
    
    # 方式 2：map
    print("使用 executor.map（保持顺序）：")
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(task, range(8)))
    print(f"  结果: {results}\n")


def demo_producer_consumer():
    """生产者-消费者模式"""
    print("=" * 60)
    print("6. 生产者-消费者模式")
    print("=" * 60)
    
    import queue
    
    q = queue.Queue(maxsize=5)
    
    def producer(name, count):
        for i in range(count):
            item = f"{name}-{i}"
            q.put(item)
            print(f"[生产者 {name}] 生产: {item}")
            time.sleep(random.uniform(0.1, 0.3))
    
    def consumer(name, count):
        for _ in range(count):
            item = q.get()
            print(f"[消费者 {name}] 消费: {item}")
            time.sleep(random.uniform(0.2, 0.5))
            q.task_done()
    
    # 启动生产者和消费者
    producers = [
        threading.Thread(target=producer, args=("P1", 3)),
        threading.Thread(target=producer, args=("P2", 3))
    ]
    consumers = [
        threading.Thread(target=consumer, args=("C1", 3)),
        threading.Thread(target=consumer, args=("C2", 3))
    ]
    
    for p in producers:
        p.start()
    for c in consumers:
        c.start()
    
    for p in producers:
        p.join()
    for c in consumers:
        c.join()
    
    q.join()  # 等待队列清空
    print("所有任务完成\n")


def demo_gil_impact():
    """GIL 的影响演示"""
    print("=" * 60)
    print("7. GIL 的影响演示")
    print("=" * 60)
    
    # CPU 密集型任务
    def cpu_intensive(n):
        total = 0
        for i in range(n):
            total += i * i
        return total
    
    # 单线程
    start = time.time()
    for _ in range(4):
        cpu_intensive(1000000)
    single_time = time.time() - start
    print(f"CPU 密集型任务（计算 100 万次平方和）")
    print(f"  单线程 x4: {single_time:.3f} 秒")
    
    # 多线程
    start = time.time()
    threads = []
    for _ in range(4):
        t = threading.Thread(target=cpu_intensive, args=(1000000,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    multi_time = time.time() - start
    print(f"  多线程 x4: {multi_time:.3f} 秒")
    print(f"  加速比: {single_time / multi_time:.2f}x")
    print(f"  → GIL 导致多线程无法并行，甚至更慢（线程切换开销）\n")
    
    # IO 密集型任务
    def io_intensive():
        time.sleep(0.5)  # 模拟 IO 等待
    
    # 单线程
    start = time.time()
    for _ in range(4):
        io_intensive()
    single_io_time = time.time() - start
    print(f"IO 密集型任务（等待 0.5 秒）")
    print(f"  单线程 x4: {single_io_time:.3f} 秒")
    
    # 多线程
    start = time.time()
    threads = []
    for _ in range(4):
        t = threading.Thread(target=io_intensive)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    multi_io_time = time.time() - start
    print(f"  多线程 x4: {multi_io_time:.3f} 秒")
    print(f"  加速比: {single_io_time / multi_io_time:.2f}x")
    print(f"  → IO 等待时释放 GIL，多线程真正并发\n")


if __name__ == "__main__":
    demo_basic_thread()
    demo_lock()
    demo_rlock()
    demo_condition()
    demo_thread_pool()
    demo_producer_consumer()
    demo_gil_impact()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 线程适合 IO 密集型任务（网络、文件）")
    print("2. 共享数据必须加锁（Lock/RLock）")
    print("3. 使用线程池管理线程（ThreadPoolExecutor）")
    print("4. 生产者-消费者模式解耦任务生成和处理")
    print("5. GIL 限制 CPU 密集型任务的多线程并行")
    print("6. CPU 密集型任务应使用多进程（见 multiprocessing_demo）")
