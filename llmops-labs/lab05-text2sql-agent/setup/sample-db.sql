-- Lab 05 样例数据库：一个迷你电商（与容器初始化一起自动执行）
-- SET NAMES 必须放在最前：初始化脚本默认可能以 latin1 客户端字符集执行，中文会存成乱码（实测踩过）
SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS shop CHARACTER SET utf8mb4;
USE shop;

CREATE TABLE users (
  user_id    VARCHAR(32) PRIMARY KEY,
  name       VARCHAR(64) NOT NULL,
  city       VARCHAR(32) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
  product_id VARCHAR(32) PRIMARY KEY,
  name       VARCHAR(128) NOT NULL,
  category   VARCHAR(64) NOT NULL,
  price      DECIMAL(18,2) NOT NULL
);

CREATE TABLE orders (
  order_id   VARCHAR(32) PRIMARY KEY,
  user_id    VARCHAR(32) NOT NULL,
  product_id VARCHAR(32) NOT NULL,
  quantity   INT NOT NULL,
  amount     DECIMAL(18,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (user_id, name, city) VALUES
  ('u001', '张伟', '上海'), ('u002', '王芳', '北京'), ('u003', '李娜', '上海'),
  ('u004', '刘强', '广州'), ('u005', '陈静', '深圳'), ('u006', '杨洋', '北京');

INSERT INTO products (product_id, name, category, price) VALUES
  ('p001', '机械键盘', '外设', 399.00), ('p002', '无线鼠标', '外设', 199.00),
  ('p003', '显示器', '显示设备', 1499.00), ('p004', 'USB-C 扩展坞', '配件', 259.00);

INSERT INTO orders (order_id, user_id, product_id, quantity, amount) VALUES
  ('o001', 'u001', 'p001', 1, 399.00),  ('o002', 'u001', 'p002', 2, 398.00),
  ('o003', 'u002', 'p003', 1, 1499.00), ('o004', 'u003', 'p001', 1, 399.00),
  ('o005', 'u004', 'p004', 3, 777.00),  ('o006', 'u005', 'p002', 1, 199.00),
  ('o007', 'u006', 'p003', 2, 2998.00), ('o008', 'u002', 'p001', 1, 399.00);

-- LLM 专用只读账号：Text2SQL 的第一道防线（应用连接串只给它，绝不给 root）
CREATE USER IF NOT EXISTS 'llm_ro'@'%' IDENTIFIED BY 'llm_ro_pass';
GRANT SELECT ON shop.* TO 'llm_ro'@'%';
FLUSH PRIVILEGES;
