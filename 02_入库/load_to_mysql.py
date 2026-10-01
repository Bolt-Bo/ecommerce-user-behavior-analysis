# -*- coding: utf-8 -*-
"""
第 3 个脚本：把清洗后的 CSV 灌进 MySQL
用法：先把下面 password 改成你自己的 root 密码，再 python load_to_mysql.py
"""
import pandas as pd
from sqlalchemy import create_engine

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"

# 把 123456 换成你装 MySQL 时设的 root 密码
engine = create_engine(
    # 注意：本文件是公开的，不要在这里填真实密码
    "mysql+pymysql://root:填写你的MySQL密码@localhost:3306/ecommerce?charset=utf8mb4"
)

# ---- 1. 导入订单表（约 40 万行，几十秒）----
retail = pd.read_csv(BASE + r"\01_清洗\retail_clean.csv")
retail.to_sql("retail_orders", engine, if_exists="append", index=False, chunksize=20000)
print("retail_orders 导入完成：", len(retail))

# ---- 2. 导入行为表（200 万行，可能要几分钟，耐心等）----
behavior = pd.read_csv(BASE + r"\01_清洗\user_behavior_clean.csv")
behavior.to_sql("user_behavior", engine, if_exists="append", index=False, chunksize=20000)
print("user_behavior 导入完成：", len(behavior))

# ---- 3. 验证一下有没有真的进去 ----
with engine.connect() as conn:
    for t in ["retail_orders", "user_behavior"]:
        n = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t} 表共 {n} 行")
