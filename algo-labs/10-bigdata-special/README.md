# 专题 10：大数据特色数据结构

> 这是大数据架构师面试的**差异化考点**——普通算法题库不覆盖，但生产环境天天用。

## 为什么重要

大数据场景的数据量级（亿级、TB 级）决定了：
- 精确算法（HashSet 去重、HashMap 计数）内存扛不住
- 需要**近似算法**：用少量内存（KB~MB 级）换可接受的误差（1%~5%）

## 四个核心数据结构

---

### 1. 布隆过滤器（Bloom Filter）

**用途**：快速判断元素"可能存在"或"一定不存在"。
- **假阳性**：说存在，实际可能不存在（概率可控）
- **无假阴性**：说不存在，一定不存在

**原理**：
- 一个 bit 数组（初始全 0）+ k 个哈希函数
- 插入元素：用 k 个哈希函数计算 k 个位置，全部置 1
- 查询元素：检查 k 个位置是否全为 1（有一个 0 就一定不存在）

**参数选择**：
- 误判率 p、元素数量 n → 最优 bit 数 m = -n·ln(p)/(ln2)²
- 最优哈希函数数 k = (m/n)·ln2

**应用场景**：
- 缓存穿透防护（先查布隆，不命中就不查 DB）
- 爬虫去重（URL 是否已爬）
- 邮件黑名单（快速判断是否在黑名单）

---

### 2. HyperLogLog

**用途**：基数估计（去重计数），如"有多少个独立用户访问"。
- 误差约 1.04/√m（m 是寄存器数，通常 1024~65536）
- 内存固定（几 KB），不管数据量多大

**原理**（简化版）：
- 把元素哈希成二进制串
- 观察前导零的个数（如 `0001...` 有 3 个前导零）
- 前导零越多，说明元素越"稀有"，基数越大
- 用调和平均数估计基数：2^(最大前导零数) × 校正系数

**应用场景**：
- UV 统计（独立访客数）
- 数据库 COUNT(DISTINCT) 的近似版（Redis、BigQuery 都内置）

---

### 3. CountMinSketch

**用途**：频率估计（元素出现次数的近似值）。
- 高估不低估（overestimate）
- 误差与总流量成正比

**原理**：
- d 行 w 列的二维数组（d 个哈希函数，每个哈希到 [0, w)）
- 插入元素：d 个哈希函数计算 d 个位置，对应位置 +1
- 查询频率：取 d 个位置的最小值（最小化碰撞影响）

**参数选择**：
- 误差 ε、失败概率 δ → w = ⌈e/ε⌉, d = ⌈ln(1/δ)⌉

**应用场景**：
- 流式数据的 TopK（配合堆）
- 网络流量监控（哪个 IP 访问最多）
- 词频统计（近似版）

---

### 4. 滑动窗口去重

**用途**：流式数据中，只保留最近 N 个元素内的去重。

**原理**：
- 用队列维护窗口内的元素
- 用 HashSet 快速判断重复
- 窗口滑动时，队列头部出队，同时从 HashSet 删除

**复杂度**：插入 O(1)，查询 O(1)，空间 O(N)

**应用场景**：
- 实时日志去重（最近 1 小时内的日志）
- 滑动窗口聚合（最近 5 分钟的独立用户数）

---

## 代码实现

Java 和 Python 代码见对应目录，每个数据结构独立文件，均含 main 函数可直接运行。

**运行方式**：
```bash
cd 10-bigdata-special
javac java/*.java && java -cp java BloomFilterDemo
java -cp java HyperLogLogDemo
java -cp java CountMinSketchDemo
java -cp java SlidingWindowDedupDemo
# 或
python3 python/bloom_filter.py
python3 python/hyperloglog.py
python3 python/count_min_sketch.py
python3 python/sliding_window_dedup.py
```

## 面试怎么讲

**不要背定义，要讲场景**：
- "布隆过滤器用在缓存穿透防护，先查布隆再查 DB，布隆说不存在就一定不存在，避免了无效查询"
- "HyperLogLog 用来算 UV，1 亿用户用 HashSet 要几 GB 内存，用 HyperLogLog 只要几 KB，误差 1% 业务可接受"
- "CountMinSketch 用在流式 TopK，配合最小堆，实时统计高频元素"

**关键数字要记住**：
- 布隆过滤器：1% 误判率，10 万元素约需 120 KB
- HyperLogLog：1024 个寄存器，误差 3.25%；16384 个寄存器，误差 0.81%
- CountMinSketch：误差 ε=0.01，需要 w=272, d=5（约 5 KB）

## 与数仓的联系

这些数据结构在数仓中的应用：
- **布隆过滤器**：ORC/Parquet 文件的 min/max 索引本质是简化版布隆
- **HyperLogLog**：Spark SQL 的 `approx_count_distinct` 函数
- **CountMinSketch**：Flink 的近似计数
- **滑动窗口**：Flink 的滑动窗口聚合

数据工程师做 Agent（interview-prep/06 篇）时，这些结构可以作为工具暴露给模型（如"用 HyperLogLog 估算 UV"）。
