# -*- coding: utf-8 -*-
"""
把所有指标的查询结果导出成一个 Excel（写报告、做图都从这里取数）
用法：py 03_指标/export_results.py
输出：05_报告/指标结果.xlsx
"""
import re
import pandas as pd
from sqlalchemy import create_engine, text

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"
PASSWORD = "123123"
OUT = BASE + r"\05_报告\指标结果.xlsx"

FILES = [
    BASE + r"\03_指标\metrics_retail.sql",
    BASE + r"\03_指标\metrics_behavior.sql",
]

engine = create_engine(
    f"mysql+pymysql://root:{PASSWORD}@localhost:3306/ecommerce?charset=utf8mb4"
)

def statements(path):
    raw = open(path, encoding="utf-8").read()
    for chunk in raw.split(";"):
        title, body = "", []
        for line in chunk.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("--"):
                if not body and not title:
                    title = s.lstrip("- ").strip()
                continue
            body.append(line)
        stmt = "\n".join(body).strip()
        if stmt:
            yield title, stmt

def safe_sheet(name, used):
    name = re.sub(r"[\\/*?:\[\]]", "_", name)[:28]
    while name in used:
        name = name[:27] + "_"
    used.add(name)
    return name

def main():
    used = set()
    with pd.ExcelWriter(OUT, engine="openpyxl") as writer, engine.connect() as conn:
        for path in FILES:
            for title, stmt in statements(path):
                head = stmt.split()[0].upper()
                if head not in ("SELECT", "WITH"):
                    continue
                try:
                    df = pd.read_sql_query(text(stmt), conn)
                except Exception as e:
                    print("跳过一条（出错）：", title)
                    continue
                code = re.match(r"([A-Z]\d)", title)
                sheet = safe_sheet((code.group(1) + "_" if code else "") + title[:24], used)
                df.to_excel(writer, sheet_name=sheet, index=False)
                print("已导出：", sheet, df.shape)
    print("\n全部导出到：", OUT)

if __name__ == "__main__":
    main()
