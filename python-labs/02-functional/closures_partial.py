#!/usr/bin/env python3
"""
闭包与 functools 模块

演示内容：
1. 闭包的概念与应用
2. nonlocal 关键字
3. functools.partial（偏函数）
4. functools.lru_cache（缓存）
5. functools.reduce（累积）
6. functools.total_ordering（自动补全比较方法）
"""

from functools import partial, lru_cache, reduce, total_ordering
import time


def demo_closure_basic():
    """闭包基础"""
    print("=" * 60)
    print("1. 闭包基础")
    print("=" * 60)
    
    # 什么是闭包？
    # 内部函数引用了外部函数的变量，即使外部函数已返回
    
    def outer(x):
        def inner(y):
            return x + y  # inner 引用了 outer 的变量 x
        return inner
    
    add5 = outer(5)
    add10 = outer(10)
    
    print(f"add5 = outer(5)")
    print(f"add10 = outer(10)")
    print(f"add5(3) = {add5(3)}")  # 5 + 3 = 8
    print(f"add10(3) = {add10(3)}")  # 10 + 3 = 13
    print()
    
    print("闭包三要素：")
    print("  1. 嵌套函数（inner 在 outer 内部）")
    print("  2. 内部函数引用外部变量（inner 使用 x）")
    print("  3. 外部函数返回内部函数（return inner）")
    print()
    
    # 查看闭包捕获的变量
    print(f"add5.__closure__ = {add5.__closure__}")
    print(f"add5.__closure__[0].cell_contents = {add5.__closure__[0].cell_contents}")
    print()


def demo_nonlocal():
    """nonlocal 关键字"""
    print("=" * 60)
    print("2. nonlocal 关键字")
    print("=" * 60)
    
    # 错误示例：无法修改外部变量
    def bad_counter():
        count = 0
        def increment():
            # count += 1  # UnboundLocalError: local variable 'count' referenced before assignment
            return count
        return increment
    
    print("错误示例（不用 nonlocal）：")
    print("  def bad_counter():")
    print("      count = 0")
    print("      def increment():")
    print("          count += 1  # Error!")
    print("          return count")
    print("      return increment")
    print()
    
    # 正确示例：使用 nonlocal
    def good_counter():
        count = 0
        def increment():
            nonlocal count  # 声明使用外部变量
            count += 1
            return count
        return increment
    
    print("正确示例（使用 nonlocal）：")
    counter = good_counter()
    print(f"  counter() = {counter()}")  # 1
    print(f"  counter() = {counter()}")  # 2
    print(f"  counter() = {counter()}")  # 3
    print()
    
    # 闭包隔离性
    counter1 = good_counter()
    counter2 = good_counter()
    print("闭包隔离性：")
    print(f"  counter1() = {counter1()}")  # 1
    print(f"  counter1() = {counter1()}")  # 2
    print(f"  counter2() = {counter2()}")  # 1（独立的计数器）
    print()


def demo_closure_applications():
    """闭包的实际应用"""
    print("=" * 60)
    print("3. 闭包的实际应用")
    print("=" * 60)
    
    # 应用 1：配置工厂
    def make_greeter(greeting):
        def greeter(name):
            return f"{greeting}, {name}!"
        return greeter
    
    hello = make_greeter("Hello")
    hi = make_greeter("Hi")
    
    print("【配置工厂】")
    print(f"  hello = make_greeter('Hello')")
    print(f"  hi = make_greeter('Hi')")
    print(f"  hello('Alice') = {hello('Alice')}")
    print(f"  hi('Bob') = {hi('Bob')}")
    print()
    
    # 应用 2：延迟计算
    def lazy_sum(*args):
        def calculate():
            return sum(args)
        return calculate
    
    print("【延迟计算】")
    total = lazy_sum(1, 2, 3, 4, 5)
    print(f"  total = lazy_sum(1, 2, 3, 4, 5)")
    print(f"  此时未计算，total 是一个函数")
    print(f"  total() = {total()}")  # 调用时才计算
    print()
    
    # 应用 3：函数增强
    def with_logging(func):
        def wrapper(*args, **kwargs):
            print(f"[LOG] 调用 {func.__name__}{args}")
            result = func(*args, **kwargs)
            print(f"[LOG] 返回 {result}")
            return result
        return wrapper
    
    def add(a, b):
        return a + b
    
    logged_add = with_logging(add)
    print("【函数增强】")
    print(f"  logged_add = with_logging(add)")
    print(f"  logged_add(3, 5):")
    logged_add(3, 5)
    print()


def demo_partial():
    """functools.partial（偏函数）"""
    print("=" * 60)
    print("4. functools.partial（偏函数）")
    print("=" * 60)
    
    # 固定部分参数
    def power(base, exponent):
        return base ** exponent
    
    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)
    
    print("固定 exponent 参数：")
    print(f"  square = partial(power, exponent=2)")
    print(f"  cube = partial(power, exponent=3)")
    print(f"  square(5) = {square(5)}")  # 5^2 = 25
    print(f"  cube(5) = {cube(5)}")  # 5^3 = 125
    print()
    
    # 固定位置参数
    def greet(greeting, name, punctuation):
        return f"{greeting}, {name}{punctuation}"
    
    hello = partial(greet, "Hello")
    hello_excited = partial(hello, punctuation="!")
    
    print("逐步固定参数：")
    print(f"  hello = partial(greet, 'Hello')")
    print(f"  hello_excited = partial(hello, punctuation='!')")
    print(f"  hello('Alice', '!') = {hello('Alice', '!')}")
    print(f"  hello_excited('Bob') = {hello_excited('Bob')}")
    print()
    
    # 实际应用场景
    print("实际应用场景：")
    
    # 1. 创建特定配置的函数
    import json
    dumps_compact = partial(json.dumps, separators=(',', ':'))
    dumps_pretty = partial(json.dumps, indent=2)
    
    data = {"name": "Alice", "age": 30}
    print(f"  dumps_compact(data) = {dumps_compact(data)}")
    print(f"  dumps_pretty(data):")
    print(dumps_pretty(data))
    print()
    
    # 2. 回调函数预设参数
    def callback(event, handler_name):
        print(f"[{handler_name}] 处理事件: {event}")
    
    button_click = partial(callback, handler_name="ButtonHandler")
    print("  button_click = partial(callback, handler_name='ButtonHandler')")
    print("  button_click('click'):")
    button_click("click")
    print()


def demo_lru_cache():
    """functools.lru_cache（缓存）"""
    print("=" * 60)
    print("5. functools.lru_cache（缓存）")
    print("=" * 60)
    
    # 未缓存的递归函数
    def fibonacci_slow(n):
        if n < 2:
            return n
        return fibonacci_slow(n-1) + fibonacci_slow(n-2)
    
    print("未缓存的斐波那契：")
    start = time.time()
    result = fibonacci_slow(30)
    time_slow = time.time() - start
    print(f"  fibonacci_slow(30) = {result}")
    print(f"  耗时: {time_slow:.4f} 秒")
    print()
    
    # 使用 lru_cache
    @lru_cache(maxsize=None)
    def fibonacci_fast(n):
        if n < 2:
            return n
        return fibonacci_fast(n-1) + fibonacci_fast(n-2)
    
    print("使用 @lru_cache 的斐波那契：")
    start = time.time()
    result = fibonacci_fast(30)
    time_fast = time.time() - start
    print(f"  fibonacci_fast(30) = {result}")
    print(f"  耗时: {time_fast:.6f} 秒")
    print(f"  加速比: {time_slow/time_fast:.0f}x")
    print()
    
    # 查看缓存信息
    print("缓存信息：")
    print(f"  fibonacci_fast.cache_info() = {fibonacci_fast.cache_info()}")
    print(f"  hits = {fibonacci_fast.cache_info().hits}（缓存命中次数）")
    print(f"  misses = {fibonacci_fast.cache_info().misses}（缓存未命中次数）")
    print()
    
    # 清除缓存
    fibonacci_fast.cache_clear()
    print(f"  fibonacci_fast.cache_clear()  # 清除缓存")
    print(f"  fibonacci_fast.cache_info() = {fibonacci_fast.cache_info()}")
    print()
    
    # maxsize 参数
    @lru_cache(maxsize=3)
    def cached_func(x):
        print(f"  计算 {x}...")
        return x * 2
    
    print("maxsize=3 的缓存（只保留最近 3 个）：")
    print(f"  cached_func(1) = {cached_func(1)}")
    print(f"  cached_func(2) = {cached_func(2)}")
    print(f"  cached_func(3) = {cached_func(3)}")
    print(f"  cached_func(1) = {cached_func(1)}")  # 缓存命中
    print(f"  cached_func(4) = {cached_func(4)}")  # 淘汰最老的 (2)
    print(f"  cached_func(2) = {cached_func(2)}")  # 缓存未命中，重新计算
    print()


def demo_reduce_function():
    """functools.reduce（累积计算）"""
    print("=" * 60)
    print("6. functools.reduce（累积计算）")
    print("=" * 60)
    
    # 基本用法
    numbers = [1, 2, 3, 4, 5]
    
    # 求和
    total = reduce(lambda x, y: x + y, numbers)
    print(f"numbers = {numbers}")
    print(f"reduce(lambda x, y: x + y, numbers) = {total}")
    print(f"  计算过程: ((((1+2)+3)+4)+5) = {total}")
    print()
    
    # 求积
    product = reduce(lambda x, y: x * y, numbers)
    print(f"reduce(lambda x, y: x * y, numbers) = {product}")
    print(f"  计算过程: ((((1*2)*3)*4)*5) = {product}")
    print()
    
    # 带初始值
    total_with_init = reduce(lambda x, y: x + y, numbers, 10)
    print(f"reduce(lambda x, y: x + y, numbers, 10) = {total_with_init}")
    print(f"  计算过程: (((((10+1)+2)+3)+4)+5) = {total_with_init}")
    print()
    
    # 实际应用：合并字典
    dicts = [{"a": 1}, {"b": 2}, {"c": 3}]
    merged = reduce(lambda x, y: {**x, **y}, dicts)
    print(f"合并字典列表：")
    print(f"  dicts = {dicts}")
    print(f"  reduce(lambda x, y: {{**x, **y}}, dicts) = {merged}")
    print()
    
    # 实际应用：链式属性访问
    data = {"user": {"profile": {"name": "Alice"}}}
    keys = ["user", "profile", "name"]
    result = reduce(lambda obj, key: obj[key], keys, data)
    print(f"链式属性访问：")
    print(f"  data = {data}")
    print(f"  keys = {keys}")
    print(f"  reduce(lambda obj, key: obj[key], keys, data) = '{result}'")
    print()


def demo_total_ordering():
    """functools.total_ordering（自动补全比较方法）"""
    print("=" * 60)
    print("7. functools.total_ordering（自动补全比较方法）")
    print("=" * 60)
    
    # 不用 total_ordering：需要实现所有比较方法
    class Point1:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        
        def __eq__(self, other):
            return self.x == other.x and self.y == other.y
        
        def __lt__(self, other):
            return (self.x, self.y) < (other.x, other.y)
        
        # 还需要手动实现 __le__, __gt__, __ge__
        def __le__(self, other):
            return self == other or self < other
        
        def __gt__(self, other):
            return not self <= other
        
        def __ge__(self, other):
            return not self < other
    
    # 使用 total_ordering：只需实现 __eq__ 和一个比较方法
    @total_ordering
    class Point2:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        
        def __eq__(self, other):
            return self.x == other.x and self.y == other.y
        
        def __lt__(self, other):
            return (self.x, self.y) < (other.x, other.y)
        
        # __le__, __gt__, __ge__ 自动生成！
    
    print("不用 total_ordering：")
    print("  需要手动实现 __eq__, __lt__, __le__, __gt__, __ge__")
    print()
    
    print("使用 @total_ordering：")
    print("  只需实现 __eq__ 和 __lt__（或其他一个比较方法）")
    print()
    
    p1 = Point2(1, 2)
    p2 = Point2(3, 4)
    
    print("测试 Point2：")
    print(f"  p1 = Point2(1, 2)")
    print(f"  p2 = Point2(3, 4)")
    print(f"  p1 < p2: {p1 < p2}")
    print(f"  p1 <= p2: {p1 <= p2}")
    print(f"  p1 > p2: {p1 > p2}")
    print(f"  p1 >= p2: {p1 >= p2}")
    print(f"  p1 == p2: {p1 == p2}")
    print()
    
    # 用于排序
    points = [Point2(3, 4), Point2(1, 2), Point2(2, 3)]
    sorted_points = sorted(points)
    print("排序测试：")
    print(f"  points = [(3,4), (1,2), (2,3)]")
    sorted_str = ", ".join(f"({p.x},{p.y})" for p in sorted_points)
    print(f"  sorted(points) = [{sorted_str}]")
    print()


if __name__ == "__main__":
    demo_closure_basic()
    demo_nonlocal()
    demo_closure_applications()
    demo_partial()
    demo_lru_cache()
    demo_reduce_function()
    demo_total_ordering()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 闭包 = 内部函数 + 捕获的外部变量")
    print("2. nonlocal 声明修改外部变量（而非创建局部变量）")
    print("3. partial 固定部分参数，创建专用函数")
    print("4. lru_cache 缓存函数结果，避免重复计算")
    print("5. reduce 累积计算（求和、求积、合并）")
    print("6. total_ordering 自动生成比较方法")
