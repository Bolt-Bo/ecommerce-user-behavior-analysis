-- 建库建表：在 MySQL Workbench 里全选执行（Ctrl+Shift+Enter）
CREATE DATABASE IF NOT EXISTS ecommerce DEFAULT CHARSET utf8mb4;
USE ecommerce;

DROP TABLE IF EXISTS retail_orders;
CREATE TABLE retail_orders (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    invoice_no   VARCHAR(32),
    stock_code   VARCHAR(32),
    description  VARCHAR(255),
    quantity     INT,
    unit_price   DECIMAL(10, 2),
    customer_id  VARCHAR(32),
    country      VARCHAR(64),
    amount       DECIMAL(14, 2),
    invoice_date DATETIME,
    dt           DATE,
    ym           VARCHAR(7),
    KEY idx_dt (dt),
    KEY idx_customer (customer_id)
);

DROP TABLE IF EXISTS user_behavior;
CREATE TABLE user_behavior (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT,
    item_id       INT,
    category_id   INT,
    behavior_type VARCHAR(8),
    event_time    DATETIME,
    dt            DATE,
    hour          INT,
    KEY idx_type (behavior_type),
    KEY idx_user (user_id),
    KEY idx_dt (dt)
);

-- 确认表建好了
SHOW TABLES;
