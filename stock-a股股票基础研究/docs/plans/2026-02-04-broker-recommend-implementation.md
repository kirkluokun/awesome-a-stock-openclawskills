# 券商月度金股数据接入 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现券商月度金股数据的拉取、存储、统计和报告生成功能

**Architecture:** 三层架构 - fetchers 拉取数据存DB，analyzers 统计计算，interpreters 生成报告

**Tech Stack:** Python, SQLite, Tushare API

---

## Task 1: 数据库表结构

**Files:**
- Create: `analyzers/broker_recommend/schema.sql`
- Create: `analyzers/broker_recommend/_shared/db.py`

**Step 1: 创建目录结构**

```bash
mkdir -p analyzers/broker_recommend/_shared
touch analyzers/broker_recommend/__init__.py
touch analyzers/broker_recommend/_shared/__init__.py
```

**Step 2: 创建 schema.sql**

```sql
-- analyzers/broker_recommend/schema.sql
CREATE TABLE IF NOT EXISTS broker_recommend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,              -- 月度 YYYYMM
    broker TEXT NOT NULL,             -- 券商名称
    ts_code TEXT NOT NULL,            -- 股票代码
    name TEXT NOT NULL,               -- 股票简称
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(month, broker, ts_code)
);

CREATE INDEX IF NOT EXISTS idx_br_month ON broker_recommend(month);
CREATE INDEX IF NOT EXISTS idx_br_ts_code ON broker_recommend(ts_code);
CREATE INDEX IF NOT EXISTS idx_br_broker ON broker_recommend(broker);
```

**Step 3: 创建 db.py**

```python
# analyzers/broker_recommend/_shared/db.py
"""券商金股数据库工具"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "finance.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_table():
    """初始化券商金股表"""
    conn = connect()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def upsert_recommendations(rows: list[dict]) -> int:
    """批量插入金股数据，返回插入条数"""
    if not rows:
        return 0
    conn = connect()
    try:
        sql = """
            INSERT INTO broker_recommend (month, broker, ts_code, name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(month, broker, ts_code) DO UPDATE SET
                name = excluded.name
        """
        values = [
            (r.get("month"), r.get("broker"), r.get("ts_code"), r.get("name"))
            for r in rows
        ]
        conn.executemany(sql, values)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="券商金股数据库工具")
    parser.add_argument("--init", action="store_true", help="初始化表")
    args = parser.parse_args()
    
    if args.init:
        init_table()
        print(f"表已初始化: {DB_PATH}")
    else:
        parser.print_help()
```

**Step 4: 初始化表**

```bash
cd openclaw-skills/stock-research-group
python -c "from analyzers.broker_recommend._shared.db import init_table; init_table()"
```

**Step 5: Commit**

```bash
git add analyzers/broker_recommend/
git commit -m "feat(broker_recommend): 添加券商金股表结构和数据库工具"
```

---

## Task 2: Fetcher - 拉取金股数据

**Files:**
- Create: `fetchers/broker_recommend.py`

**Step 1: 创建 fetcher**

```python
# fetchers/broker_recommend.py
"""从 Tushare 拉取券商月度金股数据"""

import os
import sys
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.broker_recommend._shared.db import upsert_recommendations

load_dotenv(PROJECT_ROOT.parents[1] / ".env")

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_broker_recommend(month: str) -> int:
    """
    从 Tushare 拉取指定月份的金股数据，存入 DB
    
    Args:
        month: 月度 YYYYMM，如 "202602"
    
    Returns:
        新增/更新条数
    """
    pro = get_pro()
    
    try:
        df = pro.broker_recommend(month=month)
    except Exception as e:
        print(f"API 调用失败: {e}")
        return 0
    
    if df.empty:
        return 0
    
    rows = df.to_dict("records")
    return upsert_recommendations(rows)


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="拉取券商月度金股")
    parser.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    args = parser.parse_args()
    
    month = args.month or datetime.now().strftime("%Y%m")
    count = fetch_broker_recommend(month)
    print(f"已入库 {count} 条金股数据（{month}）")
```

**Step 2: 测试拉取**

```bash
python fetchers/broker_recommend.py --month 202602
```

**Step 3: Commit**

```bash
git add fetchers/broker_recommend.py
git commit -m "feat(broker_recommend): 添加券商金股数据拉取 fetcher"
```

---

## Task 3: Analyzer - 统计功能

**Files:**
- Create: `analyzers/broker_recommend/stats.py`

**Step 1: 创建 stats.py**

```python
# analyzers/broker_recommend/stats.py
"""券商金股统计功能"""

from collections import defaultdict
from ._shared.db import connect


def get_monthly_stats(month: str) -> dict:
    """
    获取指定月份的统计
    
    Returns:
        {
            "month": "202602",
            "by_company": [{"ts_code": "...", "name": "...", "count": 5, "brokers": [...]}],
            "by_broker": [{"broker": "...", "count": 10}]
        }
    """
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT ts_code, name, broker FROM broker_recommend WHERE month = ?",
            (month,)
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    
    # 按公司统计
    company_stats = defaultdict(lambda: {"ts_code": "", "name": "", "count": 0, "brokers": []})
    for row in rows:
        key = row["ts_code"]
        company_stats[key]["ts_code"] = row["ts_code"]
        company_stats[key]["name"] = row["name"]
        company_stats[key]["count"] += 1
        company_stats[key]["brokers"].append(row["broker"])
    
    by_company = sorted(
        [
            {
                "ts_code": v["ts_code"],
                "name": v["name"],
                "count": v["count"],
                "brokers": list(set(v["brokers"]))
            }
            for v in company_stats.values()
        ],
        key=lambda x: x["count"],
        reverse=True
    )
    
    # 按券商统计
    broker_stats = defaultdict(int)
    for row in rows:
        broker_stats[row["broker"]] += 1
    
    by_broker = sorted(
        [{"broker": k, "count": v} for k, v in broker_stats.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return {
        "month": month,
        "by_company": by_company,
        "by_broker": by_broker
    }


def get_continuous_recommendations(ts_code: str, min_months: int = 2) -> list[str]:
    """
    获取连续被推荐的月份列表
    
    Args:
        ts_code: 股票代码
        min_months: 最少连续月份数
    
    Returns:
        连续月份列表，如 ["202501", "202502", "202503"]
    """
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT DISTINCT month FROM broker_recommend WHERE ts_code = ? ORDER BY month",
            (ts_code,)
        )
        months = [r["month"] for r in cur.fetchall()]
    finally:
        conn.close()
    
    if len(months) < min_months:
        return []
    
    # 找出连续月份
    continuous = []
    current_seq = [months[0]]
    
    for i in range(1, len(months)):
        prev_month = int(current_seq[-1])
        curr_month = int(months[i])
        
        # 计算月份差（考虑跨年）
        if curr_month % 100 == 1 and prev_month % 100 == 12:
            # 跨年：12月 -> 1月
            if current_seq:
                continuous.append(current_seq)
            current_seq = [months[i]]
        elif curr_month == prev_month + 1 or (curr_month % 100 == prev_month % 100 + 1 and curr_month // 100 == prev_month // 100):
            # 连续月份
            current_seq.append(months[i])
        else:
            # 不连续
            if len(current_seq) >= min_months:
                continuous.append(current_seq)
            current_seq = [months[i]]
    
    if len(current_seq) >= min_months:
        continuous.append(current_seq)
    
    # 返回最长的连续序列
    return max(continuous, key=len) if continuous else []


def get_broker_recommendations(broker: str, month: str = None) -> list[dict]:
    """
    获取某券商的金股列表
    
    Args:
        broker: 券商名称
        month: 可选，指定月份
    
    Returns:
        金股列表
    """
    conn = connect()
    try:
        if month:
            cur = conn.execute(
                "SELECT month, ts_code, name FROM broker_recommend WHERE broker = ? AND month = ? ORDER BY ts_code",
                (broker, month)
            )
        else:
            cur = conn.execute(
                "SELECT month, ts_code, name FROM broker_recommend WHERE broker = ? ORDER BY month DESC, ts_code",
                (broker,)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
```

**Step 2: 测试统计**

```bash
python -c "from analyzers.broker_recommend.stats import get_monthly_stats; import json; print(json.dumps(get_monthly_stats('202602'), ensure_ascii=False, indent=2))"
```

**Step 3: Commit**

```bash
git add analyzers/broker_recommend/stats.py
git commit -m "feat(broker_recommend): 添加统计功能"
```

---

## Task 4: Analyzer - Pipeline 入口

**Files:**
- Create: `analyzers/broker_recommend/pipeline.py`

**Step 1: 创建 pipeline.py**

```python
# analyzers/broker_recommend/pipeline.py
"""券商金股分析流程入口"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.broker_recommend import fetch_broker_recommend
from analyzers.broker_recommend.stats import get_monthly_stats


def run_fetch(month: str = None) -> int:
    """
    拉取数据
    
    Args:
        month: 月度 YYYYMM，None 时使用当前月份
    
    Returns:
        新增条数
    """
    if not month:
        month = datetime.now().strftime("%Y%m")
    return fetch_broker_recommend(month)


def run_stats(month: str = None) -> dict:
    """
    运行统计
    
    Args:
        month: 月度 YYYYMM，None 时使用当前月份
    
    Returns:
        统计结果
    """
    if not month:
        month = datetime.now().strftime("%Y%m")
    return get_monthly_stats(month)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="券商金股分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 拉取
    fetch_p = subparsers.add_parser("fetch", help="拉取金股数据")
    fetch_p.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    
    # 统计
    stats_p = subparsers.add_parser("stats", help="查看统计")
    stats_p.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        count = run_fetch(args.month)
        print(f"已入库 {count} 条")
    
    elif args.command == "stats":
        result = run_stats(args.month)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
```

**Step 2: 测试 pipeline**

```bash
python -m analyzers.broker_recommend.pipeline fetch --month 202602
python -m analyzers.broker_recommend.pipeline stats --month 202602
```

**Step 3: Commit**

```bash
git add analyzers/broker_recommend/pipeline.py
git commit -m "feat(broker_recommend): 添加 pipeline 入口"
```

---

## Task 5: Interpreter - 报告生成

**Files:**
- Create: `interpreters/broker_recommend/report.py`

**Step 1: 创建目录结构**

```bash
mkdir -p interpreters/broker_recommend
touch interpreters/broker_recommend/__init__.py
```

**Step 2: 创建 report.py**

```python
# interpreters/broker_recommend/report.py
"""券商金股报告生成"""

import csv
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.broker_recommend.stats import get_monthly_stats

OUTPUT_DIR = PROJECT_ROOT / "output"


def generate_report(month: str, output_format: str = "csv") -> str:
    """
    生成报告
    
    Args:
        month: 月度 YYYYMM
        output_format: 输出格式，目前仅支持 csv
    
    Returns:
        文件路径
    """
    stats = get_monthly_stats(month)
    
    if output_format == "csv":
        filename = f"broker_recommend_{month}.csv"
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["排名", "股票代码", "股票名称", "推荐次数", "推荐券商"])
            
            for i, item in enumerate(stats["by_company"], 1):
                brokers_str = "|".join(item["brokers"])
                writer.writerow([
                    i,
                    item["ts_code"],
                    item["name"],
                    item["count"],
                    brokers_str
                ])
        
        print(f"报告已生成: {filepath}")
        return str(filepath)
    
    else:
        raise ValueError(f"不支持的格式: {output_format}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成券商金股报告")
    parser.add_argument("--month", help="月度 YYYYMM，默认当前月份")
    parser.add_argument("--format", default="csv", help="输出格式，默认 csv")
    args = parser.parse_args()
    
    month = args.month or datetime.now().strftime("%Y%m")
    generate_report(month, args.format)
```

**Step 3: 测试报告生成**

```bash
python interpreters/broker_recommend/report.py --month 202602
```

**Step 4: Commit**

```bash
git add interpreters/broker_recommend/
git commit -m "feat(broker_recommend): 添加报告生成功能"
```

---

## 验收测试

```bash
cd openclaw-skills/stock-research-group

# 1. 初始化表
python -c "from analyzers.broker_recommend._shared.db import init_table; init_table()"

# 2. 拉取数据
python -m analyzers.broker_recommend.pipeline fetch --month 202602

# 3. 查看统计
python -m analyzers.broker_recommend.pipeline stats --month 202602

# 4. 生成报告
python interpreters/broker_recommend/report.py --month 202602

# 5. 查看输出
cat output/broker_recommend_202602.csv
```
