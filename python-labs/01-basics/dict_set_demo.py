#!/usr/bin/env python3
"""
字典与集合的底层原理

核心概念：
- 字典基于哈希表实现，平均 O(1) 查找
- 集合本质是只有键的字典
- 哈希碰撞的处理机制
- 高效操作的最佳实践
"""

import sys
import time


def demo_dict_hash():
    """演示字典的哈希表原理"""
    print("=" * 60)
    print("1. 字典的哈希表原理")
    print("=" * 60)
    
    # 哈希值计算
    key = "hello"
    hash_value = hash(key)
    print(f"键 '{key}' 的哈希值：{hash_value}")
    print(f"二进制表示：{bin(hash_value)}\n")
    
    # 不同对象的哈希值
    keys = ["hello", 42, (1, 2, 3), True]
    print("不同键的哈希值：")
    for key in keys:
        print(f"  {key!r:20} → hash = {hash(key)}")
    print()
    
    # 哈希碰撞演示
    print("哈希碰撞（人为构造）：")
    class BadHash:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            return 42  # 所有对象返回相同哈希值
        
        def __eq__(self, other):
            return self.value == other.value
    
    a = BadHash(1)
    b = BadHash(2)
    print(f"hash(a) = {hash(a)}, hash(b) = {hash(b)}")
    print(f"→ 哈希碰撞！字典会用 == 比较区分它们\n")
    
    # 字典内部结构
    d = {"a": 1, "b": 2, "c": 3}
    print(f"字典 d = {d}")
    print(f"内存占用：{sys.getsizeof(d)} bytes")
    print(f"→ 字典预分配空间，即使只有 3 个元素也占用较多内存\n")


def demo_dict_performance():
    """演示字典操作的性能"""
    print("=" * 60)
    print("2. 字典操作性能")
    print("=" * 60)
    
    # 构建大字典
    n = 100_000
    print(f"构建 {n:,} 个键值对的字典...")
    start = time.time()
    d = {f"key_{i}": i for i in range(n)}
    build_time = time.time() - start
    print(f"耗时：{build_time:.3f} s")
    print(f"内存：{sys.getsizeof(d) / 1024 / 1024:.1f} MB\n")
    
    # 查找性能
    test_keys = [f"key_{i}" for i in range(0, n, n // 100)]
    
    start = time.time()
    for key in test_keys:
        _ = d[key]
    lookup_time = time.time() - start
    
    print(f"查找 {len(test_keys)} 个键：")
    print(f"  总耗时：{lookup_time*1000:.3f} ms")
    print(f"  平均每次：{lookup_time/len(test_keys)*1000000:.1f} μs")
    print(f"  → O(1) 查找，与字典大小无关\n")
    
    # 删除性能
    start = time.time()
    for key in test_keys:
        del d[key]
    delete_time = time.time() - start
    
    print(f"删除 {len(test_keys)} 个键：")
    print(f"  总耗时：{delete_time*1000:.3f} ms")
    print(f"  平均每次：{delete_time/len(test_keys)*1000000:.1f} μs\n")


def demo_dict_methods():
    """演示字典的常用方法"""
    print("=" * 60)
    print("3. 字典的常用方法")
    print("=" * 60)
    
    d = {"a": 1, "b": 2, "c": 3}
    print(f"原始字典：{d}\n")
    
    # get() - 安全获取
    print("get() - 安全获取（不存在返回默认值）：")
    print(f"  d.get('a') = {d.get('a')}")
    print(f"  d.get('z') = {d.get('z')}")
    print(f"  d.get('z', 0) = {d.get('z', 0)}\n")
    
    # setdefault() - 获取或设置默认值
    print("setdefault() - 获取或设置默认值：")
    print(f"  d.setdefault('d', 4) = {d.setdefault('d', 4)}")
    print(f"  d = {d}\n")
    
    # update() - 批量更新
    print("update() - 批量更新：")
    d.update({"e": 5, "f": 6})
    print(f"  d.update({{'e': 5, 'f': 6}})")
    print(f"  d = {d}\n")
    
    # pop() - 删除并返回
    print("pop() - 删除并返回：")
    value = d.pop("f")
    print(f"  d.pop('f') = {value}")
    print(f"  d = {d}\n")
    
    # items(), keys(), values()
    print("视图方法：")
    print(f"  d.keys() = {list(d.keys())}")
    print(f"  d.values() = {list(d.values())}")
    print(f"  d.items() = {list(d.items())}\n")


def demo_set_operations():
    """演示集合运算"""
    print("=" * 60)
    print("4. 集合运算")
    print("=" * 60)
    
    a = {1, 2, 3, 4, 5}
    b = {4, 5, 6, 7, 8}
    
    print(f"a = {a}")
    print(f"b = {b}\n")
    
    # 并集
    print("并集（a | b）：")
    print(f"  {a | b}")
    print(f"  a.union(b) = {a.union(b)}\n")
    
    # 交集
    print("交集（a & b）：")
    print(f"  {a & b}")
    print(f"  a.intersection(b) = {a.intersection(b)}\n")
    
    # 差集
    print("差集（a - b）：")
    print(f"  {a - b}")
    print(f"  a.difference(b) = {a.difference(b)}\n")
    
    # 对称差集
    print("对称差集（a ^ b）：")
    print(f"  {a ^ b}")
    print(f"  a.symmetric_difference(b) = {a.symmetric_difference(b)}\n")
    
    # 子集和超集
    c = {1, 2, 3}
    print(f"c = {c}")
    print(f"  c.issubset(a) = {c.issubset(a)}")
    print(f"  a.issuperset(c) = {a.issuperset(c)}\n")


def demo_set_performance():
    """演示集合的性能优势"""
    print("=" * 60)
    print("5. 集合 vs 列表的性能对比")
    print("=" * 60)
    
    # 成员检查
    n = 100_000
    lst = list(range(n))
    st = set(range(n))
    
    test_values = [0, n // 2, n - 1, n + 1]
    
    print(f"数据量：{n:,}")
    print(f"测试值：{test_values}\n")
    
    # 列表成员检查
    start = time.time()
    for val in test_values:
        _ = val in lst
    list_time = time.time() - start
    
    print(f"列表成员检查（val in lst）：")
    print(f"  总耗时：{list_time*1000:.3f} ms")
    print(f"  平均每次：{list_time/len(test_values)*1000:.3f} ms")
    print(f"  → O(n) 线性查找\n")
    
    # 集合成员检查
    start = time.time()
    for val in test_values:
        _ = val in st
    set_time = time.time() - start
    
    print(f"集合成员检查（val in st）：")
    print(f"  总耗时：{set_time*1000:.3f} ms")
    print(f"  平均每次：{set_time/len(test_values)*1000:.3f} ms")
    print(f"  → O(1) 哈希查找\n")
    
    speedup = list_time / set_time
    print(f"→ 集合比列表快 {speedup:.0f} 倍\n")


def demo_dict_set_memory():
    """演示字典和集合的内存占用"""
    print("=" * 60)
    print("6. 内存占用对比")
    print("=" * 60)
    
    n = 10_000
    
    # 列表
    lst = list(range(n))
    list_size = sys.getsizeof(lst)
    
    # 字典
    d = {i: i for i in range(n)}
    dict_size = sys.getsizeof(d)
    
    # 集合
    st = set(range(n))
    set_size = sys.getsizeof(st)
    
    print(f"数据量：{n:,} 个整数\n")
    print(f"列表：{list_size / 1024:.1f} KB")
    print(f"字典：{dict_size / 1024:.1f} KB（{dict_size / list_size:.1f}x）")
    print(f"集合：{set_size / 1024:.1f} KB（{set_size / list_size:.1f}x）\n")
    
    print("→ 字典和集合占用更多内存（哈希表开销）")
    print("→ 但换来 O(1) 的查找性能\n")


def demo_dict_view():
    """演示字典视图对象"""
    print("=" * 60)
    print("7. 字典视图对象")
    print("=" * 60)
    
    d = {"a": 1, "b": 2, "c": 3}
    
    # 获取视图
    keys_view = d.keys()
    values_view = d.values()
    items_view = d.items()
    
    print(f"字典：{d}")
    print(f"keys_view = d.keys() → {keys_view}")
    print(f"values_view = d.values() → {values_view}")
    print(f"items_view = d.items() → {items_view}\n")
    
    # 视图是动态的
    print("视图是动态的（反映字典变化）：")
    d["d"] = 4
    print(f"  d['d'] = 4 后")
    print(f"  keys_view = {keys_view}")
    print(f"  → 自动包含新键\n")
    
    # 视图支持集合运算
    print("视图支持集合运算：")
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    
    print(f"  d1.keys() = {d1.keys()}")
    print(f"  d2.keys() = {d2.keys()}")
    print(f"  d1.keys() & d2.keys() = {d1.keys() & d2.keys()}")
    print(f"  d1.keys() | d2.keys() = {d1.keys() | d2.keys()}")
    print(f"  d1.keys() - d2.keys() = {d1.keys() - d2.keys()}\n")


def demo_best_practices():
    """演示最佳实践"""
    print("=" * 60)
    print("8. 最佳实践")
    print("=" * 60)
    
    print("✅ 使用 get() 避免 KeyError：")
    print("  d.get('key', default_value)")
    print("  而不是：d['key'] if 'key' in d else default_value\n")
    
    print("✅ 使用 setdefault() 初始化嵌套结构：")
    print("  d = {}")
    print("  d.setdefault('users', []).append('Alice')")
    print("  → {'users': ['Alice']}\n")
    
    print("✅ 使用集合去重：")
    print("  unique_items = list(set(items))")
    print("  而不是：遍历列表检查是否已存在\n")
    
    print("✅ 使用集合运算替代嵌套循环：")
    print("  common = set1 & set2  # 交集")
    print("  而不是：[x for x in set1 if x in set2]\n")
    
    print("✅ 预分配字典大小（如果知道）：")
    print("  d = {k: None for k in range(1000000)}")
    print("  而不是：逐步添加导致多次扩容\n")


if __name__ == "__main__":
    demo_dict_hash()
    demo_dict_performance()
    demo_dict_methods()
    demo_set_operations()
    demo_set_performance()
    demo_dict_set_memory()
    demo_dict_view()
    demo_best_practices()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 字典和集合基于哈希表，平均 O(1) 操作")
    print("2. 哈希碰撞通过 == 比较解决")
    print("3. 集合成员检查比列表快数千倍")
    print("4. 字典视图是动态的，支持集合运算")
    print("5. 使用 get() 和 setdefault() 避免 KeyError")
