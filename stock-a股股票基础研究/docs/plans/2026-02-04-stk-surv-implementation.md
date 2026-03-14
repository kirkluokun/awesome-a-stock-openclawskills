# 机构调研数据接入 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现机构调研数据的拉取、检索和查询功能

**Architecture:** 两张表设计 - event表存调研事件和content，participant表存参与人员

**Tech Stack:** Python, SQLite, Tushare API

---

## Task 1: 数据库表结构

**Files:**
- Create: `analyzers/stk_surv/schema.sql`
- Create: `analyzers/stk_surv/_shared/db.py`

**Step 1: 创建目录结构**

```bash
mkdir -p analyzers/stk_surv/_shared
touch analyzers/stk_surv/__init__.py
touch analyzers/stk_surv/_shared/__init__.py
```

**Step 2: 创建 schema.sql**

```sql
-- analyzers/stk_surv/schema.sql
CREATE TABLE IF NOT EXISTS stk_surv_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code TEXT NOT NULL,
    name TEXT NOT NULL,
    surv_date TEXT NOT NULL,
    rece_place TEXT,
    rece_mode TEXT,
    comp_rece TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, surv_date)
);

CREATE INDEX IF NOT EXISTS idx_surv_event_ts_code ON stk_surv_event(ts_code);
CREATE INDEX IF NOT EXISTS idx_surv_event_date ON stk_surv_event(surv_date);
CREATE INDEX IF NOT EXISTS idx_surv_event_name ON stk_surv_event(name);

CREATE TABLE IF NOT EXISTS stk_surv_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    fund_visitors TEXT,
    rece_org TEXT,
    org_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES stk_surv_event(id),
    UNIQUE(event_id, fund_visitors, rece_org)
);

CREATE INDEX IF NOT EXISTS idx_surv_part_event_id ON stk_surv_participant(event_id);
CREATE INDEX IF NOT EXISTS idx_surv_part_org ON stk_surv_participant(rece_org);
CREATE INDEX IF NOT EXISTS idx_surv_part_visitor ON stk_surv_participant(fund_visitors);
```

**Step 3: 创建 db.py**

```python
# analyzers/stk_surv/_shared/db.py
"""机构调研数据库工具"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "finance.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    """初始化调研表"""
    conn = connect()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def upsert_event(row: dict) -> int:
    """插入或更新调研事件，返回event_id"""
    conn = connect()
    try:
        sql = """
            INSERT INTO stk_surv_event 
            (ts_code, name, surv_date, rece_place, rece_mode, comp_rece, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ts_code, surv_date) DO UPDATE SET
                name = excluded.name,
                rece_place = excluded.rece_place,
                rece_mode = excluded.rece_mode,
                comp_rece = excluded.comp_rece,
                content = COALESCE(excluded.content, stk_surv_event.content)
        """
        cur = conn.execute(sql, (
            row.get("ts_code"), row.get("name"), row.get("surv_date"),
            row.get("rece_place"), row.get("rece_mode"), row.get("comp_rece"),
            row.get("content")
        ))
        conn.commit()
        
        # 获取event_id
        cur = conn.execute(
            "SELECT id FROM stk_surv_event WHERE ts_code = ? AND surv_date = ?",
            (row.get("ts_code"), row.get("surv_date"))
        )
        return cur.fetchone()["id"]
    finally:
        conn.close()


def upsert_participants(event_id: int, participants: list[dict]) -> int:
    """批量插入参与人员"""
    if not participants:
        return 0
    conn = connect()
    try:
        sql = """
            INSERT INTO stk_surv_participant (event_id, fund_visitors, rece_org, org_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(event_id, fund_visitors, rece_org) DO UPDATE SET
                org_type = excluded.org_type
        """
        values = [
            (event_id, p.get("fund_visitors"), p.get("rece_org"), p.get("org_type"))
            for p in participants
        ]
        conn.executemany(sql, values)
        conn.commit()
        return len(participants)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="机构调研数据库工具")
    parser.add_argument("--init", action="store_true", help="初始化表")
    args = parser.parse_args()
    
    if args.init:
        init_tables()
        print(f"表已初始化: {DB_PATH}")
    else:
        parser.print_help()
```

**Step 4: 初始化表**

```bash
cd openclaw-skills/stock-research-group
python -c "from analyzers.stk_surv._shared.db import init_tables; init_tables(); print('表初始化成功')"
```

**Step 5: Commit**

```bash
git add analyzers/stk_surv/
git commit -m "feat(stk_surv): 添加机构调研表结构和数据库工具"
```

---

## Task 2: Fetcher - 拉取调研数据

**Files:**
- Create: `fetchers/stk_surv.py`

**Step 1: 创建 fetcher**

```python
# fetchers/stk_surv.py
"""从 Tushare 拉取机构调研数据"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.stk_surv._shared.db import upsert_event, upsert_participants

load_dotenv(PROJECT_ROOT.parents[1] / ".env")

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_stk_surv(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
    include_content: bool = True,
) -> int:
    """
    拉取调研数据，存入两张表
    
    Args:
        ts_code: 股票代码
        trade_date: 单日 YYYYMMDD
        start_date/end_date: 日期范围
        include_content: 是否拉取content字段
    
    Returns:
        新增事件数
    """
    pro = get_pro()
    
    fields = "ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org,org_type,comp_rece"
    if include_content:
        fields += ",content"
    
    params = {}
    if ts_code:
        params["ts_code"] = ts_code
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    all_dfs = []
    offset = 0
    limit = 100
    
    # 循环拉取（单次最大100条）
    while True:
        try:
            df = pro.stk_surv(**params, offset=offset, limit=limit, fields=fields)
        except Exception as e:
            print(f"API 调用失败: {e}")
            break
        
        if df is None or df.empty:
            break
        
        all_dfs.append(df)
        print(f"  获取 {len(df)} 条（offset={offset}）")
        
        if len(df) < limit:
            break
        
        offset += limit
        time.sleep(0.5)  # 避免限流
    
    if not all_dfs:
        return 0
    
    # 合并数据
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 按(ts_code, surv_date)分组处理
    event_count = 0
    for (ts_code_val, surv_date_val), group in combined_df.groupby(['ts_code', 'surv_date']):
        # 提取事件信息（取第一条，因为同一事件的公共字段相同）
        first_row = group.iloc[0].to_dict()
        event_row = {
            "ts_code": ts_code_val,
            "name": first_row.get("name"),
            "surv_date": surv_date_val,
            "rece_place": first_row.get("rece_place"),
            "rece_mode": first_row.get("rece_mode"),
            "comp_rece": first_row.get("comp_rece"),
            "content": first_row.get("content") if include_content else None
        }
        
        # 插入或更新事件
        event_id = upsert_event(event_row)
        
        # 提取参与人员
        participants = []
        for _, row in group.iterrows():
            participants.append({
                "fund_visitors": row.get("fund_visitors"),
                "rece_org": row.get("rece_org"),
                "org_type": row.get("org_type")
            })
        
        # 插入参与人员
        upsert_participants(event_id, participants)
        event_count += 1
    
    return event_count


if __name__ == "__main__":
    import argparse
    from datetime import datetime, timedelta
    
    parser = argparse.ArgumentParser(description="拉取机构调研数据")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--date", help="单日 YYYYMMDD")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--days", type=int, help="最近N天")
    parser.add_argument("--no-content", action="store_true", help="不拉取content")
    args = parser.parse_args()
    
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        count = fetch_stk_surv(start_date=start_str, end_date=end_str, include_content=not args.no_content)
    else:
        count = fetch_stk_surv(
            ts_code=args.ts_code,
            trade_date=args.date,
            start_date=args.start,
            end_date=args.end,
            include_content=not args.no_content
        )
    
    print(f"已入库 {count} 个调研事件")
```

**Step 2: 测试拉取**

```bash
python fetchers/stk_surv.py --days 7
```

**Step 3: Commit**

```bash
git add fetchers/stk_surv.py
git commit -m "feat(stk_surv): 添加机构调研数据拉取 fetcher"
```

---

## Task 3: Analyzer - 检索功能

**Files:**
- Create: `analyzers/stk_surv/search.py`

**Step 1: 创建 search.py**

```python
# analyzers/stk_surv/search.py
"""机构调研检索功能"""

from datetime import datetime, timedelta
from ._shared.db import connect


def search_by_company(company_name: str, days: int = None) -> list[dict]:
    """
    按公司名称搜索调研
    
    Args:
        company_name: 公司名称（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["name LIKE ?"]
        params = [f"%{company_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT id, ts_code, name, surv_date, rece_place, rece_mode, comp_rece
            FROM stk_surv_event
            WHERE {' AND '.join(conditions)}
            ORDER BY surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def search_by_org(org_name: str, days: int = None) -> list[dict]:
    """
    按机构名称搜索（该机构参加了哪些调研）
    
    Args:
        org_name: 机构名称（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["p.rece_org LIKE ?"]
        params = [f"%{org_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("e.surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT DISTINCT e.id, e.ts_code, e.name, e.surv_date, 
                   e.rece_place, e.rece_mode, e.comp_rece
            FROM stk_surv_event e
            JOIN stk_surv_participant p ON e.id = p.event_id
            WHERE {' AND '.join(conditions)}
            ORDER BY e.surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def search_by_person(person_name: str, days: int = None) -> list[dict]:
    """
    按参与人员姓名搜索
    
    Args:
        person_name: 人员姓名（支持模糊匹配）
        days: 可选，最近N天
    
    Returns:
        调研事件列表
    """
    conn = connect()
    try:
        conditions = ["p.fund_visitors LIKE ?"]
        params = [f"%{person_name}%"]
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            conditions.append("e.surv_date >= ?")
            params.append(cutoff_date)
        
        sql = f"""
            SELECT DISTINCT e.id, e.ts_code, e.name, e.surv_date,
                   e.rece_place, e.rece_mode, e.comp_rece
            FROM stk_surv_event e
            JOIN stk_surv_participant p ON e.id = p.event_id
            WHERE {' AND '.join(conditions)}
            ORDER BY e.surv_date DESC
        """
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_survey_detail(event_id: int) -> dict:
    """
    获取某次调研的详细信息
    
    Args:
        event_id: 事件ID
    
    Returns:
        {
            "event": {...},
            "participants": [...]
        }
    """
    conn = connect()
    try:
        # 获取事件信息
        cur = conn.execute(
            "SELECT * FROM stk_surv_event WHERE id = ?",
            (event_id,)
        )
        event = dict(cur.fetchone())
        
        # 获取参与人员
        cur = conn.execute(
            "SELECT fund_visitors, rece_org, org_type FROM stk_surv_participant WHERE event_id = ?",
            (event_id,)
        )
        participants = [dict(r) for r in cur.fetchall()]
        
        return {
            "event": event,
            "participants": participants
        }
    finally:
        conn.close()
```

**Step 2: 测试检索**

```bash
python -c "from analyzers.stk_surv.search import search_by_company; import json; print(json.dumps(search_by_company('比亚迪', days=30), ensure_ascii=False, indent=2))"
```

**Step 3: Commit**

```bash
git add analyzers/stk_surv/search.py
git commit -m "feat(stk_surv): 添加检索功能"
```

---

## Task 4: Analyzer - Pipeline 入口

**Files:**
- Create: `analyzers/stk_surv/pipeline.py`

**Step 1: 创建 pipeline.py**

```python
# analyzers/stk_surv/pipeline.py
"""机构调研分析流程入口"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.stk_surv import fetch_stk_surv
from analyzers.stk_surv.search import (
    search_by_company, search_by_org, search_by_person, get_survey_detail
)


def run_fetch_recent(days: int = 30) -> int:
    """拉取最近N天的所有调研数据"""
    return fetch_stk_surv(days=days)


def run_search(query: str, query_type: str = "company", days: int = None) -> list[dict]:
    """
    统一搜索入口
    
    Args:
        query: 搜索关键词
        query_type: company/org/person
        days: 可选，最近N天
    """
    if query_type == "company":
        return search_by_company(query, days)
    elif query_type == "org":
        return search_by_org(query, days)
    elif query_type == "person":
        return search_by_person(query, days)
    else:
        raise ValueError(f"不支持的查询类型: {query_type}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="机构调研分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 拉取
    fetch_p = subparsers.add_parser("fetch", help="拉取调研数据")
    fetch_p.add_argument("--days", type=int, default=30, help="最近N天，默认30")
    
    # 搜索
    search_p = subparsers.add_parser("search", help="搜索调研")
    search_p.add_argument("query", help="搜索关键词")
    search_p.add_argument("--type", choices=["company", "org", "person"], default="company", help="查询类型")
    search_p.add_argument("--days", type=int, help="最近N天")
    
    # 详情
    detail_p = subparsers.add_parser("detail", help="查看调研详情")
    detail_p.add_argument("--event-id", type=int, required=True, help="事件ID")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        count = run_fetch_recent(args.days)
        print(f"已入库 {count} 个调研事件")
    
    elif args.command == "search":
        results = run_search(args.query, args.type, args.days)
        for r in results:
            print(f"[{r['id']}] [{r['surv_date']}] {r['name']} ({r['ts_code']})")
        print(f"\n共 {len(results)} 条")
    
    elif args.command == "detail":
        result = get_survey_detail(args.event_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
```

**Step 2: 测试 pipeline**

```bash
python -m analyzers.stk_surv.pipeline fetch --days 7
python -m analyzers.stk_surv.pipeline search "比亚迪" --type company
```

**Step 3: Commit**

```bash
git add analyzers/stk_surv/pipeline.py
git commit -m "feat(stk_surv): 添加 pipeline 入口"
```

---

## 验收测试

```bash
cd openclaw-skills/stock-research-group

# 1. 初始化表
python -c "from analyzers.stk_surv._shared.db import init_tables; init_tables()"

# 2. 拉取最近7天数据
python -m analyzers.stk_surv.pipeline fetch --days 7

# 3. 搜索某公司
python -m analyzers.stk_surv.pipeline search "比亚迪" --type company

# 4. 查看详情
python -m analyzers.stk_surv.pipeline detail --event-id 1
```
