# 模块 02：函数式编程与装饰器

> **目标**：掌握 Python 函数式编程范式，理解装饰器原理与高级函数用法

## 核心概念

### 1. 一等函数（First-class Functions）

函数在 Python 中是一等公民，可以：
- 赋值给变量
- 作为参数传递
- 作为返回值
- 存储在数据结构中

```python
def square(x):
    return x ** 2

# 赋值给变量
f = square
print(f(5))  # 25

# 作为参数
def apply(func, x):
    return func(x)

print(apply(square, 5))  # 25

# 存储在列表
funcs = [square, abs, len]
```

### 2. 高阶函数

接受函数作为参数或返回函数的函数。

**内置高阶函数**：
- `map(func, iterable)` - 对每个元素应用函数
- `filter(func, iterable)` - 过滤满足条件的元素
- `sorted(iterable, key=func)` - 自定义排序
- `max/min(iterable, key=func)` - 自定义最值

```python
numbers = [1, 2, 3, 4, 5]

# map：平方每个元素
squared = list(map(lambda x: x**2, numbers))  # [1, 4, 9, 16, 25]

# filter：筛选偶数
evens = list(filter(lambda x: x % 2 == 0, numbers))  # [2, 4]

# sorted：按绝对值排序
nums = [-5, 3, -1, 4]
sorted_nums = sorted(nums, key=abs)  # [-1, 3, 4, -5]
```

### 3. Lambda 表达式

匿名函数，用于简单的单行函数。

```python
# 语法：lambda 参数: 表达式
square = lambda x: x ** 2
add = lambda x, y: x + y

# 常用于高阶函数
numbers = [1, 2, 3, 4]
squared = list(map(lambda x: x**2, numbers))

# 复杂场景建议用 def
def complex_logic(x):
    if x > 0:
        return x ** 2
    else:
        return -x
```

### 4. 闭包（Closure）

内部函数记住外部函数的变量。

```python
def make_multiplier(factor):
    def multiplier(x):
        return x * factor  # 记住外部的 factor
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))  # 10
print(triple(5))  # 15
```

**闭包三条件**：
1. 嵌套函数
2. 内部函数引用外部变量
3. 外部函数返回内部函数

### 5. 装饰器（Decorator）

**本质**：接受函数作为参数，返回新函数的高阶函数。

**语法糖**：`@decorator` 等价于 `func = decorator(func)`

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
# 输出：
# Before function call
# Hello!
# After function call
```

**多层装饰器**：从下往上应用，从上往下执行

```python
@decorator1
@decorator2
def func():
    pass

# 等价于
func = decorator1(decorator2(func))
```

### 6. functools 模块

**@lru_cache** - 缓存函数结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(100))  # 快速计算，缓存中间结果
```

**partial** - 固定部分参数

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
print(square(5))  # 25
```

**wraps** - 保留原函数元数据

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)  # 保留 func 的 __name__ 和 __doc__
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

## 面试题

### Q1: 什么是装饰器？手写一个计时装饰器

**答案**：
```python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {end - start:.4f} 秒")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "done"

slow_function()  # 输出：slow_function 耗时: 1.0012 秒
```

### Q2: 装饰器的执行顺序？

```python
@a
@b
@c
def func():
    pass
```

**应用顺序**：从下往上（c → b → a）  
**执行顺序**：从上往下（a → b → c）

等价于：`func = a(b(c(func)))`

### Q3: 带参数的装饰器怎么写？

```python
def repeat(times):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")
# 输出 3 次：Hello, Alice!
```

**三层嵌套**：
1. `repeat(times)` - 接受装饰器参数
2. `decorator(func)` - 接受被装饰函数
3. `wrapper(*args, **kwargs)` - 实际调用

### Q4: 闭包中修改外部变量？

```python
def make_counter():
    count = 0
    def counter():
        nonlocal count  # 声明使用外部变量
        count += 1
        return count
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
```

## 示例文件

### 1. higher_order_functions.py
- map/filter/reduce 实战
- sorted 自定义排序
- 函数组合（compose）

### 2. decorators.py
- 基础装饰器（计时、日志、重试）
- 带参数的装饰器
- 类装饰器
- 装饰器叠加

### 3. closures_partial.py
- 闭包原理与应用
- functools.partial 用法
- functools.wraps 的重要性
- lru_cache 缓存优化

## 运行示例

```bash
cd 02-functional
python3 higher_order_functions.py
python3 decorators.py
python3 closures_partial.py
```

## 最佳实践

1. **装饰器要用 @wraps**：保留原函数的元数据
2. **闭包用 nonlocal**：修改外部变量时显式声明
3. **lru_cache 用于纯函数**：相同输入总是相同输出
4. **装饰器保持简单**：复杂逻辑拆分为多个装饰器
5. **优先用内置函数**：map/filter 比循环更 Pythonic

## 学习路线

```
1. 理解一等函数 → 高阶函数
2. 掌握 lambda → 闭包
3. 手写简单装饰器 → 带参数装饰器
4. 学习 functools → 实战应用
```

## 扩展阅读

- [Python 官方文档 - 装饰器](https://docs.python.org/3/glossary.html#term-decorator)
- [Real Python - 装饰器详解](https://realpython.com/primer-on-python-decorators/)
- [Python 函数式编程指南](https://docs.python.org/3/howto/functional.html)
