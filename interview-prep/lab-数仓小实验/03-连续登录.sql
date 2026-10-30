-- ============================================================
-- 实验三：连续 N 天登录（row_number 打标法）—— 手撕 SQL 高频题
-- 对应面试题：02-数仓建模.md Q21
-- 运行方式：
--   docker exec -i llmops-mysql mysql -uroot -proot_lab_only < 03-连续登录.sql
-- ============================================================
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS dw_lab3;
CREATE DATABASE dw_lab3 CHARACTER SET utf8mb4;
USE dw_lab3;

CREATE TABLE login_log (
  user_id VARCHAR(32),
  dt      DATE
);
INSERT INTO login_log VALUES
 ('u001','2026-10-23'),('u001','2026-10-24'),('u001','2026-10-25'),   -- u001 连续 5 天
 ('u001','2026-10-26'),('u001','2026-10-27'),
 ('u002','2026-10-23'),('u002','2026-10-25'),                        -- u002 断续
 ('u003','2026-10-24'),('u003','2026-10-25'),('u003','2026-10-26'),  -- u003 连续 3 天
 ('u004','2026-10-23'),
 ('u004','2026-10-23');                                              -- 重复行，验证 DISTINCT

-- 步骤 1：去重
CREATE TABLE t_login AS SELECT DISTINCT user_id, dt FROM login_log;

-- 步骤 2：打标法——"日期减去序号"得到连续段分组键
-- 同一用户内若日期连续，date_sub(dt, rn) 相同 → 该值相同的行属于同一个连续段
CREATE TABLE t_marked AS
SELECT user_id, dt,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) AS rn,
       DATE_SUB(dt, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) DAY) AS grp
FROM t_login;

-- 步骤 3：按段聚合出每个连续段的天数
CREATE TABLE t_streak AS
SELECT user_id, MIN(dt) AS streak_start, MAX(dt) AS streak_end, COUNT(*) AS days
FROM t_marked GROUP BY user_id, grp;

SELECT * FROM t_streak ORDER BY user_id, streak_start;

-- 断言 C1：u001 存在一个 5 天连续段；u003 3 天；u002 最长 1 天
SELECT IF(SUM(user_id='u001' AND days=5)=1
      AND SUM(user_id='u003' AND days=3)=1
      AND SUM(user_id='u002' AND days=1)=2,
      'PASS C1: 连续段计算全部正确', 'FAIL C1') AS check_1 FROM t_streak;

-- 断言 C2：连续 >=3 天的用户名单（面试要的最终形态）
SELECT user_id, MAX(days) AS max_streak
FROM t_streak GROUP BY user_id HAVING MAX(days) >= 3;
SELECT IF(COUNT(*)=2, 'PASS C2: 连续>=3天的用户共2人', 'FAIL C2') AS check_2 FROM (
  SELECT user_id FROM t_streak GROUP BY user_id HAVING MAX(days) >= 3) t;

-- 思考题（面试追问）：
-- 1. 如何算"连续登录>=N 天的用户数"按月统计？（把 streak_start 的月份当分组键）
-- 2. 上游按天增量时怎么增量维护？（新分区与上一分区 union 后重算该用户窗口，用户级增量而非全量）
-- 3. 数据倾斜在哪一步可能出现？（大用户(机器刷量)单个 partition 过大——落到 03-大数据引擎.md 的倾斜治理）
