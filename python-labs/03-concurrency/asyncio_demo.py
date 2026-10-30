#!/usr/bin/env python3
"""
异步编程演示（asyncio）

演示内容：
1. 协程基础（async/await）
2. 并发执行多个协程
3. 异步 IO 操作
4. asyncio.gather vs asyncio.wait
5. 异步队列和信号量
6. 异步与同步混合
"""

import asyncio
import time
import random


def demo_basic_coroutine():
    """协程基础"""
    print("=" * 60)
    print("1. 协程基础（async/await）")
    print("=" * 60)
    
    async def hello():
        print("Hello")
        await asyncio.sleep(1)  # 非阻塞等待
        print("World")
        return "Done"
    
    # 运行协程
    result = asyncio.run(hello())
    print(f"返回值: {result}\n")
    
    # 协程对象 vs 协程执行
    print("协程对象 vs 协程执行：")
    coro = hello()  # 创建协程对象，不会执行
    print(f"  coro = {coro}（协程对象，未执行）")
    
    result = asyncio.run(coro)  # 执行协程
    print(f"  result = {result}\n")


def demo_concurrent_execution():
    """并发执行多个协程"""
    print("=" * 60)
    print("2. 并发执行多个协程")
    print("=" * 60)
    
    async def task(name, duration):
        print(f"[{name}] 开始，耗时 {duration} 秒")
        await asyncio.sleep(duration)
        print(f"[{name}] 完成")
        return f"{name} done"
    
    # 串行执行（错误方式）
    print("串行执行（逐个 await）：")
    async def serial():
        start = time.time()
        r1 = await task("Task-1", 2)
        r2 = await task("Task-2", 1)
        r3 = await task("Task-3", 1)
        elapsed = time.time() - start
        print(f"  总耗时: {elapsed:.2f} 秒（串行：2+1+1=4 秒）\n")
    
    asyncio.run(serial())
    
    # 并发执行（正确方式）
    print("并发执行（asyncio.gather）：")
    async def concurrent():
        start = time.time()
        results = await asyncio.gather(
            task("Task-1", 2),
            task("Task-2", 1),
            task("Task-3", 1)
        )
        elapsed = time.time() - start
        print(f"  结果: {results}")
        print(f"  总耗时: {elapsed:.2f} 秒（并发：max(2,1,1)=2 秒）\n")
    
    asyncio.run(concurrent())


def demo_async_io():
    """异步 IO 操作"""
    print("=" * 60)
    print("3. 异步 IO 操作")
    print("=" * 60)
    
    # 模拟异步 HTTP 请求
    async def fetch_data(url, delay):
        print(f"[请求] {url} 开始")
        await asyncio.sleep(delay)  # 模拟网络延迟
        data = f"数据来自 {url}"
        print(f"[请求] {url} 完成")
        return data
    
    async def main():
        urls = [
            ("https://api.example.com/1", 2),
            ("https://api.example.com/2", 1),
            ("https://api.example.com/3", 1.5)
        ]
        
        print("并发请求 3 个 URL：")
        start = time.time()
        
        tasks = [fetch_data(url, delay) for url, delay in urls]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        print(f"\n所有请求完成，耗时: {elapsed:.2f} 秒")
        print(f"结果: {results}\n")
    
    asyncio.run(main())


def demo_gather_vs_wait():
    """asyncio.gather vs asyncio.wait"""
    print("=" * 60)
    print("4. asyncio.gather vs asyncio.wait")
    print("=" * 60)
    
    async def task(name, duration, fail=False):
        print(f"[{name}] 开始")
        await asyncio.sleep(duration)
        if fail:
            raise ValueError(f"{name} 失败")
        print(f"[{name}] 完成")
        return f"{name} done"
    
    # asyncio.gather
    print("【asyncio.gather】")
    print("  - 所有任务完成才返回")
    print("  - 任一任务失败则抛出异常")
    print("  - 返回结果列表（保持顺序）")
    
    async def gather_demo():
        try:
            results = await asyncio.gather(
                task("T1", 1),
                task("T2", 2),
                task("T3", 1.5)
            )
            print(f"  结果: {results}\n")
        except Exception as e:
            print(f"  异常: {e}\n")
    
    asyncio.run(gather_demo())
    
    # asyncio.wait
    print("【asyncio.wait】")
    print("  - 更灵活的控制")
    print("  - 可以设置完成条件（ALL_COMPLETED, FIRST_COMPLETED）")
    print("  - 返回 (done, pending) 两个集合")
    
    async def wait_demo():
        tasks = [
            asyncio.create_task(task("T1", 1)),
            asyncio.create_task(task("T2", 2)),
            asyncio.create_task(task("T3", 1.5))
        ]
        
        # 等待所有完成
        done, pending = await asyncio.wait(tasks)
        print(f"  完成: {len(done)} 个")
        print(f"  待处理: {len(pending)} 个")
        
        results = [t.result() for t in done]
        print(f"  结果: {results}\n")
    
    asyncio.run(wait_demo())
    
    # FIRST_COMPLETED
    print("【FIRST_COMPLETED】")
    print("  任意一个任务完成就返回")
    
    async def first_completed_demo():
        tasks = [
            asyncio.create_task(task("T1", 2)),
            asyncio.create_task(task("T2", 1)),
            asyncio.create_task(task("T3", 3))
        ]
        
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        print(f"  首先完成: {[t.result() for t in done]}")
        print(f"  仍在运行: {len(pending)} 个")
        
        # 取消未完成的任务
        for pending_task in pending:
            pending_task.cancel()
        print()
    
    asyncio.run(first_completed_demo())


def demo_async_queue():
    """异步队列"""
    print("=" * 60)
    print("5. 异步队列（asyncio.Queue）")
    print("=" * 60)
    
    async def producer(queue, name, count):
        for i in range(count):
            item = f"{name}-{i}"
            await queue.put(item)
            print(f"[生产者 {name}] 放入: {item}")
            await asyncio.sleep(random.uniform(0.1, 0.3))
        print(f"[生产者 {name}] 完成")
    
    async def consumer(queue, name):
        while True:
            item = await queue.get()
            print(f"[消费者 {name}] 取出: {item}")
            await asyncio.sleep(random.uniform(0.2, 0.5))
            queue.task_done()
    
    async def main():
        queue = asyncio.Queue(maxsize=5)
        
        # 启动生产者和消费者
        producers = [
            asyncio.create_task(producer(queue, "P1", 3)),
            asyncio.create_task(producer(queue, "P2", 3))
        ]
        consumers = [
            asyncio.create_task(consumer(queue, "C1")),
            asyncio.create_task(consumer(queue, "C2"))
        ]
        
        # 等待生产者完成
        await asyncio.gather(*producers)
        
        # 等待队列处理完成
        await queue.join()
        
        # 取消消费者
        for c in consumers:
            c.cancel()
        
        print("所有任务完成\n")
    
    asyncio.run(main())


def demo_semaphore():
    """异步信号量（限制并发数）"""
    print("=" * 60)
    print("6. 异步信号量（Semaphore）")
    print("=" * 60)
    
    async def task(sem, name, duration):
        async with sem:  # 获取信号量
            print(f"[{name}] 开始（获取信号量）")
            await asyncio.sleep(duration)
            print(f"[{name}] 完成（释放信号量）")
    
    async def main():
        # 限制同时最多 3 个任务运行
        sem = asyncio.Semaphore(3)
        
        print("信号量限制：最多 3 个并发")
        print("提交 6 个任务：\n")
        
        start = time.time()
        tasks = [
            task(sem, f"Task-{i}", random.uniform(1, 2))
            for i in range(6)
        ]
        
        await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"\n总耗时: {elapsed:.2f} 秒\n")
    
    asyncio.run(main())


def demo_async_sync_mix():
    """异步与同步混合"""
    print("=" * 60)
    print("7. 异步与同步混合")
    print("=" * 60)
    
    # 在异步代码中调用同步代码
    def sync_function():
        print("[同步] 开始耗时操作")
        time.sleep(1)  # 阻塞操作
        print("[同步] 完成")
        return "同步结果"
    
    async def async_wrapper():
        print("[异步] 调用同步函数")
        # 使用 run_in_executor 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_function)
        print(f"[异步] 得到结果: {result}")
        return result
    
    asyncio.run(async_wrapper())
    print()
    
    # 在同步代码中调用异步代码
    async def async_function():
        print("[异步函数] 执行中")
        await asyncio.sleep(1)
        return "异步结果"
    
    def sync_caller():
        print("[同步] 调用异步函数")
        result = asyncio.run(async_function())
        print(f"[同步] 得到结果: {result}")
    
    sync_caller()
    print()


def demo_async_context_manager():
    """异步上下文管理器"""
    print("=" * 60)
    print("8. 异步上下文管理器")
    print("=" * 60)
    
    class AsyncResource:
        async def __aenter__(self):
            print("[资源] 异步获取资源")
            await asyncio.sleep(0.5)
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            print("[资源] 异步释放资源")
            await asyncio.sleep(0.5)
            return False
    
    async def use_resource():
        async with AsyncResource() as resource:
            print("[使用] 正在使用资源")
            await asyncio.sleep(1)
            print("[使用] 完成")
    
    asyncio.run(use_resource())
    print()


def demo_performance_comparison():
    """性能对比：同步 vs 异步"""
    print("=" * 60)
    print("9. 性能对比：同步 vs 异步")
    print("=" * 60)
    
    # 模拟 IO 密集型任务
    def sync_task():
        time.sleep(0.1)  # 模拟 IO 等待
    
    async def async_task():
        await asyncio.sleep(0.1)  # 异步 IO 等待
    
    num_tasks = 100
    
    # 同步执行
    start = time.time()
    for _ in range(num_tasks):
        sync_task()
    sync_time = time.time() - start
    print(f"同步执行 {num_tasks} 个 IO 任务: {sync_time:.3f} 秒")
    
    # 异步执行
    async def run_async():
        await asyncio.gather(*[async_task() for _ in range(num_tasks)])
    
    start = time.time()
    asyncio.run(run_async())
    async_time = time.time() - start
    print(f"异步执行 {num_tasks} 个 IO 任务: {async_time:.3f} 秒")
    
    print(f"加速比: {sync_time / async_time:.1f}x")
    print(f"→ 异步适合大量 IO 并发场景\n")


if __name__ == "__main__":
    demo_basic_coroutine()
    demo_concurrent_execution()
    demo_async_io()
    demo_gather_vs_wait()
    demo_async_queue()
    demo_semaphore()
    demo_async_sync_mix()
    demo_async_context_manager()
    demo_performance_comparison()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. async/await 是异步编程的基础")
    print("2. asyncio.gather 并发执行多个协程")
    print("3. 异步适合 IO 密集型任务（网络、文件）")
    print("4. 使用 Queue 和 Semaphore 控制并发")
    print("5. run_in_executor 在异步中调用同步代码")
    print("6. 异步比多线程更轻量（单线程，无锁竞争）")
    print()
    print("选择指南：")
    print("  IO 密集型（网络请求、文件读写）→ asyncio")
    print("  CPU 密集型（计算、图像处理）→ 多进程")
    print("  简单并发（少量线程）→ 多线程")
