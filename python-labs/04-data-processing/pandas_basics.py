"""
Pandas 基础操作演示

本示例演示 Pandas 的核心功能：
1. DataFrame 创建与基本操作
2. 数据选择与过滤
3. 数据清洗（缺失值处理）
4. 分组聚合（groupby）
5. 数据透视表
6. 数据合并（merge/join/concat）
"""

import pandas as pd
import numpy as np


def demo_dataframe_creation():
    """DataFrame 创建与基本操作"""
    print("=" * 60)
    print("1. DataFrame 创建与基本操作")
    print("=" * 60)
    
    # 从字典创建
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'city': ['New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Seattle'],
        'salary': [70000, 90000, 85000, 65000, 80000]
    }
    df = pd.DataFrame(data)
    
    print("\n从字典创建 DataFrame:")
    print(df)
    print(f"\n形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    print(f"索引: {df.index.tolist()}")
    print(f"数据类型:\n{df.dtypes}")
    
    # 基本信息
    print(f"\n基本信息:")
    print(df.info())
    
    # 统计摘要
    print(f"\n统计摘要:")
    print(df.describe())


def demo_selection_filtering():
    """数据选择与过滤"""
    print("\n" + "=" * 60)
    print("2. 数据选择与过滤")
    print("=" * 60)
    
    # 创建示例数据
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'city': ['New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Seattle'],
        'salary': [70000, 90000, 85000, 65000, 80000]
    }
    df = pd.DataFrame(data)
    
    # 选择列
    print("\n选择单列 (Series):")
    print(df['name'])
    
    print("\n选择多列 (DataFrame):")
    print(df[['name', 'age']])
    
    # 选择行
    print("\n选择行 (iloc - 按位置):")
    print(df.iloc[0])  # 第一行
    print("\n选择多行:")
    print(df.iloc[0:3])  # 前三行
    
    print("\n选择行 (loc - 按标签):")
    print(df.loc[0:2])  # 索引 0-2 的行
    
    # 条件过滤
    print("\n条件过滤 (age > 30):")
    print(df[df['age'] > 30])
    
    print("\n多条件过滤 (age > 25 且 salary > 70000):")
    print(df[(df['age'] > 25) & (df['salary'] > 70000)])
    
    # query 方法（更简洁）
    print("\n使用 query 方法:")
    print(df.query('age > 25 and salary > 70000'))


def demo_data_cleaning():
    """数据清洗（缺失值处理）"""
    print("\n" + "=" * 60)
    print("3. 数据清洗（缺失值处理）")
    print("=" * 60)
    
    # 创建含缺失值的数据
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, np.nan, 28, 32],
        'city': ['New York', 'San Francisco', 'Los Angeles', None, 'Seattle'],
        'salary': [70000, 90000, 85000, 65000, np.nan]
    }
    df = pd.DataFrame(data)
    
    print("\n原始数据（含缺失值）:")
    print(df)
    
    # 检测缺失值
    print("\n缺失值检测:")
    print(df.isnull())
    print(f"\n各列缺失值数量:\n{df.isnull().sum()}")
    
    # 删除缺失值
    print("\n删除含缺失值的行:")
    print(df.dropna())
    
    print("\n只删除所有值都为空的行:")
    print(df.dropna(how='all'))
    
    # 填充缺失值
    print("\n填充缺失值（用 0 填充）:")
    print(df.fillna(0))
    
    print("\n填充缺失值（用均值填充 age 列）:")
    df_filled = df.copy()
    df_filled['age'] = df_filled['age'].fillna(df_filled['age'].mean())
    print(df_filled)
    
    print("\n前向填充（用前一个值填充）:")
    print(df.fillna(method='ffill'))
    
    print("\n后向填充（用后一个值填充）:")
    print(df.fillna(method='bfill'))


def demo_groupby():
    """分组聚合（groupby）"""
    print("\n" + "=" * 60)
    print("4. 分组聚合（groupby）")
    print("=" * 60)
    
    # 创建示例数据
    data = {
        'department': ['Sales', 'Engineering', 'Sales', 'Engineering', 'HR', 'Sales'],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank'],
        'salary': [70000, 90000, 75000, 95000, 60000, 72000],
        'years': [3, 5, 2, 7, 1, 4]
    }
    df = pd.DataFrame(data)
    
    print("\n原始数据:")
    print(df)
    
    # 单列分组
    print("\n按部门分组（单列聚合）:")
    print(df.groupby('department')['salary'].mean())
    
    # 多列聚合
    print("\n按部门分组（多列聚合）:")
    print(df.groupby('department').agg({
        'salary': ['mean', 'max', 'min'],
        'years': 'sum'
    }))
    
    # 自定义聚合函数
    print("\n自定义聚合（薪资范围）:")
    def salary_range(x):
        return x.max() - x.min()
    
    print(df.groupby('department')['salary'].agg(['mean', salary_range]))
    
    # 分组后过滤
    print("\n筛选平均薪资 > 70000 的部门:")
    grouped = df.groupby('department')['salary'].mean()
    print(grouped[grouped > 70000])


def demo_pivot_table():
    """数据透视表"""
    print("\n" + "=" * 60)
    print("5. 数据透视表")
    print("=" * 60)
    
    # 创建示例数据
    data = {
        'date': ['2024-01', '2024-01', '2024-01', '2024-02', '2024-02', '2024-02'],
        'product': ['A', 'B', 'A', 'B', 'A', 'B'],
        'region': ['North', 'South', 'North', 'South', 'North', 'South'],
        'sales': [100, 150, 120, 180, 110, 160]
    }
    df = pd.DataFrame(data)
    
    print("\n原始数据:")
    print(df)
    
    # 基本透视表
    print("\n基本透视表（按产品和地区汇总销售额）:")
    pivot = pd.pivot_table(
        df,
        values='sales',
        index='product',
        columns='region',
        aggfunc='sum'
    )
    print(pivot)
    
    # 多聚合函数
    print("\n多聚合函数（sum 和 mean）:")
    pivot_multi = pd.pivot_table(
        df,
        values='sales',
        index='product',
        columns='region',
        aggfunc=['sum', 'mean']
    )
    print(pivot_multi)
    
    # 添加边际（总计）
    print("\n添加边际（总计）:")
    pivot_margins = pd.pivot_table(
        df,
        values='sales',
        index='product',
        columns='region',
        aggfunc='sum',
        margins=True
    )
    print(pivot_margins)


def demo_merge_join():
    """数据合并（merge/join/concat）"""
    print("\n" + "=" * 60)
    print("6. 数据合并（merge/join/concat）")
    print("=" * 60)
    
    # 创建示例数据
    df1 = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    })
    
    df2 = pd.DataFrame({
        'id': [2, 3, 4, 5],
        'department': ['Engineering', 'Sales', 'HR', 'Marketing']
    })
    
    print("\nDataFrame 1:")
    print(df1)
    print("\nDataFrame 2:")
    print(df2)
    
    # merge - 类似 SQL JOIN
    print("\n内连接 (inner join):")
    print(pd.merge(df1, df2, on='id', how='inner'))
    
    print("\n左连接 (left join):")
    print(pd.merge(df1, df2, on='id', how='left'))
    
    print("\n右连接 (right join):")
    print(pd.merge(df1, df2, on='id', how='right'))
    
    print("\n外连接 (outer join):")
    print(pd.merge(df1, df2, on='id', how='outer'))
    
    # concat - 简单拼接
    df3 = pd.DataFrame({
        'id': [5, 6],
        'name': ['Eve', 'Frank']
    })
    
    print("\n纵向拼接 (concat axis=0):")
    print(pd.concat([df1, df3], ignore_index=True))
    
    # 横向拼接
    df4 = pd.DataFrame({
        'age': [25, 30, 35, 40]
    })
    
    print("\n横向拼接 (concat axis=1):")
    print(pd.concat([df1, df4], axis=1))


def demo_performance_tips():
    """性能优化技巧"""
    print("\n" + "=" * 60)
    print("7. 性能优化技巧")
    print("=" * 60)
    
    # 创建大数据集
    n = 100000
    df = pd.DataFrame({
        'a': np.random.randint(0, 100, n),
        'b': np.random.randint(0, 100, n),
        'category': np.random.choice(['A', 'B', 'C', 'D'], n)
    })
    
    print(f"\n数据集大小: {len(df)} 行")
    
    # 避免 apply，使用向量化操作
    import time
    
    print("\n【慢方法】使用 apply:")
    start = time.time()
    df['c_slow'] = df.apply(lambda row: row['a'] + row['b'], axis=1)
    slow_time = time.time() - start
    print(f"耗时: {slow_time:.4f} 秒")
    
    print("\n【快方法】使用向量化操作:")
    start = time.time()
    df['c_fast'] = df['a'] + df['b']
    fast_time = time.time() - start
    print(f"耗时: {fast_time:.4f} 秒")
    print(f"加速比: {slow_time / fast_time:.1f}x")
    
    # 使用 query 代替布尔索引
    print("\n【慢方法】布尔索引:")
    start = time.time()
    result1 = df[(df['a'] > 50) & (df['b'] > 50)]
    slow_time = time.time() - start
    print(f"耗时: {slow_time:.4f} 秒")
    
    print("\n【快方法】query:")
    start = time.time()
    result2 = df.query('a > 50 and b > 50')
    fast_time = time.time() - start
    print(f"耗时: {fast_time:.4f} 秒")
    print(f"加速比: {slow_time / fast_time:.1f}x")
    
    # 选择合适的数据类型
    print("\n【优化数据类型】")
    print(f"优化前内存使用: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    df['category'] = df['category'].astype('category')
    df['a'] = df['a'].astype('int32')
    df['b'] = df['b'].astype('int32')
    
    print(f"优化后内存使用: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")


def main():
    """主函数：运行所有演示"""
    print("\n" + "=" * 60)
    print("Pandas 基础操作演示")
    print("=" * 60)
    
    demo_dataframe_creation()
    demo_selection_filtering()
    demo_data_cleaning()
    demo_groupby()
    demo_pivot_table()
    demo_merge_join()
    demo_performance_tips()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
