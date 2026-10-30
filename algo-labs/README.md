# 算法与数据结构实验室（algo-labs）

> 大数据架构师面试的"手撕"能力核心。本模块覆盖 10 个专题，每题提供 **Java + Python 双解**，可直接编译运行。

## 设计目标

1. **可运行**：每份代码都有 main/测试入口，`javac` 或 `python3` 直接跑
2. **双语言**：同一道题两种实现，方便对比思维差异
3. **大数据特色**：第 10 专题专门讲布隆过滤器、HyperLogLog、TopK 堆、滑动窗口去重等生产常用结构
4. **面试导向**：每道题标注时间复杂度、常见追问、破坏练习

## 10 个专题

| # | 专题 | 核心内容 | 大数据关联 |
|---|------|---------|-----------|
| 01 | 数组与双指针 | Two Sum、盛水容器、有序数组去重 | 数据扫描、窗口计算 |
| 02 | 哈希表 | 两数之和、字母异位词、最长无重复子串 | 去重、分组、频率统计 |
| 03 | 链表 | 反转、合并、环检测、LRU 缓存 | LRU 是缓存核心 |
| 04 | 栈与队列 | 有效括号、最小栈、**单调栈**（每日温度） | 单调栈用于时序数据处理 |
| 05 | 二叉树 | 遍历（前中后层）、最大深度、对称、LCA | 树形依赖、执行计划 |
| 06 | 堆与 TopK | 第 K 大、合并 K 个链表、**数据流中位数** | TopK 是流处理核心 |
| 07 | 二分查找 | 标准模板、旋转数组、搜索区间 | 有序数据快速定位 |
| 08 | 图 | BFS/DFS、拓扑排序、并查集 | DAG 调度、依赖分析 |
| 09 | 动态规划 | 爬楼梯、背包、最长子序列、编辑距离 | 状态转移思维 |
| 10 | **大数据特色** | 布隆过滤器、HyperLogLog、RoaringBitmap、流式去重、CountMinSketch | **生产直接可用** |

## 学习方法

1. **读 README**：理解概念、看题解、记复杂度
2. **跑代码**：`javac Solution.java && java Solution` 或 `python3 solution.py`
3. **做破坏练习**：改输入边界、改算法参数、观察行为变化
4. **口述思路**：不看代码，能讲清"为什么这么做、时间复杂度多少、怎么优化"

## 文件结构

```
algo-labs/
├── README.md（本文件）
├── 01-array-two-pointers/
│   ├── README.md
│   ├── java/Solution.java
│   └── python/solution.py
├── 02-hash/
│   ├── README.md
│   ├── java/Solution.java
│   └── python/solution.py
...
└── 10-bigdata-special/
    ├── README.md
    ├── java/（4 个独立文件）
    └── python/（4 个独立文件）
```

## 运行环境

- Java 17+（与 llmops-labs 的 .venv 同目录）
- Python 3.11+（用 llmops-labs/.venv 即可）

## 相关模块

完成本模块后，可以继续学习：

- **[java-labs](../java-labs/)** - Java 进阶（集合/并发/JVM/函数式，深化语言基础）
- **[python-labs](../python-labs/)** - Python 进阶（基础/函数式/并发/数据处理）
- **[interview-prep](../interview-prep/)** - 面试准备（02-数仓、03-大数据引擎篇与本模块算法呼应）
- **[agent-labs](../agent-labs/)** - Agent 开发（将算法能力应用到智能体构建）
- **[english-labs](../english-labs/)** - 英语面试（用英语讲解本模块的算法题）
- **[career-portfolio](../career-portfolio/)** - 职业发展（将算法能力体现在简历和作品集中）
