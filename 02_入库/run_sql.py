# -*- coding: utf-8 -*-
"""
一键跑 SQL 脚本（代替 Workbench）
用法：在命令行里执行（密码要先改对）：
    py 02_入库/run_sql.py create      ← 建表
    py 02_入库/run_sql.py retail      ← GMV、商品、RFM 指标
    py 02_入库/run_sql.py behavior    ← 漏斗、留存、时段指标
"""
import re
import sys
import pandas as pd
from sqlalchemy import create_engine, text

BASE = r"C:\Users\admin\Desktop\电商数据分析项目"
# 注意：本文件是公开的，不要在这里填真实密码
PASSWORD = "填写你的MySQL密码"   # ← 改成你的 MySQL root 密码

FILES = {
    "create":   BASE + r"\02_入库\create_tables.sql",
    "retail":   BASE + r"\03_指标\metrics_retail.sql",
    "behavior": BASE + r"\03_指标\metrics_behavior.sql",
}

engine = create_engine(
    f"mysql+pymysql://root:{PASSWORD}@localhost:3306/ecommerce?charset=utf8mb4"
)

def statements(path):
    """把 SQL 文件按分号拆成一条条语句，顺便提取每条上面的 -- 注释当标题"""
    raw = open(path, encoding="utf-8").read()
    for chunk in raw.split(";"):
        title, body = "", []
        for line in chunk.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("--"):
                # 第一条注释当标题，其余注释行全部跳过（不当成 SQL）
                if not body and not title:
                    title = s.lstrip("- ").strip()
                continue
            body.append(line)
        stmt = "\n".join(body).strip()
        if stmt:
            yield title, stmt

def run(key):
    path = FILES[key]
    print("=" * 62)
    print("执行：", path)
    with engine.connect() as conn:
        for title, stmt in statements(path):
            head = stmt.split()[0].upper()
            try:
                if head in ("SELECT", "WITH"):
                    df = pd.read_sql_query(text(stmt), conn)
                    print("\n【" + (title or "查询结果") + "】")
                    print(df.to_string(index=False))
                else:
                    conn.exec_driver_sql(stmt)
                    conn.commit()
                    if title:
                        print("完成：" + title)
            except Exception as e:
                print("这条出错（不影响后面）：", title or stmt[:40])
                print("   ", str(e).split("\n")[0])

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in FILES:
        print("用法：py 02_入库/run_sql.py create|retail|behavior")
        sys.exit(1)
    run(sys.argv[1])
    print("\n跑完了。")
