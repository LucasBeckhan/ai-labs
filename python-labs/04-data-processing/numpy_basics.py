#!/usr/bin/env python3
"""
NumPy 基础演示

演示内容：
1. 数组创建与基本操作
2. 索引与切片
3. 向量化计算
4. 广播机制
5. 常用数学函数
"""

import numpy as np
import time


def demo_array_creation():
    """数组创建方式"""
    print("=" * 60)
    print("1. 数组创建方式")
    print("=" * 60)
    
    # 从列表创建
    arr1 = np.array([1, 2, 3, 4, 5])
    print(f"从列表创建: {arr1}")
    print(f"  类型: {type(arr1)}, 数据类型: {arr1.dtype}\n")
    
    # 二维数组
    arr2 = np.array([[1, 2, 3], [4, 5, 6]])
    print(f"二维数组:\n{arr2}")
    print(f"  形状: {arr2.shape}, 维度: {arr2.ndim}\n")
    
    # 特殊数组
    zeros = np.zeros((3, 4))
    print(f"全零数组 (3x4):\n{zeros}\n")
    
    ones = np.ones((2, 3))
    print(f"全 1 数组 (2x3):\n{ones}\n")
    
    eye = np.eye(3)
    print(f"单位矩阵 (3x3):\n{eye}\n")
    
    # 序列数组
    arange = np.arange(0, 10, 2)
    print(f"arange(0, 10, 2): {arange}\n")
    
    linspace = np.linspace(0, 1, 5)
    print(f"linspace(0, 1, 5): {linspace}\n")
    
    # 随机数组
    rand = np.random.rand(2, 3)
    print(f"随机数组 (2x3):\n{rand}\n")
    
    randint = np.random.randint(0, 10, (3, 3))
    print(f"随机整数 (3x3, 0-9):\n{randint}\n")


def demo_indexing():
    """索引与切片"""
    print("=" * 60)
    print("2. 索引与切片")
    print("=" * 60)
    
    arr = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    print(f"数组: {arr}\n")
    
    # 基本索引
    print(f"arr[0] = {arr[0]}")
    print(f"arr[-1] = {arr[-1]}\n")
    
    # 切片
    print(f"arr[2:5] = {arr[2:5]}")
    print(f"arr[::2] = {arr[::2]} (步长 2)")
    print(f"arr[::-1] = {arr[::-1]} (反转)\n")
    
    # 二维数组索引
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    print(f"矩阵:\n{matrix}\n")
    
    print(f"matrix[0, 1] = {matrix[0, 1]}")
    print(f"matrix[1, :] = {matrix[1, :]} (第 2 行)")
    print(f"matrix[:, 2] = {matrix[:, 2]} (第 3 列)")
    print(f"matrix[0:2, 1:3] =\n{matrix[0:2, 1:3]} (子矩阵)\n")
    
    # 布尔索引
    arr = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    print(f"数组: {arr}")
    print(f"arr > 5: {arr > 5}")
    print(f"arr[arr > 5]: {arr[arr > 5]}\n")
    
    # 花式索引
    arr = np.array([10, 20, 30, 40, 50])
    indices = [0, 2, 4]
    print(f"数组: {arr}")
    print(f"花式索引 arr[[0, 2, 4]]: {arr[indices]}\n")


def demo_vectorization():
    """向量化计算"""
    print("=" * 60)
    print("3. 向量化计算")
    print("=" * 60)
    
    # 标量运算
    arr = np.array([1, 2, 3, 4])
    print(f"数组: {arr}")
    print(f"arr * 2 = {arr * 2}")
    print(f"arr + 10 = {arr + 10}")
    print(f"arr ** 2 = {arr ** 2}\n")
    
    # 数组运算
    a = np.array([1, 2, 3])
    b = np.array([4, 5, 6])
    print(f"a = {a}")
    print(f"b = {b}")
    print(f"a + b = {a + b}")
    print(f"a * b = {a * b} (逐元素相乘)")
    print(f"np.dot(a, b) = {np.dot(a, b)} (点积)\n")
    
    # 性能对比：Python 循环 vs NumPy 向量化
    n = 1000000
    
    # Python 循环
    start = time.time()
    result1 = sum(i * i for i in range(n))
    python_time = time.time() - start
    
    # NumPy 向量化
    start = time.time()
    arr = np.arange(n)
    result2 = np.sum(arr * arr)
    numpy_time = time.time() - start
    
    print("性能对比（计算 1² + 2² + ... + n²）:")
    print(f"  Python 循环: {python_time:.4f} 秒")
    print(f"  NumPy 向量化: {numpy_time:.4f} 秒")
    print(f"  加速比: {python_time / numpy_time:.1f}x")
    print(f"  结果一致: {result1 == result2}\n")


def demo_broadcasting():
    """广播机制"""
    print("=" * 60)
    print("4. 广播机制")
    print("=" * 60)
    
    # 标量与数组
    arr = np.array([1, 2, 3])
    print(f"数组: {arr}")
    print(f"arr + 10 = {arr + 10} (标量广播)\n")
    
    # 一维与二维
    matrix = np.array([[1, 2, 3], [4, 5, 6]])
    vector = np.array([10, 20, 30])
    print(f"矩阵 (2x3):\n{matrix}")
    print(f"\n向量 (3,): {vector}")
    print(f"\n矩阵 + 向量:\n{matrix + vector} (广播)\n")
    
    # 列向量广播
    col_vector = np.array([[10], [20]])
    print(f"列向量 (2x1):\n{col_vector}")
    print(f"\n矩阵 + 列向量:\n{matrix + col_vector} (广播)\n")
    
    # 广播规则
    print("广播规则：")
    print("  1. 维度不同时，从右边对齐")
    print("  2. 维度大小为 1 的自动扩展")
    print("  3. 维度大小必须相等或其中一个为 1")
    print()
    print("示例：")
    print("  (3, 4) + (4,)   → (3, 4) + (1, 4) → (3, 4) ✓")
    print("  (3, 4) + (3, 1) → (3, 4) + (3, 1) → (3, 4) ✓")
    print("  (3, 4) + (3,)   → (3, 4) + (1, 3) → 不兼容 ✗")
    print()


def demo_math_functions():
    """常用数学函数"""
    print("=" * 60)
    print("5. 常用数学函数")
    print("=" * 60)
    
    arr = np.array([1, 2, 3, 4, 5])
    print(f"数组: {arr}\n")
    
    # 统计函数
    print("【统计函数】")
    print(f"  np.sum(arr) = {np.sum(arr)}")
    print(f"  np.mean(arr) = {np.mean(arr)}")
    print(f"  np.median(arr) = {np.median(arr)}")
    print(f"  np.std(arr) = {np.std(arr):.4f} (标准差)")
    print(f"  np.var(arr) = {np.var(arr):.4f} (方差)")
    print(f"  np.min(arr) = {np.min(arr)}")
    print(f"  np.max(arr) = {np.max(arr)}\n")
    
    # 轴操作
    matrix = np.array([[1, 2, 3], [4, 5, 6]])
    print(f"矩阵:\n{matrix}\n")
    print(f"  np.sum(matrix) = {np.sum(matrix)} (全部求和)")
    print(f"  np.sum(matrix, axis=0) = {np.sum(matrix, axis=0)} (按列求和)")
    print(f"  np.sum(matrix, axis=1) = {np.sum(matrix, axis=1)} (按行求和)\n")
    
    # 数学函数
    arr = np.array([0, np.pi/6, np.pi/4, np.pi/3, np.pi/2])
    print(f"角度: {arr / np.pi * 180} 度")
    print(f"  sin: {np.sin(arr)}")
    print(f"  cos: {np.cos(arr)}\n")
    
    arr = np.array([1, 2, 3, 4])
    print(f"数组: {arr}")
    print(f"  sqrt: {np.sqrt(arr)}")
    print(f"  exp: {np.exp(arr)}")
    print(f"  log: {np.log(arr)}\n")
    
    # 排序
    arr = np.array([3, 1, 4, 1, 5, 9, 2, 6])
    print(f"数组: {arr}")
    print(f"  排序: {np.sort(arr)}")
    print(f"  排序索引: {np.argsort(arr)}")
    print(f"  唯一值: {np.unique(arr)}\n")


def demo_linear_algebra():
    """线性代数"""
    print("=" * 60)
    print("6. 线性代数")
    print("=" * 60)
    
    # 矩阵乘法
    A = np.array([[1, 2], [3, 4]])
    B = np.array([[5, 6], [7, 8]])
    
    print(f"矩阵 A:\n{A}\n")
    print(f"矩阵 B:\n{B}\n")
    
    print(f"A @ B (矩阵乘法):\n{A @ B}\n")
    print(f"np.dot(A, B):\n{np.dot(A, B)}\n")
    
    # 转置
    print(f"A.T (转置):\n{A.T}\n")
    
    # 逆矩阵
    print(f"np.linalg.inv(A) (逆矩阵):\n{np.linalg.inv(A)}\n")
    
    # 行列式
    print(f"np.linalg.det(A) (行列式): {np.linalg.det(A):.4f}\n")
    
    # 特征值
    eigenvalues, eigenvectors = np.linalg.eig(A)
    print(f"特征值: {eigenvalues}")
    print(f"特征向量:\n{eigenvectors}\n")


def demo_reshaping():
    """数组变形"""
    print("=" * 60)
    print("7. 数组变形")
    print("=" * 60)
    
    arr = np.arange(12)
    print(f"原始数组: {arr}\n")
    
    # reshape
    matrix = arr.reshape(3, 4)
    print(f"reshape(3, 4):\n{matrix}\n")
    
    # flatten
    flat = matrix.flatten()
    print(f"flatten(): {flat}\n")
    
    # transpose
    transposed = matrix.T
    print(f"转置:\n{transposed}\n")
    
    # 堆叠
    a = np.array([1, 2, 3])
    b = np.array([4, 5, 6])
    print(f"a = {a}")
    print(f"b = {b}")
    print(f"np.vstack([a, b]) (垂直堆叠):\n{np.vstack([a, b])}")
    print(f"np.hstack([a, b]) (水平堆叠): {np.hstack([a, b])}\n")


if __name__ == "__main__":
    demo_array_creation()
    demo_indexing()
    demo_vectorization()
    demo_broadcasting()
    demo_math_functions()
    demo_linear_algebra()
    demo_reshaping()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("1. NumPy 是 Python 数值计算的基础")
    print("2. 向量化操作比 Python 循环快 100 倍+")
    print("3. 广播机制自动处理不同形状的数组")
    print("4. 丰富的数学函数和线性代数支持")
    print("5. 掌握索引和切片是数据处理的基础")
