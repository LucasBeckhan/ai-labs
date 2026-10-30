# 08 — 手撕 SQL 题库 14 题（全部在样例 MySQL 上跑通验证）

> 运行方式（17 条断言全部 PASS，可随时重跑）：
> ```bash
> docker exec -i llmops-mysql mysql -uroot -proot_lab_only \
>   < ~/Documents/ai-labs/interview-prep/sql-drill/08-SQL题库验证.sql
> ```
> 手撕 SQL 的评分点不是"写出来"，而是：① **写对边界**（并列/NULL/去重）；② **说得出执行代价**（哪个字段要索引、哪一步会 shuffle）；③ **能应付追问变体**。每题的【追问变体】就是二面的真实下钻方向。

## D1 每部门工资前三（并列处理）★必考

```sql
SELECT dept, name, salary, rk
FROM (SELECT dept, name, salary,
             DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk
      FROM emp) t
WHERE rk <= 3;
```
- **核心考点**：`ROW_NUMBER`（强行唯一）vs `RANK`（并列跳号：1,2,2,4）vs `DENSE_RANK`（并列不跳号：1,2,2,3）——题目说"工资前三的人"该用哪个？**并列都要 → DENSE_RANK**。实测技术部 4 人全进（25k、22k、22k、18k 是前三档）。
- 【追问变体】"只要 3 个人"呢？（换 ROW_NUMBER 或先取 DENSE_RANK 档位再取前 3 档）→ "工资前 3 高的金额"呢？（`SELECT DISTINCT salary ... ORDER BY salary DESC LIMIT 3`，根本不用窗口）

## D2 每个用户最近一次订单

```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt DESC, order_id DESC) AS rn
  FROM orders) t WHERE rn = 1;
```
- **核心考点**：排序键加 `order_id DESC` 兜底同日多单的确定性。
- 【追问变体】亿级表怎么优化？（先 `GROUP BY user_id` 取 `MAX(dt)` 再 join 回明细——两步降低窗口排序规模；或按 user 分桶预聚合）→ 不用窗口怎么写？（相关子查询 `WHERE dt = (SELECT MAX(dt)...)`，讲清两者执行计划差异）

## D3/D4 行转列与列转行（互逆）★必考

```sql
-- 行转列
SELECT name,
  MAX(CASE WHEN subject='语文' THEN score END) AS `语文`,
  MAX(CASE WHEN subject='数学' THEN score END) AS `数学`
FROM score GROUP BY name;
-- 列转行（还原）
SELECT name,'语文' AS subject,`语文` AS score FROM score_pivot
UNION ALL SELECT name,'数学',`数学` FROM score_pivot
UNION ALL SELECT name,'英语',`英语` FROM score_pivot;
```
- **核心考点**：CASE WHEN + 聚合的透视套路；**MySQL 限制**：临时表在同一条查询里不能引用两次（实测报 `Can't reopen table`，改真实表）。
- 【追问变体】列很多怎么办？（动态 SQL 拼 CASE WHEN，或用 JSON 函数；Hive 里 `map` 类型/`stack` 函数）→ 为什么用 MAX 而不是 SUM？（每人每科只有一行，MAX/SUM 等价；重复行时语义不同——先想清楚粒度）

## D5 环比与同比（LAG）

```sql
SELECT ym, amount,
       LAG(amount) OVER (ORDER BY ym) AS prev_month,
       ROUND((amount - LAG(amount) OVER (ORDER BY ym)) / LAG(amount) OVER (ORDER BY ym) * 100, 1) AS mom_pct
FROM monthly_sales;
```
- **核心考点**：LAG(col, N) 的 N 期偏移——**同比 = LAG(amount, 12) 前提是数据连续无缺月**，缺月要用自关联日历表。实测 2026-01 环比 +100%（180 vs 上月 90）。
- 【追问变体】除零/NULL 怎么处理？（NULLIF + COALESCE）→ 环比跨年对不齐？（生成连续月历表 LEFT JOIN 事实表，这是数仓标准做法）

## D6 累计求和

```sql
SELECT dt, amount, SUM(amount) OVER (ORDER BY dt) AS cum_amount FROM daily_sales;
```
- 【追问变体】按分组的累计？（`OVER (PARTITION BY ... ORDER BY dt)`）→ 要"本月累计"每月重置？（PARTITION BY 月份）

## D7 金额区间分布

```sql
SELECT CASE WHEN amount < 100 THEN '0-99'
            WHEN amount < 200 THEN '100-199'
            WHEN amount < 300 THEN '200-299'
            ELSE '300+' END AS bucket, COUNT(*) AS cnt
FROM orders GROUP BY 1;
```
- **核心考点**：CASE 分桶**边界方向要一致**（全左闭右开），写混了会出现 100 同时落两桶或两不落。
- 【追问变体】区间要可配置？（维度表存区间 + JOIN ON `amount BETWEEN low AND high`，或非等值 join 注意性能）

## D8 重复数据去重保留最新一条 ★必考

```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
  FROM orders_dup) t WHERE rn = 1;
-- 真删：
DELETE t FROM orders_dup t
JOIN (SELECT order_id, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) rn
      FROM orders_dup) x ON t.order_id = x.order_id AND x.rn > 1;
```
- **核心考点**：这题的现实形态是"上游重复推送"——数仓 DWD 去重的原型（llmops-labs Lab 03 的 `lab-数仓小实验/02` 就是它的数仓版）。
- 【追问变体】MySQL 5.7 不支持窗口怎么办？（自关联：`t.updated_at < (SELECT MAX(updated_at) ...)` 或 join 计数法）→ 怎么防再产生？（上游幂等键 + 唯一索引兜底）

## D9 中位数（奇偶通吃）

```sql
SELECT AVG(salary) AS median
FROM (SELECT salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn, COUNT(*) OVER () AS n FROM emp) t
WHERE rn IN (FLOOR((n+1)/2), CEIL((n+1)/2));
```
- **核心考点**：9 人的中位数 = 第 5 名（15000）；`rn IN (FLOOR/CEIL)` 同时覆盖奇偶。**为什么不用 AVG(两边)**：偶数时恰取两数平均，奇数时两数相同——写一次通吃。
- 【追问变体】按部门求中位数？（窗口加 PARTITION BY dept）→ 为什么 MySQL 没有内置 median？（严格聚合语义，UDF/窗口组合实现）

## D10 集合差：买了 A 没买 B

```sql
SELECT DISTINCT a.user_id
FROM user_buy a
LEFT JOIN user_buy b ON a.user_id = b.user_id AND b.item = 'B'
WHERE a.item = 'A' AND b.user_id IS NULL;
```
- **核心考点**：差集的正确姿势是 LEFT JOIN + IS NULL（或 NOT EXISTS），**不是 NOT IN**——和 D14 呼应。
- 【追问变体】"买了 A 或 B 但没都买"？（互斥集：分组计数=1）→ 亿级用户两个集合怎么做？（位图/位图或 bloom 预过滤）

## D11 分组拼接 GROUP_CONCAT

```sql
SELECT dept, GROUP_CONCAT(name ORDER BY salary DESC SEPARATOR '、') AS members,
       COUNT(*) AS headcount, MAX(salary) AS max_salary
FROM emp GROUP BY dept;
```
- 【追问变体】GROUP_CONCAT 默认 1024 字符截断！（`group_concat_max_len` 调大——这是真实生产事故来源）→ Hive 里对应什么？（`collect_list/collect_set` + `concat_ws`）

## D12 首末登录间隔与活跃天数

```sql
SELECT user_id, MIN(dt) AS first_dt, MAX(dt) AS last_dt,
       DATEDIFF(MAX(dt), MIN(dt)) AS span_days,
       COUNT(DISTINCT dt) AS active_days
FROM visit_log GROUP BY user_id;
```
- **核心考点**：`span_days`（自然日跨度）≠ `active_days`（真实活跃数）——u01 跨度 4 天但活跃 5 天？不可能——**这两个数能帮你自查数据错误**（活跃数 > 跨度+1 必有脏数据）。

## D13 连续 N 天（打标法复验）

与 `lab-数仓小实验/03` 同源，换个数据集再验一遍：连续 ≥3 天的段共 2 段（u01 的 5 天段、u03 的 3 天段）。**追问方向**：按月统计 / 增量维护 / 大用户倾斜（见 03 篇 Q3）。

## D14 NULL 语义陷阱（最容易白丢分的题）★必考

```sql
SELECT COUNT(*) FROM emp WHERE salary <> NULL;        -- 0 行！NULL 与任何比较都为 UNKNOWN
SELECT COUNT(*) FROM emp WHERE salary IS NOT NULL;    -- 正解
SELECT COUNT(*) FROM emp WHERE dept NOT IN (SELECT dept FROM t_black);  -- t_black 含 NULL 时 → 0 行！
SELECT COUNT(*) FROM emp e WHERE NOT EXISTS (SELECT 1 FROM t_black b WHERE b.dept = e.dept);  -- 正解 7 行
```
- **核心考点**：三值逻辑（TRUE/FALSE/**UNKNOWN**）。`NOT IN` 的子查询只要含一个 NULL，整个 NOT IN 永远空——这是 SQL 面试最著名的陷阱题。**生产映射**：维表/黑名单表的主键列必须 NOT NULL，或代码里先过滤。
- 【追问变体】COUNT(col) 和 COUNT(*) 区别？（前者跳过 NULL）→ SUM 全 NULL 返回什么？（NULL 不是 0——报表里要 COALESCE）

## 评分与练习建议

1. 每题**先说思路再写**（面试官要看的是思考过程，闷头写完直接报答案反而扣分）
2. 写完必做三件事：**边界自查**（并列/NULL/重复）、**说执行代价**（哪步 shuffle/要不要索引）、**给变体**（主动说"如果要求变成 X 我会改成 Y"）
3. 全部 14 题建议脱稿重写两遍——第一遍对着答案，第二遍只看题目
