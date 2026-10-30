-- ============================================================
-- 实验二：数仓四层分层落地 + 次日留存指标
-- 对应面试题：02-数仓建模.md Q1 / Q22
-- 运行方式：
--   docker exec -i llmops-mysql mysql -uroot -proot_lab_only < 02-分层与留存.sql
-- ============================================================
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS dw_lab2;
CREATE DATABASE dw_lab2 CHARACTER SET utf8mb4;
USE dw_lab2;

-- ---------- ODS：原始事件流（模拟上游推送，含重复与脏数据——真实世界如此） ----------
CREATE TABLE ods_user_event_raw (
  dt        DATE,
  user_id   VARCHAR(32),
  event     VARCHAR(32),      -- open / pay / click
  event_ts  VARCHAR(32)       -- 上游给的是字符串，格式问题在 DWD 修
);
INSERT INTO ods_user_event_raw VALUES
 ('2026-10-23','u001','open','2026-10-23 08:00:01'),
 ('2026-10-23','u002','open','2026-10-23 09:12:00'),
 ('2026-10-23','u003','open','2026-10-23 21:40:11'),
 ('2026-10-23','u001','open','2026-10-23 08:00:01'),        -- 上游重复推送
 ('2026-10-23','u004','open','2026-10-23 10:00:00'),
 ('2026-10-24','u001','open','2026-10-24 08:00:02'),
 ('2026-10-24','u002','open','2026-10-24 09:30:00'),
 ('2026-10-24','u005','open','2026-10-24 20:11:00'),
 ('2026-10-25','u001','open','2026-10-25 08:00:03'),
 ('2026-10-25','u003','open','2026-10-25 12:00:00'),
 ('2026-10-25','u005','open','2026-10-25 19:00:00'),
 ('2026-10-25','u006','open','2026-10-25 22:30:00'),
 ('2026-10-26','u001','open','2026-10-26 08:00:04'),
 ('2026-10-26','u005','open','2026-10-26 18:00:00'),
 ('2026-10-26','u006','open','2026-10-26 21:00:00'),
 ('2026-10-27','u005','open','2026-10-27 18:00:00'),
 ('2026-10-27','u006','open','2026-10-27 21:10:00'),
 ('2026-10-27','u001','open','2026-10-27 08:00:05'),
 ('2026-10-27','','open','2026-10-27 12:00:00');            -- 脏数据：空 user_id

-- ---------- DWD：清洗去重 + 规范化，一事件一表 ----------
CREATE TABLE dwd_user_open AS
SELECT dt,
       user_id,
       event_ts                                AS event_time
FROM (
  SELECT dt, user_id, event_ts,
         ROW_NUMBER() OVER (PARTITION BY dt, user_id, event ORDER BY event_ts) AS rn
  FROM ods_user_event_raw
  WHERE event = 'open' AND user_id <> ''        -- 去重：同 dt+user+event 只留最早一条
) t
WHERE rn = 1;

-- 断言 B1：19 行原始 → 去重去脏后 17 行（上游重复 1 条 + 空 user_id 脏数据 1 条）
SELECT IF((SELECT COUNT(*) FROM ods_user_event_raw)=19
      AND (SELECT COUNT(*) FROM dwd_user_open)=17,
      'PASS B1: ODS 19 行 -> DWD 17 行（去重1条+脏数据1条）', 'FAIL B1') AS check_1;

-- ---------- DWS：用户 × 天 活跃明细（沉淀复用粒度） ----------
CREATE TABLE dws_user_active_1d AS
SELECT dt, user_id FROM dwd_user_open;

-- ---------- ADS：次日留存率 ----------
CREATE TABLE ads_user_retention_1d AS
SELECT a.dt                                     AS first_dt,          -- 首访日
       COUNT(DISTINCT a.user_id)                AS new_users,
       COUNT(DISTINCT b.user_id)                AS retained_1d,
       ROUND(COUNT(DISTINCT b.user_id) / COUNT(DISTINCT a.user_id) * 100, 1) AS retention_rate
FROM dws_user_active_1d a
LEFT JOIN dws_user_active_1d b
       ON a.user_id = b.user_id AND b.dt = DATE_ADD(a.dt, INTERVAL 1 DAY)
GROUP BY a.dt;

SELECT * FROM ads_user_retention_1d ORDER BY first_dt;

-- 断言 B2：10-23 新增 4 人（u001-u004），次日 u001、u002 回流 → 留存 50%
SELECT IF(SUM(first_dt='2026-10-23' AND new_users=4 AND retained_1d=2 AND retention_rate=50.0)=1,
          'PASS B2: 10-23 首访 4 人次日留存 50%', 'FAIL B2') AS check_2
FROM ads_user_retention_1d;

-- 断言 B3：10-27 无次日数据，留存应为 0（NULL 计 0）
SELECT IF(SUM(first_dt='2026-10-27' AND retained_1d=0)=1,
          'PASS B3: 尾日留存 0（无次日数据）', 'FAIL B3') AS check_3
FROM ads_user_retention_1d;

-- ---------- 层与层的关系演示：血缘可见 ----------
-- ods_user_event_raw (19行) -> dwd_user_open (16行) -> dws_user_active_1d -> ads_user_retention_1d
-- 面试表述："留存口径只定义一次（DWS 活跃 + ADS join 规则），下游所有报表共用，
--            活跃口径变更时只需重刷 DWS 两张表。"
