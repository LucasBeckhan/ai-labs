#!/usr/bin/env python3
"""
高阶函数演示

演示内容：
1. 一等公民（函数作为参数和返回值）
2. map - 映射转换
3. filter - 过滤筛选
4. reduce - 累积归约
5. sorted - 自定义排序
6. 函数组合
"""

from functools import reduce


def demo_first_class():
    """函数是一等公民"""
    print("=" * 60)
    print("1. 函数是一等公民")
    print("=" * 60)
    
    # 函数可以赋值给变量
    def greet(name):
        return f"Hello, {name}!"
    
    say_hello = greet
    print(f"say_hello = greet")
    print(f"say_hello('Alice') = {say_hello('Alice')}")
    print()
    
    # 函数可以作为参数传递
    def apply(func, value):
        return func(value)
    
    result = apply(greet, "Bob")
    print(f"apply(greet, 'Bob') = {result}")
    print()
    
    # 函数可以作为返回值
    def make_multiplier(factor):
        def multiplier(x):
            return x * factor
        return multiplier
    
    double = make_multiplier(2)
    triple = make_multiplier(3)
    print(f"double = make_multiplier(2)")
    print(f"triple = make_multiplier(3)")
    print(f"double(5) = {double(5)}")
    print(f"triple(5) = {triple(5)}")
    print()


def demo_map():
    """map - 映射转换"""
    print("=" * 60)
    print("2. map - 映射转换")
    print("=" * 60)
    
    # 基本用法
    numbers = [1, 2, 3, 4, 5]
    squared = list(map(lambda x: x**2, numbers))
    print(f"numbers = {numbers}")
    print(f"map(lambda x: x**2, numbers) = {squared}")
    print()
    
    # 多个可迭代对象
    list1 = [1, 2, 3]
    list2 = [10, 20, 30]
    sums = list(map(lambda x, y: x + y, list1, list2))
    print(f"list1 = {list1}")
    print(f"list2 = {list2}")
    print(f"map(lambda x, y: x + y, list1, list2) = {sums}")
    print()
    
    # 实际应用：类型转换
    str_numbers = ["1", "2", "3", "4", "5"]
    int_numbers = list(map(int, str_numbers))
    print(f"str_numbers = {str_numbers}")
    print(f"list(map(int, str_numbers)) = {int_numbers}")
    print()
    
    # 实际应用：提取属性
    users = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]
    names = list(map(lambda u: u["name"], users))
    print("users = [{'name': 'Alice', 'age': 30}, ...]")
    print(f"map(lambda u: u['name'], users) = {names}")
    print()


def demo_filter():
    """filter - 过滤筛选"""
    print("=" * 60)
    print("3. filter - 过滤筛选")
    print("=" * 60)
    
    # 基本用法
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    evens = list(filter(lambda x: x % 2 == 0, numbers))
    print(f"numbers = {numbers}")
    print(f"filter(lambda x: x % 2 == 0, numbers) = {evens}")
    print()
    
    # 过滤 None 值
    data = [1, None, 2, None, 3, 4]
    cleaned = list(filter(None, data))
    print(f"data = {data}")
    print(f"list(filter(None, data)) = {cleaned}")
    print()
    
    # 实际应用：筛选符合条件的对象
    users = [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
        {"name": "Charlie", "age": 35, "active": True}
    ]
    active_users = list(filter(lambda u: u["active"], users))
    print("users = [{'name': 'Alice', 'age': 30, 'active': True}, ...]")
    print("filter(lambda u: u['active'], users):")
    for user in active_users:
        print(f"  {user}")
    print()
    
    # 组合 map 和 filter
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    even_squares = list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers)))
    print(f"先过滤偶数，再平方：")
    print(f"  {even_squares}")
    print()


def demo_reduce():
    """reduce - 累积归约"""
    print("=" * 60)
    print("4. reduce - 累积归约")
    print("=" * 60)
    
    # 基本用法：求和
    numbers = [1, 2, 3, 4, 5]
    total = reduce(lambda x, y: x + y, numbers)
    print(f"numbers = {numbers}")
    print(f"reduce(lambda x, y: x + y, numbers) = {total}")
    print(f"  计算过程: 1+2=3, 3+3=6, 6+4=10, 10+5=15")
    print()
    
    # 求积
    product = reduce(lambda x, y: x * y, numbers)
    print(f"reduce(lambda x, y: x * y, numbers) = {product}")
    print(f"  计算过程: 1*2=2, 2*3=6, 6*4=24, 24*5=120")
    print()
    
    # 带初始值
    total_with_init = reduce(lambda x, y: x + y, numbers, 100)
    print(f"reduce(lambda x, y: x + y, numbers, 100) = {total_with_init}")
    print(f"  计算过程: 100+1=101, 101+2=103, ...")
    print()
    
    # 实际应用：找最大值
    max_val = reduce(lambda x, y: x if x > y else y, numbers)
    print(f"reduce(lambda x, y: x if x > y else y, numbers) = {max_val}")
    print(f"  等价于 max(numbers)")
    print()
    
    # 实际应用：合并字典
    dicts = [
        {"a": 1},
        {"b": 2},
        {"c": 3}
    ]
    merged = reduce(lambda x, y: {**x, **y}, dicts)
    print("dicts = [{'a': 1}, {'b': 2}, {'c': 3}]")
    print(f"reduce(lambda x, y: {{**x, **y}}, dicts) = {merged}")
    print()
    
    # 实际应用：构建嵌套结构
    keys = ["user", "profile", "name"]
    nested = reduce(lambda d, k: {k: d}, reversed(keys), "Alice")
    print(f"keys = {keys}")
    print(f"构建嵌套字典: {nested}")
    print()


def demo_sorted():
    """sorted - 自定义排序"""
    print("=" * 60)
    print("5. sorted - 自定义排序")
    print("=" * 60)
    
    # 基本排序
    numbers = [5, 2, 8, 1, 9, 3]
    sorted_nums = sorted(numbers)
    print(f"numbers = {numbers}")
    print(f"sorted(numbers) = {sorted_nums}")
    print(f"sorted(numbers, reverse=True) = {sorted(numbers, reverse=True)}")
    print()
    
    # 自定义排序键
    words = ["banana", "apple", "cherry", "date"]
    sorted_by_len = sorted(words, key=len)
    print(f"words = {words}")
    print(f"sorted(words, key=len) = {sorted_by_len}")
    print()
    
    # 复杂对象排序
    users = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]
    sorted_by_age = sorted(users, key=lambda u: u["age"])
    print("users = [{'name': 'Alice', 'age': 30}, ...]")
    print("sorted(users, key=lambda u: u['age']):")
    for user in sorted_by_age:
        print(f"  {user}")
    print()
    
    # 多条件排序
    students = [
        {"name": "Alice", "grade": "A", "age": 20},
        {"name": "Bob", "grade": "B", "age": 21},
        {"name": "Charlie", "grade": "A", "age": 19}
    ]
    # 先按成绩升序，再按年龄降序
    sorted_students = sorted(students, key=lambda s: (s["grade"], -s["age"]))
    print("students = [{'name': 'Alice', 'grade': 'A', 'age': 20}, ...]")
    print("sorted(students, key=lambda s: (s['grade'], -s['age'])):")
    print("  （先按成绩升序，再按年龄降序）")
    for student in sorted_students:
        print(f"  {student}")
    print()
    
    # 使用 itemgetter 和 attrgetter
    from operator import itemgetter, attrgetter
    
    data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
    sorted_data = sorted(data, key=itemgetter(1))
    print(f"data = {data}")
    print(f"sorted(data, key=itemgetter(1)) = {sorted_data}")
    print()


def demo_composition():
    """函数组合"""
    print("=" * 60)
    print("6. 函数组合")
    print("=" * 60)
    
    # 简单组合
    def double(x):
        return x * 2
    
    def add_one(x):
        return x + 1
    
    def square(x):
        return x ** 2
    
    # 手动组合
    result = square(add_one(double(5)))
    print(f"square(add_one(double(5))) = {result}")
    print(f"  步骤: 5 → *2 → 10 → +1 → 11 → **2 → 121")
    print()
    
    # 创建组合函数
    def compose(*funcs):
        def composed(x):
            for func in reversed(funcs):
                x = func(x)
            return x
        return composed
    
    transform = compose(square, add_one, double)
    result = transform(5)
    print(f"transform = compose(square, add_one, double)")
    print(f"transform(5) = {result}")
    print()
    
    # 管道函数（从左到右）
    def pipe(*funcs):
        def piped(x):
            for func in funcs:
                x = func(x)
            return x
        return piped
    
    transform2 = pipe(double, add_one, square)
    result2 = transform2(5)
    print(f"transform2 = pipe(double, add_one, square)")
    print(f"transform2(5) = {result2}")
    print()
    
    # 实际应用：数据处理管道
    def strip(s):
        return s.strip()
    
    def lowercase(s):
        return s.lower()
    
    def remove_punctuation(s):
        import string
        return s.translate(str.maketrans("", "", string.punctuation))
    
    clean_text = pipe(strip, lowercase, remove_punctuation)
    
    text = "  Hello, World!  "
    result = clean_text(text)
    print(f"text = '{text}'")
    print(f"clean_text = pipe(strip, lowercase, remove_punctuation)")
    print(f"clean_text(text) = '{result}'")
    print()


if __name__ == "__main__":
    demo_first_class()
    demo_map()
    demo_filter()
    demo_reduce()
    demo_sorted()
    demo_composition()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 函数是一等公民：可以赋值、传参、返回")
    print("2. map：对每个元素应用函数，返回迭代器")
    print("3. filter：保留满足条件的元素")
    print("4. reduce：累积归约为单个值")
    print("5. sorted：支持自定义排序键和多条件排序")
    print("6. 函数组合：构建数据处理管道")
    print()
    print("最佳实践：")
    print("  - 优先使用列表推导式代替 map/filter（更 Pythonic）")
    print("  - reduce 适合累积操作（求和、合并等）")
    print("  - sorted 的 key 参数比 cmp 参数更简洁")
    print("  - 函数组合提高代码复用性")
