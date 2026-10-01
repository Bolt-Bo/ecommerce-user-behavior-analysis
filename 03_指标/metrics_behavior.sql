-- ============ C 组：流量与转化漏斗（对 user_behavior 表）============

-- C1 流量总览：PV、UV、人均浏览量
SELECT
    SUM(behavior_type = 'pv')   AS pv,
    COUNT(DISTINCT user_id)     AS uv,
    ROUND(SUM(behavior_type = 'pv') / COUNT(DISTINCT user_id), 2) AS pv_per_user
FROM user_behavior;

-- C2 四级漏斗（按人数算转化率）
SELECT
    COUNT(DISTINCT CASE WHEN behavior_type = 'pv'   THEN user_id END) AS 浏览人数,
    COUNT(DISTINCT CASE WHEN behavior_type IN ('cart', 'fav') THEN user_id END) AS 加购或收藏人数,
    COUNT(DISTINCT CASE WHEN behavior_type = 'cart' THEN user_id END) AS 加购人数,
    COUNT(DISTINCT CASE WHEN behavior_type = 'buy'  THEN user_id END) AS 下单人数
FROM user_behavior;

-- C3 漏斗每一步的转化率（算好数字直接抄进报告）
-- 注意：加购到下单必须用「加购且下单的人数 / 加购人数」，
-- 不能用「全部下单人数 / 加购人数」，否则会把没加购就下单的人算进来，转化率虚高
WITH f AS (
    SELECT
        COUNT(DISTINCT CASE WHEN behavior_type = 'pv' THEN user_id END) AS pv_uv,
        COUNT(DISTINCT CASE WHEN behavior_type IN ('cart','fav') THEN user_id END) AS interest_uv,
        COUNT(DISTINCT CASE WHEN behavior_type = 'cart' THEN user_id END) AS cart_uv,
        COUNT(DISTINCT CASE WHEN behavior_type = 'buy' THEN user_id END) AS buy_uv
    FROM user_behavior
),
x AS (
    SELECT COUNT(DISTINCT c.user_id) AS cart_buy_uv
    FROM (SELECT DISTINCT user_id FROM user_behavior WHERE behavior_type = 'cart') c
    JOIN (SELECT DISTINCT user_id FROM user_behavior WHERE behavior_type = 'buy') b
      ON c.user_id = b.user_id
)
SELECT
    ROUND(interest_uv / pv_uv * 100, 2)   AS 浏览到兴趣转化率,
    ROUND(cart_uv / pv_uv * 100, 2)       AS 浏览到加购转化率,
    ROUND(cart_buy_uv / cart_uv * 100, 2) AS 加购到下单转化率,
    ROUND(buy_uv / pv_uv * 100, 2)        AS 整体转化率,
    buy_uv - cart_buy_uv                  AS 未加购直接下单人数
FROM f, x;

-- C4 加购了但没下单的人有多少（这是报告里最重要的发现）
SELECT
    COUNT(DISTINCT c.user_id) AS 加购人数,
    COUNT(DISTINCT b.user_id) AS 其中下单人数,
    COUNT(DISTINCT c.user_id) - COUNT(DISTINCT b.user_id) AS 加购未下单人数,
    ROUND((COUNT(DISTINCT c.user_id) - COUNT(DISTINCT b.user_id))
          / COUNT(DISTINCT c.user_id) * 100, 2) AS 流失率
FROM (SELECT DISTINCT user_id FROM user_behavior WHERE behavior_type = 'cart') c
LEFT JOIN (SELECT DISTINCT user_id FROM user_behavior WHERE behavior_type = 'buy') b
       ON c.user_id = b.user_id;

-- C5 各时段活跃度（画柱状图用）
SELECT
    hour,
    COUNT(*)                                     AS 行为次数,
    COUNT(DISTINCT user_id)                      AS 活跃人数,
    SUM(behavior_type = 'buy')                   AS 下单次数
FROM user_behavior
GROUP BY hour
ORDER BY hour;

-- C6 热门品类 Top10
SELECT
    category_id,
    COUNT(*)                                        AS 行为次数,
    COUNT(DISTINCT user_id)                         AS 覆盖人数,
    SUM(behavior_type = 'buy')                      AS 下单次数,
    ROUND(SUM(behavior_type = 'buy') / COUNT(*) * 100, 2) AS 下单占比
FROM user_behavior
GROUP BY category_id
ORDER BY 行为次数 DESC
LIMIT 10;

-- C7 次日 / 7 日留存（写报告必用）
WITH first_day AS (
    SELECT user_id, MIN(dt) AS first_dt
    FROM user_behavior
    GROUP BY user_id
),
active AS (
    SELECT DISTINCT user_id, dt FROM user_behavior
)
SELECT
    DATEDIFF(a.dt, f.first_dt)      AS 第N日,
    COUNT(DISTINCT a.user_id)       AS 留存人数
FROM active a
JOIN first_day f ON a.user_id = f.user_id
WHERE DATEDIFF(a.dt, f.first_dt) BETWEEN 0 AND 7
GROUP BY 第N日
ORDER BY 第N日;

-- C8 复购率（下单超过 1 次的用户占比）
SELECT
    COUNT(*)                                                     AS 下单用户数,
    SUM(CASE WHEN order_cnt > 1 THEN 1 ELSE 0 END)               AS 复购用户数,
    ROUND(SUM(CASE WHEN order_cnt > 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS 复购率
FROM (
    SELECT user_id, COUNT(*) AS order_cnt
    FROM user_behavior
    WHERE behavior_type = 'buy'
    GROUP BY user_id
) t;
