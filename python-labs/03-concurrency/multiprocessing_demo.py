#!/usr/bin/env python3
"""
多进程编程演示（简化版）

演示内容：
1. 基础进程创建与启动
2. 进程池（ProcessPoolExecutor）
3. CPU 密集型任务的并行化
"""

import multiprocessing
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed


# ========== 模块级别的 worker 函数（macOS spawn 方式需要可 pickle）==========

def basic_worker(name, duration):
    """基础工作进程"""
    pid = os.getpid()
    print(f"[进程 {name}, PID: {pid}] 开始执行 {duration} 秒")
    time.sleep(duration)
    print(f"[进程 {name}, PID: {pid}] 执行完成")
    return f"{name} done"


def square(x):
    """计算平方（用于进程池演示）"""
    time.sleep(0.1)
    return x * x


def cpu_task(n):
    """CPU 密集型任务：计算平方和"""
    total = 0
    for i in range(n):
        total += i * i
    return total


# ========== 演示函数 ==========

def demo_basic_process():
    """基础进程创建与启动"""
    print("=" * 60)
    print("1. 基础进程创建与启动")
    print("=" * 60)
    
    print("创建两个进程：")
    p1 = multiprocessing.Process(target=basic_worker, args=("P1", 2))
    p2 = multiprocessing.Process(target=basic_worker, args=("P2", 1))
    
    print(f"主进程 PID: {os.getpid()}")
    
    p1.start()
    p2.start()
    
    print("主进程继续执行...")
    
    p1.join()
    p2.join()
    print("所有进程完成\n")


def demo_process_pool():
    """进程池（ProcessPoolExecutor）"""
    print("=" * 60)
    print("2. 进程池（ProcessPoolExecutor）")
    print("=" * 60)
    
    print("使用 ProcessPoolExecutor 并发计算平方：")
    start = time.time()
    
    with ProcessPoolExecutor(max_workers=4) as executor:
        numbers = list(range(8))
        results = list(executor.map(square, numbers))
    
    elapsed = time.time() - start
    print(f"  输入: {numbers}")
    print(f"  输出: {results}")
    print(f"  耗时: {elapsed:.2f} 秒（串行需要 0.8 秒）\n")


def demo_submit_vs_map():
    """进程池：submit vs map"""
    print("=" * 60)
    print("3. 进程池：submit + as_completed vs map")
    print("=" * 60)
    
    print("executor.map：保持输入顺序，阻塞直到所有完成")
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(square, range(8)))
    print(f"  结果: {results}\n")
    
    print("executor.submit + as_completed：按完成顺序返回")
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(square, i) for i in range(8)]
        results = []
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"  任务完成: {result}")
    print()


def demo_cpu_intensive():
    """CPU 密集型任务的并行化"""
    print("=" * 60)
    print("4. CPU 密集型任务的并行化")
    print("=" * 60)
    
    task_size = 500_000  # 减少计算量以加快演示
    num_tasks = 4
    
    print(f"任务：计算 {num_tasks} 次 {task_size:,} 以内的平方和")
    
    # 单进程执行
    start = time.time()
    results_single = []
    for _ in range(num_tasks):
        results_single.append(cpu_task(task_size))
    single_time = time.time() - start
    print(f"  单进程: {single_time:.3f} 秒")
    
    # 多进程执行
    start = time.time()
    with ProcessPoolExecutor(max_workers=4) as executor:
        results_multi = list(executor.map(cpu_task, [task_size] * num_tasks))
    multi_time = time.time() - start
    print(f"  多进程: {multi_time:.3f} 秒")
    print(f"  加速比: {single_time / multi_time:.2f}x")
    print(f"  结果一致: {results_single == results_multi}\n")
    
    # 与多线程对比
    print("与多线程对比（CPU 密集型任务）：")
    import threading
    start = time.time()
    threads = []
    results_thread = []
    for _ in range(num_tasks):
        t = threading.Thread(target=lambda: results_thread.append(cpu_task(task_size)))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    thread_time = time.time() - start
    print(f"  多线程: {thread_time:.3f} 秒")
    print(f"  加速比: {single_time / thread_time:.2f}x")
    print(f"  → GIL 导致多线程无法并行，多进程真正并行\n")


if __name__ == "__main__":
    demo_basic_process()
    demo_process_pool()
    demo_submit_vs_map()
    demo_cpu_intensive()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 多进程绕过 GIL，适合 CPU 密集型任务")
    print("2. 使用进程池管理进程（ProcessPoolExecutor）")
    print("3. map 保持顺序，submit + as_completed 按完成顺序")
    print("4. 多进程开销大（创建、通信），适合计算密集型任务")
    print()
    print("选择指南：")
    print("  CPU 密集型（计算、图像处理）→ 多进程")
    print("  IO 密集型（网络、文件）→ 多线程或 asyncio")
