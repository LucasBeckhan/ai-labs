# 模块 04：数据处理与分析

> **目标**：掌握 Python 数据处理的核心工具（NumPy、Pandas），能够高效处理和分析数据

## 核心概念

### 1. NumPy 基础

**NumPy** 是 Python 数值计算的基础库，提供高性能的多维数组对象。

**核心对象：ndarray**
```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])
matrix = np.array([[1, 2], [3, 4]])

# 常用创建方法
zeros = np.zeros((3, 4))        # 全 0 数组
ones = np.ones((2, 3))          # 全 1 数组
arange = np.arange(0, 10, 2)    # [0, 2, 4, 6, 8]
linspace = np.linspace(0, 1, 5) # [0, 0.25, 0.5, 0.75, 1]
```

**向量化操作**（比 Python 循环快 100 倍+）
```python
arr = np.array([1, 2, 3, 4])
arr * 2        # [2, 4, 6, 8]
arr + arr      # [2, 4, 6, 8]
np.sqrt(arr)   # [1, 1.414, 1.732, 2]
```

### 2. Pandas 基础

**Pandas** 是 Python 数据分析的核心库，提供 DataFrame 和 Series 数据结构。

**核心对象**：
- **Series**：一维标签数组（类似带索引的列表）
- **DataFrame**：二维标签表格（类似 Excel 表格）

```python
import pandas as pd

# 创建 Series
s = pd.Series([1, 2, 3], index=['a', 'b', 'c'])

# 创建 DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NY', 'SF', 'LA']
})
```

### 3. 数据读取与写入

```python
# CSV
df = pd.read_csv('data.csv')
df.to_csv('output.csv', index=False)

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
df.to_excel('output.xlsx', index=False)

# JSON
df = pd.read_json('data.json')
df.to_json('output.json')
```

### 4. 数据选择与过滤

```python
# 选择列
df['name']           # Series
df[['name', 'age']]  # DataFrame

# 选择行
df.iloc[0]           # 第一行（按位置）
df.loc[0]            # 第一行（按标签）
df.iloc[0:3]         # 前三行

# 条件过滤
df[df['age'] > 30]                    # 年龄 > 30
df[(df['age'] > 30) & (df['city'] == 'NY')]  # 多条件
```

### 5. 数据聚合与分组

```python
# 聚合函数
df['age'].mean()      # 平均值
df['age'].median()    # 中位数
df['age'].std()       # 标准差
df.describe()         # 统计摘要

# 分组聚合
df.groupby('city')['age'].mean()
df.groupby('city').agg({'age': ['mean', 'max'], 'name': 'count'})
```

## 面试题

### Q1: NumPy 数组比 Python 列表快在哪里？

**答案**：
1. **连续内存**：ndarray 在内存中连续存储，CPU 缓存友好
2. **向量化**：底层用 C 实现，避免 Python 循环开销
3. **类型一致**：所有元素类型相同，无需类型检查
4. **广播机制**：自动处理不同形状数组的运算

```python
# Python 列表：慢
sum([i*i for i in range(1000000)])  # ~100ms

# NumPy：快 100 倍
np.sum(np.arange(1000000)**2)       # ~1ms
```

### Q2: Pandas 的 merge、join、concat 有什么区别？

**答案**：
```python
# merge：类似 SQL JOIN，按列连接
pd.merge(df1, df2, on='key', how='inner')

# join：按索引连接（merge 的特例）
df1.join(df2, how='left')

# concat：简单拼接（纵向或横向）
pd.concat([df1, df2], axis=0)  # 纵向
pd.concat([df1, df2], axis=1)  # 横向
```

### Q3: 如何处理缺失值？

**答案**：
```python
# 检测缺失值
df.isnull().sum()           # 每列缺失数
df.isnull().any(axis=1)     # 哪些行有缺失

# 删除缺失值
df.dropna()                 # 删除有缺失的行
df.dropna(subset=['age'])   # 只检查 age 列

# 填充缺失值
df.fillna(0)                        # 填 0
df.fillna(df.mean())                # 填均值
df.fillna(method='ffill')           # 向前填充
df['age'].fillna(df['age'].median()) # 填中位数
```

### Q4: 如何优化 Pandas 性能？

**答案**：
1. **向量化操作**：避免 `apply()` 和循环
```python
# 慢
df['result'] = df.apply(lambda row: row['a'] + row['b'], axis=1)

# 快
df['result'] = df['a'] + df['b']
```

2. **选择合适的数据类型**
```python
df['category'] = df['category'].astype('category')  # 节省内存
df['id'] = df['id'].astype('int32')                  # 减小整数类型
```

3. **使用 `query()` 代替布尔索引**
```python
# 慢
df[(df['age'] > 30) & (df['city'] == 'NY')]

# 快
df.query('age > 30 and city == "NY"')
```

## 示例文件

### 1. numpy_basics.py
- NumPy 数组创建与操作
- 向量化计算性能对比
- 广播机制演示
- 常用数学函数

### 2. pandas_basics.py
- DataFrame 创建与操作
- 数据选择、过滤、排序
- 分组聚合（groupby）
- 数据透视表（pivot_table）

### 3. data_analysis.py
- 真实数据集分析（CSV 文件）
- 数据清洗（缺失值、重复值）
- 数据可视化（matplotlib）
- 完整分析流程示例

## 运行示例

```bash
cd 04-data-processing
python3 numpy_basics.py
python3 pandas_basics.py
python3 data_analysis.py
```

## 最佳实践

1. **优先使用向量化**：避免 Python 循环和 `apply()`
2. **选择合适的数据类型**：`category`、`int32` 等
3. **使用 `query()`**：比布尔索引更快更清晰
4. **避免链式赋值**：`df[df['a'] > 0]['b'] = 1` 会产生警告
5. **使用 `loc`/`iloc`**：明确指定行列索引
6. **大数据集用分块读取**：`pd.read_csv(chunksize=10000)`

## 学习路线

```
1. 掌握 NumPy 基础（数组、向量化、广播）
2. 学习 Pandas 核心操作（选择、过滤、聚合）
3. 练习真实数据集分析（清洗、转换、可视化）
4. 优化性能（向量化、数据类型、query）
```

## 扩展资源

- [NumPy 官方文档](https://numpy.org/doc/)
- [Pandas 官方文档](https://pandas.pydata.org/docs/)
- [Pandas 10 分钟入门](https://pandas.pydata.org/docs/user_guide/10min.html)
- [Kaggle Pandas 课程](https://www.kaggle.com/learn/pandas)
