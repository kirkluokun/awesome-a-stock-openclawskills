# 财务指标数据接入 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 接入 `fina_indicator`/`fina_indicator_vip`，支持单公司查询与按季度批量刷新，并完成存储与查询能力。

**Architecture:** 复用 balancesheet 的三层结构（fetchers/analyzers/CLI），采用“基础列+payload_json”存储，唯一键用 `ts_code+end_date` 以支持覆盖更新。批量刷新按季度 period 进行，区间自动拆分为季度末列表。

**Tech Stack:** Python, SQLite, pandas, tushare, json

---

### Task 1: 创建数据表结构

**Files:**
- Create: `analyzers/fina_indicator/schema.sql`

**Step 1: 创建 schema.sql**

```sql
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS fina_indicator (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  end_date TEXT NOT NULL,
  roe REAL,
  roa REAL,
  grossprofit_margin REAL,
  netprofit_margin REAL,
  current_ratio REAL,
  quick_ratio REAL,
  debt_to_assets REAL,
  assets_turn REAL,
  inv_turn REAL,
  ar_turn REAL,
  eps REAL,
  profit_to_gr REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, end_date)
);

CREATE INDEX IF NOT EXISTS idx_fina_indicator_ts_code ON fina_indicator(ts_code);
CREATE INDEX IF NOT EXISTS idx_fina_indicator_end_date ON fina_indicator(end_date);
CREATE INDEX IF NOT EXISTS idx_fina_indicator_ts_end ON fina_indicator(ts_code, end_date);
```

**Step 2: 验证 SQL**

Run: `sqlite3 data/finance.db < analyzers/fina_indicator/schema.sql`  
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analyzers/fina_indicator/schema.sql
git commit -m "feat: add fina_indicator table schema"
```

---

### Task 2: 数据库工具模块

**Files:**
- Create: `analyzers/fina_indicator/_shared/db.py`

**Step 1: 创建数据库工具**

```python
# analyzers/fina_indicator/_shared/db.py
"""财务指标数据库工具"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "finance.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_table(conn: sqlite3.Connection = None):
    if conn is None:
        conn = connect()
        should_close = True
    else:
        should_close = False
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        if should_close:
            conn.close()


def upsert_fina_indicator(conn: sqlite3.Connection, rows: list) -> int:
    if not rows:
        return 0

    base_cols = [
        "ts_code", "ann_date", "end_date",
        "roe", "roa", "grossprofit_margin", "netprofit_margin",
        "current_ratio", "quick_ratio", "debt_to_assets",
        "assets_turn", "inv_turn", "ar_turn",
        "eps", "profit_to_gr",
    ]

    unique_cols = ["ts_code", "end_date"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_rows = []
    for row in rows:
        db_row = {col: row.get(col) for col in base_cols}
        db_row["payload_json"] = json.dumps(row, ensure_ascii=False, default=str)
        db_row["source"] = "tushare"
        db_row["created_at"] = now
        db_row["updated_at"] = now
        for col in unique_cols:
            if db_row.get(col) is None:
                db_row[col] = ""
        db_rows.append(db_row)

    all_cols = list(db_rows[0].keys())
    placeholders = ", ".join(["?"] * len(all_cols))
    columns_sql = ", ".join(all_cols)
    conflict_sql = ", ".join(unique_cols)
    update_cols = [c for c in all_cols if c not in unique_cols + ["created_at"]]
    update_sql = ", ".join([f"{c} = excluded.{c}" for c in update_cols])

    sql = (
        f"INSERT INTO fina_indicator ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )
    values = [[r.get(col) for col in all_cols] for r in db_rows]

    try:
        conn.executemany(sql, values)
        conn.commit()
        return len(db_rows)
    except Exception:
        conn.rollback()
        raise


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="初始化表结构")
    args = parser.parse_args()
    if args.init:
        init_table()
        print("表结构初始化完成")
```

**Step 2: 验证导入**

Run: `python -c "from analyzers.fina_indicator._shared import db; print('OK')"`  
Expected: OK

**Step 3: Commit**

```bash
git add analyzers/fina_indicator/_shared/db.py
git commit -m "feat: add fina_indicator db utilities"
```

---

### Task 3: 获取层（fetchers）

**Files:**
- Create: `fetchers/fina_indicator.py`

**Step 1: 创建获取脚本**

```python
# fetchers/fina_indicator.py
"""从 Tushare 拉取财务指标数据"""

import os
import sys
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_indicator._shared.db import connect, upsert_fina_indicator, init_table
from fetchers.finance_basic import fetch_fina_indicator, fetch_fina_indicator_vip

load_dotenv(PROJECT_ROOT.parents[1] / ".env")

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_and_save(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    use_vip: bool = False,
) -> int:
    conn = connect()
    try:
        init_table(conn)
        if use_vip and period:
            df = fetch_fina_indicator_vip(
                period=period,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            df = fetch_fina_indicator(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
        if df is None or df.empty:
            return 0
        rows = df.to_dict("records")
        return upsert_fina_indicator(conn, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="拉取财务指标数据")
    parser.add_argument("--ts-code")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--period")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口")
    args = parser.parse_args()

    if args.vip and not args.period:
        parser.error("使用VIP接口时必须提供 --period 参数")

    count = fetch_and_save(
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        use_vip=args.vip,
    )
    print(f"保存 {count} 条记录")
```

**Step 2: 验证导入**

Run: `python -c "from fetchers.fina_indicator import fetch_and_save; print('OK')"`  
Expected: OK

**Step 3: Commit**

```bash
git add fetchers/fina_indicator.py
git commit -m "feat: add fina_indicator fetcher"
```

---

### Task 4: 查询功能

**Files:**
- Create: `analyzers/fina_indicator/search.py`

**Step 1: 创建查询模块**

```python
# analyzers/fina_indicator/search.py
"""财务指标查询功能"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_indicator._shared.db import connect


def get_fina_indicator(ts_code: str, end_date: str = None) -> Optional[Dict]:
    conn = connect()
    try:
        if end_date:
            sql = "SELECT * FROM fina_indicator WHERE ts_code = ? AND end_date = ? ORDER BY ann_date DESC LIMIT 1"
            cur = conn.execute(sql, (ts_code, end_date))
        else:
            sql = "SELECT * FROM fina_indicator WHERE ts_code = ? ORDER BY end_date DESC, ann_date DESC LIMIT 1"
            cur = conn.execute(sql, (ts_code,))
        row = cur.fetchone()
        if not row:
            return None
        result = dict(row)
        if result.get("payload_json"):
            result.update(json.loads(result["payload_json"]))
        return result
    finally:
        conn.close()


def get_fina_indicator_history(ts_code: str, start_date: str = None, end_date: str = None, limit: int = None) -> List[Dict]:
    conn = connect()
    try:
        conditions = ["ts_code = ?"]
        params = [ts_code]
        if start_date:
            conditions.append("end_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("end_date <= ?")
            params.append(end_date)
        sql = f"SELECT * FROM fina_indicator WHERE {' AND '.join(conditions)} ORDER BY end_date DESC, ann_date DESC"
        if limit:
            sql += f" LIMIT {limit}"
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        results = []
        for row in rows:
            result = dict(row)
            if result.get("payload_json"):
                result.update(json.loads(result["payload_json"]))
            results.append(result)
        return results
    finally:
        conn.close()


def get_field_value(ts_code: str, field_name: str, end_date: str = None) -> Optional[float]:
    record = get_fina_indicator(ts_code, end_date)
    if not record:
        return None
    value = record.get(field_name)
    if value is not None:
        return float(value)
    if record.get("payload_json"):
        full = json.loads(record["payload_json"])
        value = full.get(field_name)
        if value is not None:
            return float(value)
    return None
```

**Step 2: 验证导入**

Run: `python -c "from analyzers.fina_indicator.search import get_field_value; print('OK')"`  
Expected: OK

**Step 3: Commit**

```bash
git add analyzers/fina_indicator/search.py
git commit -m "feat: add fina_indicator search"
```

---

### Task 5: CLI 入口

**Files:**
- Create: `analyzers/fina_indicator/pipeline.py`

**Step 1: 创建 CLI**

```python
# analyzers/fina_indicator/pipeline.py
"""财务指标流程入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_indicator.search import get_fina_indicator, get_fina_indicator_history, get_field_value
from fetchers.fina_indicator import fetch_and_save


def run_fetch(**kwargs):
    count = fetch_and_save(**kwargs)
    print(f"保存 {count} 条记录")
    return count


def run_query(ts_code: str, field: str = None, end_date: str = None):
    if field:
        value = get_field_value(ts_code, field, end_date)
        print("未找到数据" if value is None else f"{ts_code} {field} = {value}")
    else:
        record = get_fina_indicator(ts_code, end_date)
        print("未找到数据" if not record else record)


def run_history(ts_code: str, limit: int = 4):
    records = get_fina_indicator_history(ts_code, limit=limit)
    for r in records:
        print(r.get("end_date"), r.get("roe"), r.get("netprofit_margin"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="财务指标查询")
    subparsers = parser.add_subparsers(dest="command")

    p_fetch = subparsers.add_parser("fetch", help="拉取数据")
    p_fetch.add_argument("--ts-code")
    p_fetch.add_argument("--start-date")
    p_fetch.add_argument("--end-date")
    p_fetch.add_argument("--period")
    p_fetch.add_argument("--vip", action="store_true")

    p_query = subparsers.add_parser("query", help="查询数据")
    p_query.add_argument("--ts-code", required=True)
    p_query.add_argument("--field")
    p_query.add_argument("--end-date")

    p_history = subparsers.add_parser("history", help="查询历史")
    p_history.add_argument("--ts-code", required=True)
    p_history.add_argument("--limit", type=int, default=4)

    args = parser.parse_args()
    if args.command == "fetch":
        if args.vip and not args.period:
            parser.error("使用VIP接口时必须提供 --period 参数")
        run_fetch(
            ts_code=args.ts_code,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            use_vip=args.vip,
        )
    elif args.command == "query":
        run_query(args.ts_code, args.field, args.end_date)
    elif args.command == "history":
        run_history(args.ts_code, args.limit)
```

**Step 2: 验证 CLI**

Run: `python -m analyzers.fina_indicator.pipeline --help`  
Expected: 显示 fetch/query/history

**Step 3: Commit**

```bash
git add analyzers/fina_indicator/pipeline.py
git commit -m "feat: add fina_indicator pipeline"
```

---

### Task 6: VIP 批量刷新（按区间拆分季度）

**Files:**
- Create: `fetchers/fina_indicator_vip_batch.py`

**Step 1: 创建批量脚本**

```python
# fetchers/fina_indicator_vip_batch.py
"""VIP 批量刷新财务指标（按季度）"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.fina_indicator import fetch_and_save

DATA_DIR = PROJECT_ROOT / "data"
PROGRESS_FILE = DATA_DIR / "fina_indicator_vip_progress.json"
PROGRESS_LOG = DATA_DIR / "fina_indicator_vip_progress.log"
SAVE_EVERY = 10


def quarter_ends_between(start_date: str, end_date: str) -> list[str]:
    # 生成区间内所有季度末
    def to_dt(s):
        return datetime.strptime(s, "%Y%m%d")
    def quarter_end(dt):
        if dt.month <= 3:
            return datetime(dt.year, 3, 31)
        if dt.month <= 6:
            return datetime(dt.year, 6, 30)
        if dt.month <= 9:
            return datetime(dt.year, 9, 30)
        return datetime(dt.year, 12, 31)
    start = quarter_end(to_dt(start_date))
    end = quarter_end(to_dt(end_date))
    periods = []
    cur = start
    while cur <= end:
        periods.append(cur.strftime("%Y%m%d"))
        if cur.month == 3:
            cur = datetime(cur.year, 6, 30)
        elif cur.month == 6:
            cur = datetime(cur.year, 9, 30)
        elif cur.month == 9:
            cur = datetime(cur.year, 12, 31)
        else:
            cur = datetime(cur.year + 1, 3, 31)
    return periods


def load_progress() -> set:
    processed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        processed.update(data.get("processed", []))
    if PROGRESS_LOG.exists():
        for line in PROGRESS_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                processed.add(line)
    return processed


def append_progress(period: str):
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{period}\n")


def save_progress(processed: set):
    data = {"processed": list(processed), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def run_vip(start_date: str, end_date: str, delay: float = 1.0, resume: bool = True):
    periods = quarter_ends_between(start_date, end_date)
    processed = load_progress() if resume else set()
    remaining = [p for p in periods if p not in processed]
    print(f"共 {len(periods)} 个季度，剩余 {len(remaining)} 个待拉取")
    for idx, period in enumerate(remaining, 1):
        print(f"[{idx}/{len(remaining)}] 拉取 {period}")
        try:
            count = fetch_and_save(period=period, use_vip=True)
            print(f"  ✓ 保存 {count} 条")
            processed.add(period)
            append_progress(period)
        except Exception as e:
            print(f"  ✗ 失败：{e}")
            processed.add(period)
            append_progress(period)
        if idx % SAVE_EVERY == 0:
            save_progress(processed)
        time.sleep(delay)
    save_progress(processed)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VIP 批量刷新财务指标")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    run_vip(args.start_date, args.end_date, args.delay, resume=not args.no_resume)
```

**Step 2: 验证脚本**

Run: `python fetchers/fina_indicator_vip_batch.py --start-date 20240331 --end-date 20240630 --no-resume`  
Expected: 拉取 20240331 和 20240630

**Step 3: Commit**

```bash
git add fetchers/fina_indicator_vip_batch.py
git commit -m "feat: add fina_indicator vip batch fetcher"
```

---

### Task 7: 初始化与样例拉取

**Step 1: 初始化表**

Run: `python -m analyzers.fina_indicator._shared.db --init`  
Expected: 输出“表结构初始化完成”

**Step 2: 单公司拉取**

Run: `python -m analyzers.fina_indicator.pipeline fetch --ts-code 000001.SZ --start-date 20240331 --end-date 20241231`  
Expected: 输出保存记录数

**Step 3: Commit**

```bash
git commit -m "test: verify fina_indicator fetch and query"
```

---

### Task 8: 文档引用补充（最后做）

**Files:**
- Modify: `SKILLS.md`

**Step 1: 增加字段清单引用**

在财务指标功能介绍末尾添加：

```markdown
### 字段清单参考

- `docs/financial-indicators.md`: 财务指标字段完整清单（字段名 + 中文含义）
```

**Step 2: Commit**

```bash
git add SKILLS.md
git commit -m "docs: add financial indicator fields reference"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-04-fina-indicator-implementation.md`. Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration  
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints  

Which approach?
