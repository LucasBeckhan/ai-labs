"""
完整数据分析流程演示

本示例演示一个完整的数据分析项目流程：
1. 数据加载与探索
2. 数据清洗与预处理
3. 特征工程
4. 数据分析与可视化
5. 结果总结

使用模拟的销售数据集进行分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


def generate_sample_data():
    """生成模拟销售数据集"""
    np.random.seed(42)
    n_records = 1000
    
    # 生成日期范围
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_records)]
    
    # 生成产品类别
    categories = ['Electronics', 'Clothing', 'Food', 'Books', 'Sports']
    
    # 生成数据
    data = {
        'date': dates,
        'product_category': np.random.choice(categories, n_records),
        'sales_amount': np.random.normal(1000, 300, n_records),
        'quantity': np.random.randint(1, 20, n_records),
        'customer_age': np.random.randint(18, 70, n_records),
        'customer_gender': np.random.choice(['M', 'F'], n_records),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_records),
        'discount_applied': np.random.choice([True, False], n_records, p=[0.3, 0.7])
    }
    
    df = pd.DataFrame(data)
    
    # 添加一些缺失值和异常值
    df.loc[np.random.choice(df.index, 50), 'sales_amount'] = np.nan
    df.loc[np.random.choice(df.index, 30), 'customer_age'] = np.nan
    df.loc[np.random.choice(df.index, 5), 'sales_amount'] = 10000  # 异常值
    
    return df


def step1_data_loading_exploration(df):
    """步骤 1：数据加载与探索"""
    print("=" * 70)
    print("步骤 1：数据加载与探索")
    print("=" * 70)
    
    print("\n【数据概览】")
    print(f"数据集形状: {df.shape[0]} 行, {df.shape[1]} 列")
    
    print("\n【前 5 行数据】")
    print(df.head())
    
    print("\n【数据类型】")
    print(df.dtypes)
    
    print("\n【基本统计信息】")
    print(df.describe())
    
    print("\n【缺失值统计】")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({'缺失数量': missing, '缺失比例(%)': missing_pct})
    print(missing_df[missing_df['缺失数量'] > 0])
    
    print("\n【数据质量检查】")
    print(f"重复行数: {df.duplicated().sum()}")
    print(f"sales_amount 范围: {df['sales_amount'].min():.2f} - {df['sales_amount'].max():.2f}")
    print(f"customer_age 范围: {df['customer_age'].min()} - {df['customer_age'].max()}")
    
    return df


def step2_data_cleaning(df):
    """步骤 2：数据清洗与预处理"""
    print("\n" + "=" * 70)
    print("步骤 2：数据清洗与预处理")
    print("=" * 70)
    
    df_clean = df.copy()
    
    # 2.1 处理缺失值
    print("\n【2.1 处理缺失值】")
    
    # sales_amount: 用中位数填充（对异常值更稳健）
    median_sales = df_clean['sales_amount'].median()
    df_clean['sales_amount'] = df_clean['sales_amount'].fillna(median_sales)
    print(f"sales_amount 缺失值用中位数填充: {median_sales:.2f}")
    
    # customer_age: 用中位数填充
    median_age = df_clean['customer_age'].median()
    df_clean['customer_age'] = df_clean['customer_age'].fillna(median_age)
    print(f"customer_age 缺失值用中位数填充: {median_age:.0f}")
    
    # 验证缺失值已处理
    print(f"\n处理后缺失值: {df_clean.isnull().sum().sum()}")
    
    # 2.2 处理异常值
    print("\n【2.2 处理异常值】")
    
    # 使用 IQR 方法识别和处理 sales_amount 的异常值
    Q1 = df_clean['sales_amount'].quantile(0.25)
    Q3 = df_clean['sales_amount'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df_clean[(df_clean['sales_amount'] < lower_bound) | 
                        (df_clean['sales_amount'] > upper_bound)]
    print(f"检测到 {len(outliers)} 个异常值（IQR 方法）")
    print(f"  正常范围: [{lower_bound:.2f}, {upper_bound:.2f}]")
    
    # 将异常值限制在边界内
    df_clean['sales_amount'] = df_clean['sales_amount'].clip(lower_bound, upper_bound)
    print(f"异常值已限制在合理范围内")
    
    # 2.3 数据类型转换
    print("\n【2.3 数据类型转换】")
    
    # 将 date 列转换为 datetime 类型
    df_clean['date'] = pd.to_datetime(df_clean['date'])
    print(f"date 列已转换为 datetime 类型")
    
    # 将 category 列转换为 category 类型（节省内存）
    df_clean['product_category'] = df_clean['product_category'].astype('category')
    df_clean['region'] = df_clean['region'].astype('category')
    print(f"product_category 和 region 列已转换为 category 类型")
    
    print(f"\n内存使用: {df_clean.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    return df_clean


def step3_feature_engineering(df):
    """步骤 3：特征工程"""
    print("\n" + "=" * 70)
    print("步骤 3：特征工程")
    print("=" * 70)
    
    df_features = df.copy()
    
    # 3.1 时间特征
    print("\n【3.1 时间特征】")
    df_features['year'] = df_features['date'].dt.year
    df_features['month'] = df_features['date'].dt.month
    df_features['day_of_week'] = df_features['date'].dt.dayofweek
    df_features['quarter'] = df_features['date'].dt.quarter
    df_features['is_weekend'] = df_features['day_of_week'].isin([5, 6])
    print("创建的时间特征: year, month, day_of_week, quarter, is_weekend")
    
    # 3.2 计算衍生特征
    print("\n【3.2 计算衍生特征】")
    df_features['avg_price'] = df_features['sales_amount'] / df_features['quantity']
    df_features['age_group'] = pd.cut(
        df_features['customer_age'],
        bins=[0, 25, 35, 50, 100],
        labels=['Young', 'Young-Adult', 'Middle-Age', 'Senior']
    )
    print("创建的衍生特征: avg_price, age_group")
    
    # 3.3 编码分类变量
    print("\n【3.3 编码分类变量】")
    # One-hot encoding for gender
    df_features = pd.get_dummies(df_features, columns=['customer_gender'], prefix='gender')
    print("customer_gender 已进行 one-hot 编码")
    
    print(f"\n特征工程后数据集形状: {df_features.shape}")
    print(f"新增特征数: {df_features.shape[1] - df.shape[1]}")
    
    return df_features


def step4_analysis_visualization(df):
    """步骤 4：数据分析与可视化"""
    print("\n" + "=" * 70)
    print("步骤 4：数据分析与可视化")
    print("=" * 70)
    
    # 4.1 销售趋势分析
    print("\n【4.1 销售趋势分析】")
    
    # 按月聚合销售额
    monthly_sales = df.groupby(df['date'].dt.to_period('M'))['sales_amount'].sum()
    print("月度销售额趋势:")
    print(monthly_sales.head())
    
    # 可视化（如果 matplotlib 可用）
    try:
        plt.figure(figsize=(12, 6))
        monthly_sales.plot(kind='line', marker='o')
        plt.title('Monthly Sales Trend')
        plt.xlabel('Month')
        plt.ylabel('Sales Amount')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('/tmp/monthly_sales_trend.png', dpi=100)
        print("图表已保存到: /tmp/monthly_sales_trend.png")
        plt.close()
    except Exception as e:
        print(f"可视化跳过（matplotlib 不可用）: {e}")
    
    # 4.2 产品类别分析
    print("\n【4.2 产品类别分析】")
    category_stats = df.groupby('product_category').agg({
        'sales_amount': ['sum', 'mean', 'count'],
        'quantity': 'sum'
    }).round(2)
    category_stats.columns = ['总销售额', '平均销售额', '订单数', '总数量']
    category_stats = category_stats.sort_values('总销售额', ascending=False)
    print(category_stats)
    
    # 4.3 客户分析
    print("\n【4.3 客户分析】")
    
    # 年龄分布
    age_stats = df.groupby('age_group')['sales_amount'].agg(['count', 'mean', 'sum']).round(2)
    age_stats.columns = ['订单数', '平均销售额', '总销售额']
    print("\n按年龄组的销售情况:")
    print(age_stats)
    
    # 性别分析
    gender_sales = df.groupby('customer_gender')['sales_amount'].agg(['count', 'mean']).round(2)
    gender_sales.columns = ['订单数', '平均销售额']
    print("\n按性别的销售情况:")
    print(gender_sales)
    
    # 4.4 地区分析
    print("\n【4.4 地区分析】")
    region_stats = df.groupby('region')['sales_amount'].agg(['sum', 'mean', 'count']).round(2)
    region_stats.columns = ['总销售额', '平均销售额', '订单数']
    region_stats = region_stats.sort_values('总销售额', ascending=False)
    print(region_stats)
    
    # 4.5 折扣效果分析
    print("\n【4.5 折扣效果分析】")
    discount_effect = df.groupby('discount_applied')['sales_amount'].agg(['count', 'mean', 'sum']).round(2)
    discount_effect.columns = ['订单数', '平均销售额', '总销售额']
    discount_effect.index = ['无折扣', '有折扣']
    print(discount_effect)
    
    # 4.6 相关性分析
    print("\n【4.6 相关性分析】")
    numeric_cols = ['sales_amount', 'quantity', 'customer_age', 'avg_price']
    correlation = df[numeric_cols].corr().round(3)
    print("数值特征相关性矩阵:")
    print(correlation)
    
    return df


def step5_summary(df):
    """步骤 5：结果总结"""
    print("\n" + "=" * 70)
    print("步骤 5：结果总结")
    print("=" * 70)
    
    print("\n【关键发现】")
    
    # 1. 销售概况
    total_sales = df['sales_amount'].sum()
    avg_sales = df['sales_amount'].mean()
    total_orders = len(df)
    
    print(f"\n1. 销售概况")
    print(f"   - 总销售额: ${total_sales:,.2f}")
    print(f"   - 平均订单金额: ${avg_sales:,.2f}")
    print(f"   - 总订单数: {total_orders}")
    
    # 2. 最佳产品类别
    top_category = df.groupby('product_category')['sales_amount'].sum().idxmax()
    top_category_sales = df.groupby('product_category')['sales_amount'].sum().max()
    
    print(f"\n2. 最佳产品类别")
    print(f"   - {top_category}: ${top_category_sales:,.2f}")
    
    # 3. 最佳地区
    top_region = df.groupby('region')['sales_amount'].sum().idxmax()
    top_region_sales = df.groupby('region')['sales_amount'].sum().max()
    
    print(f"\n3. 最佳销售地区")
    print(f"   - {top_region}: ${top_region_sales:,.2f}")
    
    # 4. 折扣效果
    discount_effect = df.groupby('discount_applied')['sales_amount'].mean()
    discount_lift = ((discount_effect[True] - discount_effect[False]) / discount_effect[False] * 100)
    
    print(f"\n4. 折扣效果")
    print(f"   - 有折扣平均销售额: ${discount_effect[True]:,.2f}")
    print(f"   - 无折扣平均销售额: ${discount_effect[False]:,.2f}")
    print(f"   - 折扣提升效果: {discount_lift:.1f}%")
    
    # 5. 客户画像
    avg_age = df['customer_age'].mean()
    top_age_group = df.groupby('age_group')['sales_amount'].sum().idxmax()
    
    print(f"\n5. 客户画像")
    print(f"   - 平均年龄: {avg_age:.1f} 岁")
    print(f"   - 最高消费年龄组: {top_age_group}")
    
    print("\n【建议】")
    print("1. 重点关注 {} 类别的产品，贡献了最高销售额".format(top_category))
    print("2. 加大 {} 地区的营销投入".format(top_region))
    print("3. 折扣策略有效，可考虑扩大使用范围" if discount_lift > 0 else "3. 折扣策略效果不明显，需重新评估")
    print("4. 针对 {} 年龄段客户制定精准营销策略".format(top_age_group))
    print("5. 周末销售可能较高，可考虑周末促销活动")


def main():
    """主函数：执行完整的数据分析流程"""
    print("\n" + "=" * 70)
    print("完整数据分析流程演示")
    print("=" * 70)
    print("\n本示例演示一个完整的数据分析项目流程：")
    print("1. 数据加载与探索")
    print("2. 数据清洗与预处理")
    print("3. 特征工程")
    print("4. 数据分析与可视化")
    print("5. 结果总结")
    
    # 生成模拟数据
    print("\n【生成模拟销售数据】")
    df = generate_sample_data()
    print(f"已生成 {len(df)} 条销售记录")
    
    # 执行分析流程
    df = step1_data_loading_exploration(df)
    df = step2_data_cleaning(df)
    df = step3_feature_engineering(df)
    df = step4_analysis_visualization(df)
    step5_summary(df)
    
    print("\n" + "=" * 70)
    print("分析完成！")
    print("=" * 70)
    print("\n完整的数据分析流程已演示完毕。")
    print("在实际项目中，可以根据具体需求调整每个步骤的细节。")


if __name__ == "__main__":
    main()
