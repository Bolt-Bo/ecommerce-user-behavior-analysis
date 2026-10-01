# -*- coding: utf-8 -*-
"""
自动生成 4 张报告用图（直接打开 04_看板/图表.xlsx 截图即可）
用法：py 04_看板/make_charts.py
"""
import pandas as pd
from sqlalchemy import create_engine, text
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"
PASSWORD = "123123"
OUT = BASE + r"\04_看板\图表.xlsx"

engine = create_engine(
    f"mysql+pymysql://root:{PASSWORD}@localhost:3306/ecommerce?charset=utf8mb4"
)

def q(sql):
    with engine.connect() as c:
        return pd.read_sql_query(text(sql), c)

wb = Workbook()

def dump(ws, df, start_col=1):
    """把数据框写进工作表，返回 (数据Reference起始列, 分类列号)"""
    ws.cell(row=1, column=start_col, value="")
    for j, col in enumerate(df.columns):
        ws.cell(row=1, column=start_col + j, value=str(col))
    for i, (_, row) in enumerate(df.iterrows(), start=2):
        for j, col in enumerate(df.columns):
            ws.cell(row=i, column=start_col + j, value=row[col])
    return start_col

# ============ 图 1：转化漏斗（横向条形，从大到小呈漏斗状）============
ws1 = wb.active
ws1.title = "图1_转化漏斗"
funnel = pd.DataFrame({
    "环节": ["浏览", "兴趣（收藏/加购）", "加购", "下单"],
    "人数": [19462, 17020, 14638, 13282],
})
dump(ws1, funnel)
c1 = BarChart()
c1.type = "bar"          # 横向
c1.style = 10
c1.title = "四级转化漏斗（去重人数）"
c1.y_axis.title = "人数"
c1.x_axis.title = "环节"
data = Reference(ws1, min_col=2, min_row=1, max_row=1 + len(funnel))
cats = Reference(ws1, min_col=1, min_row=2, max_row=1 + len(funnel))
c1.add_data(data, titles_from_data=True)
c1.set_categories(cats)
c1.dLbls = DataLabelList()
c1.dLbls.showVal = True
c1.width, c1.height = 18, 10
ws1.add_chart(c1, "D2")

# ============ 图 2：月度 GMV 趋势折线 ============
ws2 = wb.create_sheet("图2_月度GMV趋势")
trend = q("""
    SELECT ym AS 月份, ROUND(SUM(amount),2) AS GMV, COUNT(DISTINCT invoice_no) AS 订单数
    FROM retail_orders GROUP BY ym ORDER BY ym
""")
dump(ws2, trend)
c2 = LineChart()
c2.title = "月度 GMV 趋势"
c2.y_axis.title = "GMV"
c2.x_axis.title = "月份"
c2.add_data(Reference(ws2, min_col=2, min_row=1, max_row=1 + len(trend)), titles_from_data=True)
c2.set_categories(Reference(ws2, min_col=1, min_row=2, max_row=1 + len(trend)))
c2.dLbls = DataLabelList()
c2.dLbls.showVal = False
c2.width, c2.height = 20, 10
ws2.add_chart(c2, "E2")

# ============ 图 3：RFM 客户分层金额占比饼图 ============
ws3 = wb.create_sheet("图3_RFM分层")
rfm = q("""
WITH base AS (
  SELECT customer_id,
    DATEDIFF((SELECT MAX(dt) FROM retail_orders), MAX(dt)) AS recency,
    COUNT(DISTINCT invoice_no) AS frequency,
    SUM(amount) AS monetary
  FROM retail_orders GROUP BY customer_id),
score AS (
  SELECT *,
    NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
    NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
  FROM base),
tagged AS (
  SELECT *, IF(r_score>3,'高','低') r_tag, IF(f_score>3,'高','低') f_tag, IF(m_score>3,'高','低') m_tag
  FROM score)
SELECT
  CASE
    WHEN r_tag='高' AND f_tag='高' AND m_tag='高' THEN '重要价值客户'
    WHEN r_tag='高' AND f_tag='低' AND m_tag='高' THEN '重要发展客户'
    WHEN r_tag='低' AND f_tag='高' AND m_tag='高' THEN '重要保持客户'
    WHEN r_tag='低' AND f_tag='低' AND m_tag='高' THEN '重要挽留客户'
    WHEN r_tag='高' AND f_tag='高' AND m_tag='低' THEN '一般价值客户'
    WHEN r_tag='高' AND f_tag='低' AND m_tag='低' THEN '一般发展客户'
    WHEN r_tag='低' AND f_tag='高' AND m_tag='低' THEN '一般保持客户'
    ELSE '一般挽留客户' END AS 客户分层,
  COUNT(*) AS 人数,
  ROUND(SUM(monetary),2) AS 贡献金额
FROM tagged GROUP BY 客户分层 ORDER BY 贡献金额 DESC
""")
dump(ws3, rfm)
c3 = PieChart()
c3.title = "RFM 各分层贡献金额占比"
c3.add_data(Reference(ws3, min_col=3, min_row=1, max_row=1 + len(rfm)), titles_from_data=True)
c3.set_categories(Reference(ws3, min_col=1, min_row=2, max_row=1 + len(rfm)))
c3.dLbls = DataLabelList()
c3.dLbls.showPercent = True
c3.width, c3.height = 18, 12
ws3.add_chart(c3, "E2")

# ============ 图 4：各时段活跃与下单（柱+线组合）============
ws4 = wb.create_sheet("图4_时段活跃与下单")
hour = q("""
    SELECT hour AS 时段, COUNT(*) AS 行为次数, COUNT(DISTINCT user_id) AS 活跃人数,
           SUM(behavior_type='buy') AS 下单次数
    FROM user_behavior GROUP BY hour ORDER BY hour
""")
hour["下单次数"] = hour["下单次数"].astype(int)
dump(ws4, hour)
c4 = BarChart()
c4.title = "各时段活跃度与下单次数"
c4.y_axis.title = "行为次数"
c4.x_axis.title = "时段（小时）"
c4.add_data(Reference(ws4, min_col=2, min_row=1, max_row=1 + len(hour)), titles_from_data=True)
c4.set_categories(Reference(ws4, min_col=1, min_row=2, max_row=1 + len(hour)))
c4.width, c4.height = 22, 11

c4b = LineChart()
c4b.add_data(Reference(ws4, min_col=4, min_row=1, max_row=1 + len(hour)), titles_from_data=True)
c4b.y_axis.axId = 200
c4b.y_axis.title = "下单次数"
c4.y_axis.crosses = "autoZero"
c4b.y_axis.crosses = "max"
c4 += c4b
ws4.add_chart(c4, "F2")

# ============ 图 5（加分项）：留存曲线 ============
ws5 = wb.create_sheet("图5_留存曲线")
ret = q("""
WITH first_day AS (SELECT user_id, MIN(dt) AS first_dt FROM user_behavior GROUP BY user_id),
active AS (SELECT DISTINCT user_id, dt FROM user_behavior)
SELECT DATEDIFF(a.dt, f.first_dt) AS 第N日, COUNT(DISTINCT a.user_id) AS 留存人数
FROM active a JOIN first_day f ON a.user_id = f.user_id
WHERE DATEDIFF(a.dt, f.first_dt) BETWEEN 0 AND 7
GROUP BY 第N日 ORDER BY 第N日
""")
dump(ws5, ret)
c5 = LineChart()
c5.title = "用户留存曲线（第 0–7 日）"
c5.y_axis.title = "留存人数"
c5.x_axis.title = "距离首次活跃天数"
c5.add_data(Reference(ws5, min_col=2, min_row=1, max_row=1 + len(ret)), titles_from_data=True)
c5.set_categories(Reference(ws5, min_col=1, min_row=2, max_row=1 + len(ret)))
c5.dLbls = DataLabelList()
c5.dLbls.showVal = True
c5.width, c5.height = 18, 10
ws5.add_chart(c5, "D2")

wb.save(OUT)
print("图表已生成：", OUT)
print("共 5 张：转化漏斗、月度GMV趋势、RFM分层占比、时段活跃与下单、留存曲线")
