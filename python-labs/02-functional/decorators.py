#!/usr/bin/env python3
"""
装饰器深入

演示内容：
1. 装饰器基础（函数装饰器）
2. 带参数的装饰器
3. 类装饰器
4. 装饰器堆叠
5. 装饰器最佳实践
"""

import time
import functools
from typing import Callable, Any


def demo_basic_decorator():
    """基础装饰器"""
    print("=" * 60)
    print("1. 基础装饰器")
    print("=" * 60)
    
    # 最简单的装饰器
    def my_decorator(func):
        def wrapper():
            print(">>> 函数执行前")
            result = func()
            print("<<< 函数执行后")
            return result
        return wrapper
    
    @my_decorator
    def say_hello():
        print("Hello!")
    
    print("调用 say_hello()：")
    say_hello()
    print()
    
    # 等价的非装饰器写法
    def say_hi():
        print("Hi!")
    
    say_hi = my_decorator(say_hi)
    print("等价写法：say_hi = my_decorator(say_hi)")
    say_hi()
    print()


def demo_decorator_with_args():
    """带参数的装饰器"""
    print("=" * 60)
    print("2. 带参数的装饰器")
    print("=" * 60)
    
    # 装饰器工厂函数
    def repeat(times):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for _ in range(times):
                    result = func(*args, **kwargs)
                return result
            return wrapper
        return decorator
    
    @repeat(times=3)
    def greet(name):
        print(f"Hello, {name}!")
    
    print("调用 greet('Alice')（重复 3 次）：")
    greet("Alice")
    print()
    
    # 解释执行过程
    print("执行过程：")
    print("  @repeat(times=3)")
    print("  def greet(name): ...")
    print()
    print("  1. repeat(times=3) 返回 decorator 函数")
    print("  2. decorator(greet) 返回 wrapper 函数")
    print("  3. greet = wrapper")
    print()


def demo_decorator_with_func_args():
    """处理被装饰函数的参数"""
    print("=" * 60)
    print("3. 处理被装饰函数的参数")
    print("=" * 60)
    
    def log_args(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"调用 {func.__name__}{args}, {kwargs}")
            result = func(*args, **kwargs)
            print(f"返回: {result}")
            return result
        return wrapper
    
    @log_args
    def add(a, b):
        return a + b
    
    @log_args
    def greet(name, greeting="Hello"):
        return f"{greeting}, {name}!"
    
    print("调用 add(3, 5)：")
    add(3, 5)
    print()
    
    print("调用 greet('Bob', greeting='Hi')：")
    greet("Bob", greeting="Hi")
    print()


def demo_practical_decorators():
    """实用装饰器示例"""
    print("=" * 60)
    print("4. 实用装饰器示例")
    print("=" * 60)
    
    # 1. 计时装饰器
    def timer(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"{func.__name__} 耗时: {end - start:.4f} 秒")
            return result
        return wrapper
    
    @timer
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    print("【计时装饰器】")
    slow_function()
    print()
    
    # 2. 重试装饰器
    def retry(max_attempts=3, delay=0.1):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise
                        print(f"尝试 {attempt + 1} 失败: {e}")
                        time.sleep(delay)
            return wrapper
        return decorator
    
    @retry(max_attempts=3, delay=0.1)
    def unstable_function():
        import random
        if random.random() < 0.7:
            raise ValueError("随机失败")
        return "成功"
    
    print("【重试装饰器】")
    try:
        result = unstable_function()
        print(f"结果: {result}")
    except ValueError as e:
        print(f"最终失败: {e}")
    print()
    
    # 3. 缓存装饰器（手动实现）
    def cache(func):
        memo = {}
        @functools.wraps(func)
        def wrapper(*args):
            if args not in memo:
                memo[args] = func(*args)
            return memo[args]
        wrapper.cache = memo  # 暴露缓存
        return wrapper
    
    @cache
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    
    print("【缓存装饰器】")
    print(f"fibonacci(10) = {fibonacci(10)}")
    print(f"缓存内容: {fibonacci.cache}")
    print()
    
    # 4. 验证装饰器
    def validate_types(**type_hints):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 验证位置参数
                for i, (arg_name, arg_value) in enumerate(zip(func.__code__.co_varnames, args)):
                    if arg_name in type_hints:
                        expected_type = type_hints[arg_name]
                        if not isinstance(arg_value, expected_type):
                            raise TypeError(
                                f"参数 {arg_name} 应该是 {expected_type.__name__}，"
                                f"但得到了 {type(arg_value).__name__}"
                            )
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @validate_types(name=str, age=int)
    def create_user(name, age):
        return {"name": name, "age": age}
    
    print("【类型验证装饰器】")
    print(f"create_user('Alice', 30) = {create_user('Alice', 30)}")
    try:
        create_user("Bob", "25")  # age 应该是 int
    except TypeError as e:
        print(f"create_user('Bob', '25') → TypeError: {e}")
    print()


def demo_stacked_decorators():
    """装饰器堆叠"""
    print("=" * 60)
    print("5. 装饰器堆叠")
    print("=" * 60)
    
    def bold(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return f"<b>{func(*args, **kwargs)}</b>"
        return wrapper
    
    def italic(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return f"<i>{func(*args, **kwargs)}</i>"
        return wrapper
    
    @bold
    @italic
    def greet(name):
        return f"Hello, {name}"
    
    print("装饰器堆叠顺序：")
    print("  @bold")
    print("  @italic")
    print("  def greet(name): ...")
    print()
    print(f"greet('Alice') = {greet('Alice')}")
    print()
    
    # 执行顺序说明
    print("执行顺序（从内到外）：")
    print("  1. greet('Alice') → 'Hello, Alice'")
    print("  2. italic 包装 → '<i>Hello, Alice</i>'")
    print("  3. bold 包装 → '<b><i>Hello, Alice</i></b>'")
    print()


def demo_class_decorator():
    """类装饰器"""
    print("=" * 60)
    print("6. 类装饰器")
    print("=" * 60)
    
    # 类作为装饰器
    class CountCalls:
        def __init__(self, func):
            self.func = func
            self.count = 0
            functools.update_wrapper(self, func)
        
        def __call__(self, *args, **kwargs):
            self.count += 1
            print(f"{self.func.__name__} 被调用 {self.count} 次")
            return self.func(*args, **kwargs)
    
    @CountCalls
    def say_hello():
        print("Hello!")
    
    print("调用 say_hello() 3 次：")
    say_hello()
    say_hello()
    say_hello()
    print()
    
    # 带参数的类装饰器
    class Retry:
        def __init__(self, max_attempts=3):
            self.max_attempts = max_attempts
        
        def __call__(self, func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(self.max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == self.max_attempts - 1:
                            raise
                        print(f"尝试 {attempt + 1} 失败: {e}")
                return None
            return wrapper
    
    @Retry(max_attempts=3)
    def unstable_operation():
        import random
        if random.random() < 0.5:
            raise RuntimeError("随机失败")
        return "成功"
    
    print("带参数的类装饰器：")
    print("@Retry(max_attempts=3)")
    print("def unstable_operation(): ...")
    print()
    
    try:
        result = unstable_operation()
        print(f"结果: {result}")
    except RuntimeError as e:
        print(f"最终失败: {e}")
    print()


def functools_wraps_demo():
    """functools.wraps 的重要性"""
    print("=" * 60)
    print("7. functools.wraps 的重要性")
    print("=" * 60)
    
    # 不使用 wraps
    def bad_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    @bad_decorator
    def hello():
        """这是 hello 函数的文档字符串"""
        print("Hello!")
    
    print("不使用 @functools.wraps：")
    print(f"  hello.__name__ = '{hello.__name__}'")
    print(f"  hello.__doc__ = {hello.__doc__}")
    print()
    
    # 使用 wraps
    def good_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    @good_decorator
    def hello2():
        """这是 hello2 函数的文档字符串"""
        print("Hello!")
    
    print("使用 @functools.wraps：")
    print(f"  hello2.__name__ = '{hello2.__name__}'")
    print(f"  hello2.__doc__ = '{hello2.__doc__}'")
    print()
    
    print("最佳实践：总是使用 @functools.wraps")
    print()


def demo_decorator_patterns():
    """装饰器设计模式"""
    print("=" * 60)
    print("8. 装饰器设计模式")
    print("=" * 60)
    
    # 单例模式
    def singleton(cls):
        instances = {}
        @functools.wraps(cls)
        def get_instance(*args, **kwargs):
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]
        return get_instance
    
    @singleton
    class Database:
        def __init__(self):
            self.connection = "connected"
    
    db1 = Database()
    db2 = Database()
    print("【单例装饰器】")
    print(f"db1 = Database()")
    print(f"db2 = Database()")
    print(f"db1 is db2: {db1 is db2}")
    print()
    
    # 缓存方法
    def memoize_method(func):
        cache_attr = f'_cache_{func.__name__}'
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, cache_attr):
                setattr(self, cache_attr, {})
            cache = getattr(self, cache_attr)
            key = (args, tuple(sorted(kwargs.items())))
            if key not in cache:
                cache[key] = func(self, *args, **kwargs)
            return cache[key]
        return wrapper
    
    class Calculator:
        @memoize_method
        def expensive_computation(self, x, y):
            print(f"  计算 {x} + {y}...")
            time.sleep(0.1)
            return x + y
    
    print("【方法缓存装饰器】")
    calc = Calculator()
    print("第一次调用 calc.expensive_computation(1, 2)：")
    result1 = calc.expensive_computation(1, 2)
    print(f"  结果: {result1}")
    print("第二次调用 calc.expensive_computation(1, 2)：")
    result2 = calc.expensive_computation(1, 2)
    print(f"  结果: {result2}（从缓存获取）")
    print()


if __name__ == "__main__":
    demo_basic_decorator()
    demo_decorator_with_args()
    demo_decorator_with_func_args()
    demo_practical_decorators()
    demo_stacked_decorators()
    demo_class_decorator()
    functools_wraps_demo()
    demo_decorator_patterns()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 装饰器本质：接受函数，返回新函数")
    print("2. @decorator 语法是 func = decorator(func) 的简写")
    print("3. 使用 *args/**kwargs 处理任意参数")
    print("4. @functools.wraps 保留原函数元数据（必须使用）")
    print("5. 带参数的装饰器需要三层嵌套")
    print("6. 装饰器堆叠顺序：从下到上应用，从上到下执行")
    print("7. 类装饰器通过 __call__ 方法实现")
    print()
    print("常见应用场景：")
    print("  - 日志记录、性能监控")
    print("  - 缓存、重试、限流")
    print("  - 权限验证、参数校验")
    print("  - 单例模式、注册器")
