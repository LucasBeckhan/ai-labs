# 01 - Python 基础与数据结构

## 核心概念

### 1. 可变 vs 不可变对象

Python 中一切皆对象，但对象分为两类：

**不可变对象（Immutable）**
- 创建后不能修改
- 包括：int, float, str, tuple, frozenset, bool
- 修改变量实际是创建新对象

**可变对象（Mutable）**
- 创建后可以原地修改
- 包括：list, dict, set, 自定义类实例
- 修改变量不会创建新对象

```python
# 不可变示例
x = 10
print(id(x))  # 例如：140712345678900
x += 1
print(id(x))  # 不同的 id，创建了新对象

# 可变示例
y = [1, 2, 3]
print(id(y))  # 例如：140712345679000
y.append(4)
print(id(y))  # 相同的 id，原地修改
```

**为什么重要？**
- 函数参数传递：可变对象可能被意外修改
- 字典键：必须是不可变对象（需要稳定的 hash 值）
- 并发安全：不可变对象天然线程安全

### 2. `is` vs `==`

```python
a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)  # True：值相等
print(a is b)  # False：不是同一个对象

c = a
print(a is c)  # True：同一个对象
```

**例外：小整数和短字符串缓存**
```python
x = 100
y = 100
print(x is y)  # True：Python 缓存 -5 到 256 的整数

s1 = "hello"
s2 = "hello"
print(s1 is s2)  # True：字符串驻留（interning）
```

### 3. 列表推导式 vs 生成器表达式

```python
# 列表推导式：立即生成完整列表，占用内存
squares_list = [x**2 for x in range(1000000)]  # 占用 ~8MB 内存

# 生成器表达式：惰性计算，按需生成，节省内存
squares_gen = (x**2 for x in range(1000000))    # 占用 ~100 字节
```

**何时使用？**
- 数据量小且需要多次访问：列表推导式
- 数据量大或只需遍历一次：生成器表达式
- 管道式处理：生成器表达式（可链式组合）

### 4. 字典的哈希表实现

Python 字典基于哈希表，平均 O(1) 的查找/插入/删除：

```python
d = {"name": "Alice", "age": 30}
# 内部实现：
# 1. 计算 key 的 hash 值：hash("name") = 1234567890
# 2. 映射到数组索引：1234567890 % table_size
# 3. 存储 (key, value) 到该位置
```

**哈希碰撞处理**
- Python 使用开放寻址法（Open Addressing）
- 碰撞时探测下一个位置（线性探测 + 伪随机）
- 负载因子超过 2/3 时自动扩容

**为什么字典键必须是不可变的？**
- 可变对象的 hash 值可能改变
- hash 改变后，无法通过原 hash 找到存储位置

### 5. 集合的底层原理

集合（set）本质是只有 key 的字典：

```python
s = {1, 2, 3}
# 内部实现类似：{1: None, 2: None, 3: None}
```

**高效操作（平均 O(1)）**
- 成员检查：`x in s`
- 添加/删除：`s.add(x)`, `s.remove(x)`

**集合运算**
```python
a = {1, 2, 3}
b = {2, 3, 4}

print(a | b)  # 并集：{1, 2, 3, 4}
print(a & b)  # 交集：{2, 3}
print(a - b)  # 差集：{1}
print(a ^ b)  # 对称差集：{1, 4}
```

## 面试题精选

### Q1: `is` 和 `==` 的区别？
**答**：
- `==` 比较值是否相等（调用 `__eq__` 方法）
- `is` 比较是否是同一个对象（比较内存地址）

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b  # True：值相等
a is b  # False：不同对象
```

### Q2: 浅拷贝和深拷贝的区别？
**答**：
```python
import copy

original = [[1, 2], [3, 4]]

# 浅拷贝：只复制顶层对象，嵌套对象仍是引用
shallow = copy.copy(original)
shallow[0].append(999)
print(original)  # [[1, 2, 999], [3, 4]]：原对象被修改

# 深拷贝：递归复制所有层级
deep = copy.deepcopy(original)
deep[0].append(888)
print(original)  # [[1, 2, 999], [3, 4]]：原对象未受影响
```

### Q3: 什么是 GIL？对多线程有什么影响？
**答**：
- **GIL（Global Interpreter Lock）**：CPython 解释器的全局锁
- **作用**：同一时刻只允许一个线程执行 Python 字节码
- **影响**：
  - CPU 密集型任务：多线程无法并行，甚至比单线程慢
  - IO 密集型任务：多线程有效（等待 IO 时释放 GIL）
- **解决方案**：
  - CPU 密集型：使用多进程（multiprocessing）
  - IO 密集型：使用多线程或 asyncio

### Q4: 为什么字典的键必须是不可变的？
**答**：
- 字典通过 hash(key) 定位存储位置
- 可变对象的 hash 值可能改变（如列表添加元素后）
- hash 改变后，无法通过原 hash 找到该键值对
- 不可变对象（str, int, tuple）的 hash 值稳定

```python
d = {}
d[[1, 2]] = "value"  # TypeError: unhashable type: 'list'
d[(1, 2)] = "value"  # OK：tuple 是不可变的
```

### Q5: 列表推导式和生成器表达式的区别？
**答**：
```python
# 列表推导式：立即生成完整列表
list_comp = [x**2 for x in range(1000000)]  # 占用内存

# 生成器表达式：惰性计算，按需生成
gen_expr = (x**2 for x in range(1000000))  # 几乎不占内存

# 使用场景
sum(list_comp)  # 可以多次访问
sum(gen_expr)   # 只能遍历一次，之后生成器耗尽
```

## 练习题

1. **可变对象陷阱**：解释以下代码的输出
```python
def add_item(item, lst=[]):
    lst.append(item)
    return lst

print(add_item(1))
print(add_item(2))
print(add_item(3))
```

2. **字典合并**：用三种方式合并两个字典
```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 3, "c": 4}
# 方式 1：update()
# 方式 2：字典解包（Python 3.5+）
# 方式 3：| 运算符（Python 3.9+）
```

3. **集合优化**：以下代码的时间复杂度是多少？如何优化？
```python
# 查找列表中的重复元素
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return duplicates
```

## 运行示例

```bash
cd 01-basics
python3 mutable_immutable.py
python3 list_vs_generator.py
python3 dict_set_demo.py
```

## 扩展阅读

- [Python 数据模型](https://docs.python.org/3/reference/datamodel.html)
- [时间复杂度速查](https://wiki.python.org/moin/TimeComplexity)
- [GIL 深度解析](https://realpython.com/python-gil/)
