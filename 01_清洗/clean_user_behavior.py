# -*- coding: utf-8 -*-
"""
第 2 个脚本：清洗淘宝用户行为数据集（用来做漏斗、留存、时段分析）
原始文件约 1 亿条、900MB，太大了，所以只取前 N 行（默认 200 万行）
用法：python clean_user_behavior.py
"""
import pandas as pd

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"
SRC = BASE + r"\00_数据\UserBehavior.csv"
OUT = BASE + r"\01_清洗\user_behavior_clean.csv"

N = 2_000_000   # 只取前 200 万行；电脑卡就改成 1_000_000

# 1. 原始文件没有表头，所以我们自己指定列名
cols = ["user_id", "item_id", "category_id", "behavior_type", "ts"]
df = pd.read_csv(SRC, header=None, names=cols, nrows=N)
print("读取行数：", len(df))

# 2. 时间戳（秒）转成正常时间
df["event_time"] = pd.to_datetime(df["ts"], unit="s")
df["dt"] = df["event_time"].dt.date
df["hour"] = df["event_time"].dt.hour

# 3. 去掉完全重复的行，去掉异常的行为类型
df = df.drop_duplicates()
df = df[df["behavior_type"].isin(["pv", "buy", "cart", "fav"])]

# 4. 只保留正常时间范围（该数据集官方范围是 2017-11-25 ~ 2017-12-03），剔除时间戳异常的脏数据
df = df[(df["event_time"] >= "2017-11-25") & (df["event_time"] < "2017-12-04")]

# 4. 丢掉不再需要的时间戳列
df = df[["user_id", "item_id", "category_id", "behavior_type", "event_time", "dt", "hour"]]

df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("清洗后行数：", len(df))
print("用户数：", df["user_id"].nunique())
print("商品数：", df["item_id"].nunique())
print("日期范围：", df["dt"].min(), "~", df["dt"].max())
print("各行为条数：")
print(df["behavior_type"].value_counts())
print("已保存到：", OUT)
