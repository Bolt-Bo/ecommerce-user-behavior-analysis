-- ============ A 组：GMV 与商品分析（对 retail_orders 表）============
-- 每条语句可以单独选中执行

-- A1 总览：GMV、订单数、客户数、客单价
SELECT
    ROUND(SUM(amount), 2)                AS gmv,
    COUNT(DISTINCT invoice_no)           AS order_cnt,
    COUNT(DISTINCT customer_id)          AS customer_cnt,
    ROUND(SUM(amount) / COUNT(DISTINCT invoice_no), 2) AS avg_order_value
FROM retail_orders;

-- A2 GMV 拆解：GMV = 客户数 × 人均订单数 × 客单价
SELECT
    COUNT(DISTINCT customer_id)                                  AS 客户数,
    ROUND(COUNT(DISTINCT invoice_no) / COUNT(DISTINCT customer_id), 2) AS 人均订单数,
    ROUND(SUM(amount) / COUNT(DISTINCT invoice_no), 2)            AS 客单价,
    ROUND(SUM(amount), 2)                                        AS GMV
FROM retail_orders;

-- A3 月度趋势（画折线图用）
SELECT
    ym,
    ROUND(SUM(amount), 2)      AS gmv,
    COUNT(DISTINCT invoice_no) AS order_cnt,
    COUNT(DISTINCT customer_id) AS customer_cnt
FROM retail_orders
GROUP BY ym
ORDER BY ym;

-- A4 热销商品 Top10
SELECT
    stock_code,
    MIN(description)           AS product_name,
    SUM(quantity)              AS total_qty,
    ROUND(SUM(amount), 2)      AS total_amount
FROM retail_orders
GROUP BY stock_code
ORDER BY total_amount DESC
LIMIT 10;

-- A5 二八法则：累计贡献 80% 销售额的商品有多少个
WITH item_amt AS (
    SELECT stock_code, SUM(amount) AS amt
    FROM retail_orders
    GROUP BY stock_code
),
ranked AS (
    SELECT
        stock_code, amt,
        SUM(amt) OVER (ORDER BY amt DESC) AS cum_amt,
        SUM(amt) OVER ()                  AS total_amt
    FROM item_amt
)
SELECT COUNT(*) AS 贡献80percent销售额的商品数
FROM ranked
WHERE cum_amt <= total_amt * 0.8;

-- A6 国家/地区分布
SELECT country, ROUND(SUM(amount), 2) AS gmv, COUNT(DISTINCT customer_id) AS customer_cnt
FROM retail_orders
GROUP BY country
ORDER BY gmv DESC
LIMIT 10;

-- ============ B 组：RFM 用户分层（8 类）============
WITH base AS (
    SELECT
        customer_id,
        DATEDIFF((SELECT MAX(dt) FROM retail_orders), MAX(dt)) AS recency,
        COUNT(DISTINCT invoice_no)                             AS frequency,
        SUM(amount)                                            AS monetary
    FROM retail_orders
    GROUP BY customer_id
),
score AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,   -- 越近越高分
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,  -- 越频越高分
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score    -- 越多越高分
    FROM base
),
tagged AS (
    SELECT *,
        IF(r_score > 3, '高', '低') AS r_tag,
        IF(f_score > 3, '高', '低') AS f_tag,
        IF(m_score > 3, '高', '低') AS m_tag
    FROM score
)
SELECT
    CASE
        WHEN r_tag='高' AND f_tag='高' AND m_tag='高' THEN '重要价值客户'
        WHEN r_tag='高' AND f_tag='低' AND m_tag='高' THEN '重要发展客户'
        WHEN r_tag='低' AND f_tag='高' AND m_tag='高' THEN '重要保持客户'
        WHEN r_tag='低' AND f_tag='低' AND m_tag='高' THEN '重要挽留客户'
        WHEN r_tag='高' AND f_tag='高' AND m_tag='低' THEN '一般价值客户'
        WHEN r_tag='高' AND f_tag='低' AND m_tag='低' THEN '一般发展客户'
        WHEN r_tag='低' AND f_tag='高' AND m_tag='低' THEN '一般保持客户'
        ELSE '一般挽留客户'
    END AS segment,
    COUNT(*)                        AS 人数,
    ROUND(AVG(recency), 1)          AS 平均最近购买天数,
    ROUND(AVG(frequency), 2)        AS 平均购买次数,
    ROUND(SUM(monetary), 2)         AS 贡献金额
FROM tagged
GROUP BY segment
ORDER BY 贡献金额 DESC;

-- B2 各层客户占比（写报告要用）
-- 把上面 SELECT 的 CASE 表达式换成下面这句即可：
-- ROUND(COUNT(*) / (SELECT COUNT(*) FROM tagged) * 100, 2) AS 占比百分比
