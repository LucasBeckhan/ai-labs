-- ============================================================
-- 实验一：拉链表（缓慢变化维 SCD2）全流程
-- 对应面试题：02-数仓建模.md Q6
-- 运行方式：
--   docker exec -i llmops-mysql mysql -uroot -proot_lab_only < 01-拉链表.sql
-- 可重复执行：每次运行都会重建 dw_lab 库
-- ============================================================
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS dw_lab;
CREATE DATABASE dw_lab CHARACTER SET utf8mb4;
USE dw_lab;

-- ---------- 1. 目标表：用户等级拉链表 ----------
CREATE TABLE dim_user_level_chain (
  user_id    VARCHAR(32) NOT NULL,
  level      VARCHAR(16) NOT NULL,
  start_date DATE        NOT NULL,
  end_date   DATE        NOT NULL     -- 9999-12-31 = 当前有效
);

-- ---------- 2. 上游每日增量（模拟 3 天） ----------
CREATE TABLE ods_user_level_inc (
  dt      DATE        NOT NULL,
  user_id VARCHAR(32) NOT NULL,
  level   VARCHAR(16) NOT NULL
);
-- 第 1 天(10-23)：全量初始化
INSERT INTO ods_user_level_inc VALUES
 ('2026-10-23','u001','普通'),('2026-10-23','u002','普通'),('2026-10-23','u003','黄金');
-- 第 2 天(10-24)：u002 升级黄金；u004 新用户
INSERT INTO ods_user_level_inc VALUES
 ('2026-10-24','u001','普通'),('2026-10-24','u002','黄金'),('2026-10-24','u003','黄金'),('2026-10-24','u004','黄金');
-- 第 3 天(10-25)：u001 升黄金；u003 降普通
INSERT INTO ods_user_level_inc VALUES
 ('2026-10-25','u001','黄金'),('2026-10-25','u002','黄金'),('2026-10-25','u003','普通'),('2026-10-25','u004','黄金');

-- ---------- 3. 第 1 天：全量初始化（直接开链） ----------
INSERT INTO dim_user_level_chain
SELECT user_id, level, dt, '9999-12-31' FROM ods_user_level_inc WHERE dt='2026-10-23';

-- 断言 A1：初始化后 3 条、全部当前有效
SELECT IF(COUNT(*)=3 AND SUM(end_date='9999-12-31')=3, 'PASS A1: 初始化 3 条全有效', 'FAIL A1') AS check_1
FROM dim_user_level_chain;

-- ---------- 4. 第 2 天处理（标准两步：先关链再开链，可重跑） ----------
-- 关链：当前有效 且 与增量不一致 的记录。end_date = 增量日当天（左闭右开：[start, end)）
UPDATE dim_user_level_chain c
JOIN ods_user_level_inc i
  ON c.user_id = i.user_id AND c.level <> i.level
SET c.end_date = '2026-10-24'
WHERE i.dt = '2026-10-24' AND c.end_date = '9999-12-31';
-- 开链：增量中"没有当前同等级有效记录"的（新用户 / 发生变化的）
INSERT INTO dim_user_level_chain
SELECT i.user_id, i.level, i.dt, '9999-12-31'
FROM ods_user_level_inc i
WHERE i.dt = '2026-10-24'
  AND NOT EXISTS (SELECT 1 FROM dim_user_level_chain c
                  WHERE c.user_id = i.user_id AND c.level = i.level AND c.end_date='9999-12-31');

-- 断言 A2：u002 应有两条（普通已关链 + 黄金有效）；总行数 5
SELECT IF(COUNT(*)=5, 'PASS A2: 第2天后共5条', 'FAIL A2') AS check_2 FROM dim_user_level_chain;
SELECT IF(COUNT(*)=2, 'PASS A2.1: u002 留下2个历史版本', 'FAIL A2.1') AS check_2_1
FROM dim_user_level_chain WHERE user_id='u002';

-- ---------- 5. 第 3 天处理（同样的两步，只是日期换掉） ----------
UPDATE dim_user_level_chain c
JOIN ods_user_level_inc i
  ON c.user_id = i.user_id AND c.level <> i.level
SET c.end_date = '2026-10-25'
WHERE i.dt = '2026-10-25' AND c.end_date = '9999-12-31';
INSERT INTO dim_user_level_chain
SELECT i.user_id, i.level, i.dt, '9999-12-31'
FROM ods_user_level_inc i
WHERE i.dt = '2026-10-25'
  AND NOT EXISTS (SELECT 1 FROM dim_user_level_chain c
                  WHERE c.user_id = i.user_id AND c.level = i.level AND c.end_date='9999-12-31');

-- 断言 A3：总行数 8（4 当前有效 + 4 历史）
SELECT IF(COUNT(*)=7 AND SUM(end_date='9999-12-31')=4, 'PASS A3: 3天后共7条、4条有效', 'FAIL A3') AS check_3
FROM dim_user_level_chain;

-- ---------- 6. 核心查询：任意"按当时状态"回溯 ----------
-- 查 2026-10-24 当天各等级的用户数（当时 u002 还是普通……不对，10-24 已是黄金）
SELECT level, COUNT(*) AS users
FROM dim_user_level_chain
WHERE start_date <= '2026-10-24' AND end_date > '2026-10-24'
GROUP BY level;
-- 断言 A4：10-24 当天 黄金3 / 普通1
SELECT IF(SUM(level='黄金')=3 AND SUM(level='普通')=1,
          'PASS A4: 10-24 当日快照 黄金3/普通1', 'FAIL A4') AS check_4
FROM dim_user_level_chain
WHERE start_date <= '2026-10-24' AND end_date > '2026-10-24';

-- 查 u001 的完整历史（面试常让你手写这条）
SELECT user_id, level, start_date, end_date
FROM dim_user_level_chain WHERE user_id='u001' ORDER BY start_date;
-- 断言 A5：u001 恰好两条（普通→黄金）
SELECT IF(COUNT(*)=2, 'PASS A5: u001 两个版本', 'FAIL A5') AS check_5
FROM dim_user_level_chain WHERE user_id='u001';

-- ---------- 7. 幂等性验证：重跑第 3 天处理，行数不应变化 ----------
UPDATE dim_user_level_chain c
JOIN ods_user_level_inc i ON c.user_id = i.user_id AND c.level <> i.level
SET c.end_date = '2026-10-24' WHERE i.dt = '2026-10-25' AND c.end_date = '9999-12-31';
INSERT INTO dim_user_level_chain
SELECT i.user_id, i.level, i.dt, '9999-12-31' FROM ods_user_level_inc i
WHERE i.dt = '2026-10-25'
  AND NOT EXISTS (SELECT 1 FROM dim_user_level_chain c
                  WHERE c.user_id = i.user_id AND c.level = i.level AND c.end_date='9999-12-31');
SELECT IF(COUNT(*)=7, 'PASS A6: 重跑幂等，仍为7条', 'FAIL A6') AS check_6 FROM dim_user_level_chain;
