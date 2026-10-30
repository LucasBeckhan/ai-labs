-- ============================================================
-- 手撕 SQL 题库 · 全量验证脚本（14 题，D1–D14）
-- 运行：docker exec -i llmops-mysql mysql -uroot -proot_lab_only < 08-SQL题库验证.sql
-- 可重复执行（每次重建 sql_drill 库）。讲解与追问见 08-手撕SQL题库.md
-- ============================================================
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS sql_drill;
CREATE DATABASE sql_drill CHARACTER SET utf8mb4;
USE sql_drill;

-- ================= 公共数据集 =================
CREATE TABLE emp (
  id INT PRIMARY KEY,
  name VARCHAR(32),
  dept VARCHAR(16),
  salary INT
);
INSERT INTO emp VALUES
 (1,'张三','技术',25000),(2,'李四','技术',22000),(3,'王五','技术',22000),(4,'赵六','技术',18000),
 (5,'钱七','销售',15000),(6,'孙八','销售',12000),(7,'周九','销售',12000),
 (8,'吴十','人事',10000),(9,'郑一','人事',9000);

CREATE TABLE orders (
  order_id INT PRIMARY KEY,
  user_id  VARCHAR(8),
  amount   INT,
  dt       DATE
);
INSERT INTO orders VALUES
 (101,'u01',100,'2026-10-23'),(102,'u01',200,'2026-10-24'),
 (103,'u02',150,'2026-10-24'),(104,'u01',300,'2026-10-25'),
 (105,'u03', 50,'2026-10-25'),(106,'u02',250,'2026-10-26');

CREATE TABLE score (
  name    VARCHAR(16),
  subject VARCHAR(16),
  score   INT
);
INSERT INTO score VALUES
 ('张三','语文',90),('张三','数学',85),('张三','英语',95),
 ('李四','语文',88),('李四','数学',92),('李四','英语',78);

CREATE TABLE monthly_sales (ym CHAR(7), amount INT);
INSERT INTO monthly_sales VALUES
 ('2025-01',100),('2025-02',120),('2025-03',90),
 ('2026-01',180),('2026-02',150),('2026-03',210);

CREATE TABLE daily_sales (dt DATE, amount INT);
INSERT INTO daily_sales VALUES
 ('2026-10-23',10),('2026-10-24',20),('2026-10-25',30),('2026-10-26',40);

CREATE TABLE orders_dup (
  order_id INT, user_id VARCHAR(8), amount INT, updated_at DATETIME
);
INSERT INTO orders_dup VALUES
 (1,'u01',100,'2026-10-23 10:00:00'),(1,'u01',120,'2026-10-24 11:00:00'),
 (2,'u02', 80,'2026-10-23 09:00:00'),(3,'u01', 90,'2026-10-25 12:00:00');

CREATE TABLE user_buy (user_id VARCHAR(8), item VARCHAR(8));
INSERT INTO user_buy VALUES ('u01','A'),('u01','B'),('u02','A'),('u03','C');

CREATE TABLE visit_log (user_id VARCHAR(8), dt DATE);
INSERT INTO visit_log VALUES
 ('u01','2026-10-23'),('u01','2026-10-24'),('u01','2026-10-25'),('u01','2026-10-26'),('u01','2026-10-27'),
 ('u02','2026-10-23'),('u02','2026-10-25'),
 ('u03','2026-10-24'),('u03','2026-10-25'),('u03','2026-10-26');

-- ================= D1 每部门工资前三（并列处理） =================
SELECT dept, name, salary, rk
FROM (
  SELECT dept, name, salary,
         DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk
  FROM emp) t
WHERE rk <= 3;

SELECT IF(COUNT(*)=9, 'PASS D1: dense_rank 含并列，三部门共9行', 'FAIL D1') AS d1
FROM (SELECT dept, name,
      DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk FROM emp) t
WHERE rk <= 3;

-- ================= D2 每个用户最近一次订单 =================
SELECT user_id, order_id, amount, dt FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt DESC, order_id DESC) AS rn
  FROM orders) t WHERE rn = 1 ORDER BY user_id;

SELECT IF(COUNT(*)=3, 'PASS D2: 每用户最近一单共3人', 'FAIL D2') AS d2
FROM (SELECT user_id,
      ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt DESC, order_id DESC) AS rn
      FROM orders) t WHERE rn = 1;

-- ================= D3 行转列（成绩透视） =================
SELECT name,
       MAX(CASE WHEN subject='语文' THEN score END) AS `语文`,
       MAX(CASE WHEN subject='数学' THEN score END) AS `数学`,
       MAX(CASE WHEN subject='英语' THEN score END) AS `英语`,
       SUM(score) AS total
FROM score GROUP BY name;

SELECT IF(COUNT(*)=2 AND SUM(`数学`=85 AND `语文`=90)=1 AND SUM(`数学`=92)=1, 'PASS D3: 透视2人且分数正确', 'FAIL D3') AS d3
FROM (SELECT name,
        MAX(CASE WHEN subject='语文' THEN score END) AS `语文`,
        MAX(CASE WHEN subject='数学' THEN score END) AS `数学`,
        MAX(CASE WHEN subject='英语' THEN score END) AS `英语`
      FROM score GROUP BY name) t;

-- ================= D4 列转行（UNION ALL 还原，与 D3 互逆） =================
CREATE TABLE score_pivot_tmp AS  -- 注意：临时表在同一查询里不能引用两次(MySQL限制)，演示用真实表
SELECT name,
  MAX(CASE WHEN subject='语文' THEN score END) AS `语文`,
  MAX(CASE WHEN subject='数学' THEN score END) AS `数学`,
  MAX(CASE WHEN subject='英语' THEN score END) AS `英语`
FROM score GROUP BY name;

SELECT name, '语文' AS subject, `语文` AS score FROM score_pivot_tmp
UNION ALL SELECT name, '数学', `数学` FROM score_pivot_tmp
UNION ALL SELECT name, '英语', `英语` FROM score_pivot_tmp;

SELECT IF(COUNT(*)=6, 'PASS D4: 列转行还原6条', 'FAIL D4') AS d4
FROM (
 SELECT name, '语文' AS subject, `语文` AS score FROM score_pivot_tmp
 UNION ALL SELECT name, '数学', `数学` FROM score_pivot_tmp
 UNION ALL SELECT name, '英语', `英语` FROM score_pivot_tmp) t;

-- ================= D5 环比与同比（LAG） =================
SELECT ym, amount,
       LAG(amount) OVER (ORDER BY ym)                                AS prev_month,
       LAG(amount, 12) OVER (ORDER BY ym)                            AS same_month_last_year,
       ROUND((amount - LAG(amount) OVER (ORDER BY ym)) / LAG(amount) OVER (ORDER BY ym) * 100, 1) AS mom_pct
FROM monthly_sales ORDER BY ym;

SELECT IF(SUM(ym='2026-01' AND mom_pct=100.0)=1, 'PASS D5: 2026-01 环比 +100%', 'FAIL D5') AS d5
FROM (SELECT ym, amount,
        ROUND((amount - LAG(amount) OVER (ORDER BY ym)) / LAG(amount) OVER (ORDER BY ym) * 100, 1) AS mom_pct
      FROM monthly_sales) t;

-- ================= D6 累计求和（SUM OVER） =================
SELECT dt, amount, SUM(amount) OVER (ORDER BY dt) AS cum_amount FROM daily_sales ORDER BY dt;

SELECT IF(SUM(cum_amount=60 AND dt='2026-10-25')=1 AND SUM(cum_amount=100 AND dt='2026-10-26')=1,
          'PASS D6: 累计值正确', 'FAIL D6') AS d6
FROM (SELECT dt, amount, SUM(amount) OVER (ORDER BY dt) AS cum_amount FROM daily_sales) t;

-- ================= D7 金额区间分布（CASE 分桶） =================
SELECT CASE WHEN amount < 100 THEN '0-99'
            WHEN amount < 200 THEN '100-199'
            WHEN amount < 300 THEN '200-299'
            ELSE '300+' END AS bucket,
       COUNT(*) AS cnt
FROM orders GROUP BY 1 ORDER BY 1;

SELECT IF(SUM(bucket='0-99' AND cnt=1)=1 AND SUM(bucket='300+' AND cnt=1)=1,
          'PASS D7: 区间分布正确', 'FAIL D7') AS d7
FROM (SELECT CASE WHEN amount < 100 THEN '0-99'
            WHEN amount < 200 THEN '100-199'
            WHEN amount < 300 THEN '200-299'
            ELSE '300+' END AS bucket, COUNT(*) AS cnt
      FROM orders GROUP BY 1) t;

-- ================= D8 重复数据保留最新一条 =================
SELECT order_id, user_id, amount, updated_at FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
  FROM orders_dup) t WHERE rn = 1 ORDER BY order_id;
-- 真实删除（如面试追问）：DELETE t FROM orders_dup t
-- JOIN (SELECT order_id, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) rn FROM orders_dup) x
--   ON t.order_id = x.order_id AND x.rn > 1;

SELECT IF(COUNT(*)=3, 'PASS D8: 去重保留最新3条', 'FAIL D8') AS d8
FROM (SELECT order_id, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
      FROM orders_dup) t WHERE rn = 1;

-- ================= D9 中位数（奇偶通吃） =================
SELECT AVG(salary) AS median
FROM (
  SELECT salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn, COUNT(*) OVER () AS n FROM emp) t
WHERE rn IN (FLOOR((n+1)/2), CEIL((n+1)/2));

SELECT IF(ABS((SELECT median FROM (
  SELECT AVG(salary) AS median FROM (
    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn, COUNT(*) OVER () AS n FROM emp) t
  WHERE rn IN (FLOOR((n+1)/2), CEIL((n+1)/2))) m) - 15000) < 0.01, 'PASS D9: 9人中位数=15000', 'FAIL D9') AS d9;

-- ================= D10 购买了 A 但未购买 B 的用户 =================
SELECT DISTINCT a.user_id
FROM user_buy a
LEFT JOIN user_buy b ON a.user_id = b.user_id AND b.item = 'B'
WHERE a.item = 'A' AND b.user_id IS NULL;

SELECT IF(COUNT(*)=1, 'PASS D10: 买A未买B仅u02', 'FAIL D10') AS d10
FROM (SELECT DISTINCT a.user_id FROM user_buy a
      LEFT JOIN user_buy b ON a.user_id = b.user_id AND b.item = 'B'
      WHERE a.item = 'A' AND b.user_id IS NULL) t;

-- ================= D11 分组拼接（GROUP_CONCAT） =================
SELECT dept, GROUP_CONCAT(name ORDER BY salary DESC SEPARATOR '、') AS members,
       COUNT(*) AS headcount, MAX(salary) AS max_salary
FROM emp GROUP BY dept;

SELECT IF(SUM(dept='技术' AND headcount=4)=1, 'PASS D11: 分组聚合+拼接', 'FAIL D11') AS d11
FROM (SELECT dept, GROUP_CONCAT(name ORDER BY salary DESC SEPARATOR '、') AS members,
        COUNT(*) AS headcount, MAX(salary) AS max_salary FROM emp GROUP BY dept) t;

-- ================= D12 首末登录间隔与活跃天数 =================
SELECT user_id,
       MIN(dt) AS first_dt, MAX(dt) AS last_dt,
       DATEDIFF(MAX(dt), MIN(dt)) AS span_days,
       COUNT(DISTINCT dt) AS active_days
FROM visit_log GROUP BY user_id;

SELECT IF(SUM(user_id='u01' AND span_days=4 AND active_days=5)=1, 'PASS D12: u01 跨度4天活跃5天', 'FAIL D12') AS d12
FROM (SELECT user_id, MIN(dt) AS first_dt, MAX(dt) AS last_dt,
        DATEDIFF(MAX(dt), MIN(dt)) AS span_days, COUNT(DISTINCT dt) AS active_days
      FROM visit_log GROUP BY user_id) t;

-- ================= D13 连续 N 天（打标法，引用 03 实验思路换数据复验） =================
SELECT user_id, MIN(dt) AS streak_start, MAX(dt) AS streak_end, COUNT(*) AS days
FROM (
  SELECT user_id, dt,
         DATE_SUB(dt, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) DAY) AS grp
  FROM (SELECT DISTINCT user_id, dt FROM visit_log) a) t
GROUP BY user_id, grp HAVING COUNT(*) >= 3;

SELECT IF(COUNT(*)=2, 'PASS D13: 连续>=3天的段共2段', 'FAIL D13') AS d13
FROM (
 SELECT user_id, grp, COUNT(*) AS days FROM (
  SELECT user_id, dt,
         DATE_SUB(dt, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) DAY) AS grp
  FROM (SELECT DISTINCT user_id, dt FROM visit_log) a) t
 GROUP BY user_id, grp HAVING COUNT(*) >= 3) t;

-- ================= D14 NULL 语义陷阱（高频扣分题） =================
SELECT IF(COUNT(*)=0, 'PASS D14.1: NULL<>任何值恒不成立', 'FAIL D14.1') AS d14_1
FROM emp WHERE salary <> NULL;

SELECT IF(COUNT(*)=9, 'PASS D14.2: IS NULL/IS NOT NULL 才是正解(此处全部非空)', 'FAIL D14.2') AS d14_2
FROM emp WHERE salary IS NOT NULL;

-- NOT IN 遇到 NULL 的经典陷阱：子查询含 NULL 时 NOT IN 永远为空
CREATE TEMPORARY TABLE t_black (dept VARCHAR(16));
INSERT INTO t_black VALUES ('人事'), (NULL);
SELECT IF(COUNT(*)=0, 'PASS D14.3: NOT IN 含 NULL 时结果为空(经典陷阱)', 'FAIL D14.3') AS d14_3
FROM emp WHERE dept NOT IN (SELECT dept FROM t_black);
-- 正解：NOT IN (SELECT dept FROM t_black WHERE dept IS NOT NULL) 或 NOT EXISTS
SELECT IF(COUNT(*)=7, 'PASS D14.4: NOT EXISTS 正确排除人事7人', 'FAIL D14.4') AS d14_4
FROM emp e WHERE NOT EXISTS (SELECT 1 FROM t_black b WHERE b.dept = e.dept);
