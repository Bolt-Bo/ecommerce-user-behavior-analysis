# -*- coding: utf-8 -*-
"""
第 1 个脚本：清洗 Online Retail 数据集（有金额，用来做 GMV 和 RFM）
用法：python clean_retail.py
"""
import pandas as pd

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"
SRC = BASE + r"\00_数据\Online_Retail.xlsx"      # 你下载后放进去的原始文件
OUT = BASE + r"\01_清洗\retail_clean.csv"        # 清洗后生成的文件

# 1. 读原始数据
df = pd.read_excel(SRC)
print("原始行数：", len(df))

# 2. 去掉没有客户编号的行（没有客户ID就没法做 RFM）
df = df.dropna(subset=["CustomerID"])

# 3. 去掉退货单（发票号以 C 开头表示 Cancel）和数量/单价为负数的脏数据
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

# 4. 算金额：Amount = 数量 × 单价
df["Amount"] = df["Quantity"] * df["UnitPrice"]

# 5. 客户编号原来是小数（12583.0），转成整数字符串
df["CustomerID"] = df["CustomerID"].astype(int).astype(str)

# 6. 拆出日期和月份，后面做趋势分析要用
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["dt"] = df["InvoiceDate"].dt.date
df["ym"] = df["InvoiceDate"].dt.to_period("M").astype(str)

# 7. 列名改成小写下划线风格，方便写 SQL
df = df.rename(columns={
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "UnitPrice": "unit_price",
    "CustomerID": "customer_id",
    "Country": "country",
    "InvoiceDate": "invoice_date",
    "Amount": "amount",
})
df = df[[
    "invoice_no", "stock_code", "description", "quantity",
    "unit_price", "customer_id", "country", "amount",
    "invoice_date", "dt", "ym",
]]

# 8. 保存（utf-8-sig 是为了 Excel 打开不乱码）
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("清洗后行数：", len(df))
print("订单数：", df["invoice_no"].nunique())
print("客户数：", df["customer_id"].nunique())
print("GMV：", round(df["amount"].sum(), 2))
print("已保存到：", OUT)
