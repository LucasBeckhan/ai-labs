#!/usr/bin/env python3
"""
可变对象 vs 不可变对象演示

核心概念：
- 不可变对象（int, str, tuple）：修改时创建新对象
- 可变对象（list, dict, set）：可以原地修改
- is vs ==：身份比较 vs 值比较
"""

import sys


def demo_immutable():
    """演示不可变对象"""
    print("=" * 60)
    print("1. 不可变对象（int, str, tuple）")
    print("=" * 60)
    
    # 整数
    x = 10
    print(f"x = {x}, id = {id(x)}")
    x += 1  # 创建新对象
    print(f"x += 1 后: x = {x}, id = {id(x)}")
    print("→ id 改变，说明创建了新对象\n")
    
    # 字符串
    s = "hello"
    print(f"s = '{s}', id = {id(s)}")
    s += " world"  # 创建新字符串
    print(f"s += ' world' 后: s = '{s}', id = {id(s)}")
    print("→ 字符串不可变，拼接创建新对象\n")
    
    # 元组
    t = (1, 2, 3)
    print(f"t = {t}, id = {id(t)}")
    # t[0] = 99  # TypeError: 'tuple' object does not support item assignment
    print("→ 元组元素不可修改\n")


def demo_mutable():
    """演示可变对象"""
    print("=" * 60)
    print("2. 可变对象（list, dict, set）")
    print("=" * 60)
    
    # 列表
    lst = [1, 2, 3]
    print(f"lst = {lst}, id = {id(lst)}")
    lst.append(4)  # 原地修改
    print(f"lst.append(4) 后: lst = {lst}, id = {id(lst)}")
    print("→ id 不变，说明原地修改\n")
    
    # 字典
    d = {"a": 1}
    print(f"d = {d}, id = {id(d)}")
    d["b"] = 2  # 原地修改
    print(f"d['b'] = 2 后: d = {d}, id = {id(d)}")
    print("→ 字典可以原地添加键值对\n")
    
    # 集合
    s = {1, 2, 3}
    print(f"s = {s}, id = {id(s)}")
    s.add(4)  # 原地修改
    print(f"s.add(4) 后: s = {s}, id = {id(s)}")
    print("→ 集合可以原地添加元素\n")


def demo_is_vs_equals():
    """演示 is vs =="""
    print("=" * 60)
    print("3. is vs == 的区别")
    print("=" * 60)
    
    # 列表比较
    a = [1, 2, 3]
    b = [1, 2, 3]
    print(f"a = {a}, b = {b}")
    print(f"a == b: {a == b}  # 值相等")
    print(f"a is b: {a is b}  # 不是同一个对象")
    print(f"id(a) = {id(a)}, id(b) = {id(b)}\n")
    
    # 同一个对象
    c = a
    print(f"c = a")
    print(f"a is c: {a is c}  # 同一个对象")
    print(f"id(a) = {id(a)}, id(c) = {id(c)}\n")
    
    # 小整数缓存（-5 到 256）
    x = 100
    y = 100
    print(f"x = 100, y = 100")
    print(f"x is y: {x is y}  # 小整数被缓存，是同一个对象")
    
    x = 1000
    y = 1000
    print(f"x = 1000, y = 1000")
    print(f"x is y: {x is y}  # 大整数不缓存，不是同一个对象\n")
    
    # 字符串驻留
    s1 = "hello"
    s2 = "hello"
    print(f"s1 = 'hello', s2 = 'hello'")
    print(f"s1 is s2: {s1 is s2}  # 短字符串被驻留（interning）")
    
    s3 = "hello world!"
    s4 = "hello world!"
    print(f"s3 = 'hello world!', s4 = 'hello world!'")
    print(f"s3 is s4: {s3 is s4}  # 含特殊字符的长字符串可能不驻留\n")


def demo_copy():
    """演示浅拷贝 vs 深拷贝"""
    print("=" * 60)
    print("4. 浅拷贝 vs 深拷贝")
    print("=" * 60)
    
    import copy
    
    # 原始对象（嵌套列表）
    original = [[1, 2], [3, 4]]
    print(f"original = {original}")
    print(f"id(original) = {id(original)}")
    print(f"id(original[0]) = {id(original[0])}\n")
    
    # 浅拷贝
    shallow = copy.copy(original)
    print("浅拷贝: shallow = copy.copy(original)")
    print(f"id(shallow) = {id(shallow)}  # 新对象")
    print(f"id(shallow[0]) = {id(shallow[0])}  # 嵌套对象仍是引用")
    
    shallow[0].append(999)
    print(f"shallow[0].append(999)")
    print(f"shallow = {shallow}")
    print(f"original = {original}  # 原对象被修改！\n")
    
    # 深拷贝
    original = [[1, 2], [3, 4]]  # 重置
    deep = copy.deepcopy(original)
    print("深拷贝: deep = copy.deepcopy(original)")
    print(f"id(deep) = {id(deep)}  # 新对象")
    print(f"id(deep[0]) = {id(deep[0])}  # 嵌套对象也被复制")
    
    deep[0].append(888)
    print(f"deep[0].append(888)")
    print(f"deep = {deep}")
    print(f"original = {original}  # 原对象未受影响\n")


def demo_function_args():
    """演示函数参数传递的可变性陷阱"""
    print("=" * 60)
    print("5. 函数参数传递的可变性陷阱")
    print("=" * 60)
    
    def add_item(item, lst=[]):
        """危险的默认参数：可变对象作为默认值"""
        lst.append(item)
        return lst
    
    print("def add_item(item, lst=[]):")
    print("    lst.append(item)")
    print("    return lst\n")
    
    print(f"add_item(1) = {add_item(1)}")
    print(f"add_item(2) = {add_item(2)}  # 不是 [2]，而是 [1, 2]！")
    print(f"add_item(3) = {add_item(3)}  # [1, 2, 3]\n")
    
    print("原因：默认参数 lst 在函数定义时创建，后续调用共享同一个列表")
    print("修复方法：使用 None 作为默认值\n")
    
    def add_item_fixed(item, lst=None):
        """正确的默认参数"""
        if lst is None:
            lst = []
        lst.append(item)
        return lst
    
    print("def add_item_fixed(item, lst=None):")
    print("    if lst is None:")
    print("        lst = []")
    print("    lst.append(item)")
    print("    return lst\n")
    
    print(f"add_item_fixed(1) = {add_item_fixed(1)}")
    print(f"add_item_fixed(2) = {add_item_fixed(2)}")
    print(f"add_item_fixed(3) = {add_item_fixed(3)}\n")


def demo_memory_size():
    """演示不同对象的内存占用"""
    print("=" * 60)
    print("6. 对象内存占用对比")
    print("=" * 60)
    
    print("基本类型：")
    print(f"  int(0):           {sys.getsizeof(0)} bytes")
    print(f"  int(2**30):       {sys.getsizeof(2**30)} bytes")
    print(f"  float(3.14):      {sys.getsizeof(3.14)} bytes")
    print(f"  bool(True):       {sys.getsizeof(True)} bytes")
    print(f"  str(''):          {sys.getsizeof('')} bytes")
    print(f"  str('hello'):     {sys.getsizeof('hello')} bytes\n")
    
    print("集合类型：")
    print(f"  list([]):         {sys.getsizeof([])} bytes")
    print(f"  list([1,2,3]):    {sys.getsizeof([1,2,3])} bytes")
    print(f"  tuple(()):        {sys.getsizeof(())} bytes")
    print(f"  tuple((1,2,3)):   {sys.getsizeof((1,2,3))} bytes")
    print(f"  dict({{}}):         {sys.getsizeof({})} bytes")
    print(f"  dict(a=1,b=2):    {sys.getsizeof({'a':1,'b':2})} bytes")
    print(f"  set():            {sys.getsizeof(set())} bytes")
    print(f"  set([1,2,3]):     {sys.getsizeof({1,2,3})} bytes\n")
    
    print("生成器 vs 列表：")
    list_comp = [x**2 for x in range(1000)]
    gen_expr = (x**2 for x in range(1000))
    print(f"  [x**2 for x in range(1000)]:  {sys.getsizeof(list_comp)} bytes")
    print(f"  (x**2 for x in range(1000)):  {sys.getsizeof(gen_expr)} bytes")
    print(f"  → 生成器表达式节省 {sys.getsizeof(list_comp) - sys.getsizeof(gen_expr)} bytes\n")


if __name__ == "__main__":
    demo_immutable()
    demo_mutable()
    demo_is_vs_equals()
    demo_copy()
    demo_function_args()
    demo_memory_size()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. 不可变对象修改时创建新对象，可变对象可以原地修改")
    print("2. is 比较身份（内存地址），== 比较值")
    print("3. 浅拷贝只复制顶层，深拷贝递归复制所有层级")
    print("4. 避免使用可变对象作为函数默认参数")
    print("5. 生成器表达式比列表推导式更节省内存")
