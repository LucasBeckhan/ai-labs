#!/usr/bin/env python3
"""
列表推导式 vs 生成器表达式

核心概念：
- 列表推导式：立即生成完整列表，占用内存
- 生成器表达式：惰性计算，按需生成，节省内存
- 性能差异：内存 vs 速度
"""

import sys
import time


def demo_memory_usage():
    """演示内存占用差异"""
    print("=" * 60)
    print("1. 内存占用对比")
    print("=" * 60)
    
    # 小数据集
    n = 1000
    list_comp = [x**2 for x in range(n)]
    gen_expr = (x**2 for x in range(n))
    
    print(f"数据量：{n}")
    print(f"列表推导式内存：{sys.getsizeof(list_comp):,} bytes")
    print(f"生成器表达式内存：{sys.getsizeof(gen_expr):,} bytes")
    print(f"节省：{sys.getsizeof(list_comp) - sys.getsizeof(gen_expr):,} bytes\n")
    
    # 大数据集
    n = 10_000_000
    gen_expr = (x**2 for x in range(n))
    
    print(f"数据量：{n:,}")
    print(f"生成器表达式内存：{sys.getsizeof(gen_expr):,} bytes")
    
    # 注释掉列表推导式，避免内存溢出
    # list_comp = [x**2 for x in range(n)]  # 可能占用 ~800MB
    print(f"列表推导式（估算）：~{n * 8 / 1024 / 1024:.0f} MB")
    print(f"→ 生成器表达式节省 99.99% 内存\n")


def demo_lazy_evaluation():
    """演示惰性求值"""
    print("=" * 60)
    print("2. 惰性求值（Lazy Evaluation）")
    print("=" * 60)
    
    # 生成器不会立即计算
    print("创建生成器：gen = (x**2 for x in range(5))")
    gen = (x**2 for x in range(5))
    print(f"gen = {gen}")
    print(f"→ 生成器对象已创建，但尚未计算任何值\n")
    
    # 按需计算
    print("逐个获取值：")
    print(f"next(gen) = {next(gen)}")  # 计算 0**2
    print(f"next(gen) = {next(gen)}")  # 计算 1**2
    print(f"next(gen) = {next(gen)}")  # 计算 2**2
    print(f"→ 每次调用 next() 才计算下一个值\n")
    
    # 生成器只能遍历一次
    print("遍历剩余值：")
    for value in gen:
        print(f"  {value}")
    print("→ 生成器已耗尽\n")
    
    # 再次遍历
    print("再次遍历：")
    for value in gen:
        print(f"  {value}")
    print("→ 空！生成器只能使用一次\n")


def demo_early_termination():
    """演示提前终止的优势"""
    print("=" * 60)
    print("3. 提前终止的优势")
    print("=" * 60)
    
    # 场景：找到第一个满足条件的元素
    print("场景：找到第一个平方大于 50 的数\n")
    
    # 列表推导式：计算所有值
    print("列表推导式：")
    start = time.time()
    squares_list = [x**2 for x in range(100)]
    result = next(x for x in squares_list if x > 50)
    list_time = time.time() - start
    print(f"  结果：{result}")
    print(f"  耗时：{list_time*1000:.3f} ms")
    print(f"  计算了 {len(squares_list)} 个平方值\n")
    
    # 生成器表达式：按需计算
    print("生成器表达式：")
    start = time.time()
    squares_gen = (x**2 for x in range(100))
    result = next(x for x in squares_gen if x > 50)
    gen_time = time.time() - start
    print(f"  结果：{result}")
    print(f"  耗时：{gen_time*1000:.3f} ms")
    print(f"  只计算到满足条件的值（约 8 个）\n")
    
    print(f"→ 生成器快 {list_time/gen_time:.1f} 倍，且节省内存\n")


def demo_chaining():
    """演示生成器的链式组合"""
    print("=" * 60)
    print("4. 生成器的链式组合（Pipeline）")
    print("=" * 60)
    
    # 数据处理流水线
    print("场景：处理日志文件，找出 ERROR 级别的行并提取时间戳\n")
    
    # 模拟日志数据
    logs = [
        "2024-01-01 10:00:00 INFO User login",
        "2024-01-01 10:01:00 ERROR Database connection failed",
        "2024-01-01 10:02:00 INFO Request processed",
        "2024-01-01 10:03:00 ERROR Timeout occurred",
        "2024-01-01 10:04:00 INFO User logout",
    ]
    
    # 使用生成器链式处理
    print("生成器链式处理：")
    print("```python")
    print("lines = (line for line in logs)")
    print("errors = (line for line in lines if 'ERROR' in line)")
    print("timestamps = (line.split()[0] + ' ' + line.split()[1] for line in errors)")
    print("```\n")
    
    lines = (line for line in logs)
    errors = (line for line in lines if 'ERROR' in line)
    timestamps = (line.split()[0] + ' ' + line.split()[1] for line in errors)
    
    print("结果：")
    for ts in timestamps:
        print(f"  {ts}")
    
    print("\n→ 每个生成器按需处理，不会一次性加载所有数据到内存\n")


def demo_performance():
    """演示性能对比"""
    print("=" * 60)
    print("5. 性能对比：求和 100 万个平方数")
    print("=" * 60)
    
    n = 1_000_000
    
    # 列表推导式
    start = time.time()
    list_sum = sum([x**2 for x in range(n)])
    list_time = time.time() - start
    
    print(f"列表推导式：sum([x**2 for x in range({n:,})])")
    print(f"  结果：{list_sum:,}")
    print(f"  耗时：{list_time:.3f} s")
    print(f"  内存：~{n * 8 / 1024 / 1024:.0f} MB\n")
    
    # 生成器表达式
    start = time.time()
    gen_sum = sum(x**2 for x in range(n))
    gen_time = time.time() - start
    
    print(f"生成器表达式：sum(x**2 for x in range({n:,}))")
    print(f"  结果：{gen_sum:,}")
    print(f"  耗时：{gen_time:.3f} s")
    print(f"  内存：~{sys.getsizeof(x**2 for x in range(n))} bytes\n")
    
    print(f"→ 生成器稍慢（{gen_time/list_time:.2f}x），但内存节省 99.99%")
    print(f"→ 对于大数据集，内存节省远比速度差异重要\n")


def demo_use_cases():
    """演示使用场景"""
    print("=" * 60)
    print("6. 使用场景建议")
    print("=" * 60)
    
    print("✅ 使用列表推导式的场景：")
    print("  - 数据量小（< 10,000 个元素）")
    print("  - 需要多次访问结果")
    print("  - 需要索引访问（result[0]）")
    print("  - 需要获取长度（len(result)）\n")
    
    print("✅ 使用生成器表达式的场景：")
    print("  - 数据量大（> 100,000 个元素）")
    print("  - 只需遍历一次")
    print("  - 作为函数参数（如 sum(), max(), any()）")
    print("  - 链式处理（pipeline）")
    print("  - 处理文件流或无限序列\n")
    
    print("示例：")
    print("  # 列表推导式：需要多次访问")
    print("  squares = [x**2 for x in range(100)]")
    print("  print(squares[0], squares[50], squares[-1])\n")
    
    print("  # 生成器表达式：只需遍历一次")
    print("  total = sum(x**2 for x in range(1000000))\n")
    
    print("  # 生成器表达式：链式处理")
    print("  result = sum(x for x in data if x > 0 and x % 2 == 0)\n")


def demo_infinite_sequence():
    """演示无限序列"""
    print("=" * 60)
    print("7. 无限序列（只能用生成器）")
    print("=" * 60)
    
    # 无限斐波那契数列
    def fibonacci():
        a, b = 0, 1
        while True:
            yield a
            a, b = b, a + b
    
    print("无限斐波那契数列：")
    print("```python")
    print("def fibonacci():")
    print("    a, b = 0, 1")
    print("    while True:")
    print("        yield a")
    print("        a, b = b, a + b")
    print("```\n")
    
    fib = fibonacci()
    print("前 10 个斐波那契数：")
    first_10 = [next(fib) for _ in range(10)]
    print(f"  {first_10}\n")
    
    print("→ 无限序列只能用生成器，列表会导致内存溢出\n")


if __name__ == "__main__":
    demo_memory_usage()
    demo_lazy_evaluation()
    demo_early_termination()
    demo_chaining()
    demo_performance()
    demo_use_cases()
    demo_infinite_sequence()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 列表推导式：立即计算，占用内存，可多次访问")
    print("2. 生成器表达式：惰性计算，节省内存，只能遍历一次")
    print("3. 大数据集优先使用生成器，避免内存溢出")
    print("4. 生成器支持提前终止和链式组合")
    print("5. 无限序列只能用生成器")
