# 资产负债表功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现资产负债表数据的获取、存储、查询和基础财务分析功能，支持用户查询如"xx公司的存货如何"等基础财务问题。

**Architecture:** 遵循三层架构（fetchers → analyzers → interpreters），数据存储采用"基础列+payload_json"方案，提取20个常用字段作为基础列，其余字段存入JSON。查询时优先使用基础列，需要完整字段时解析JSON。

**Tech Stack:** Python, SQLite, pandas, tushare, json

---

## Task 1: 创建数据库表结构

**Files:**
- Create: `analyzers/balancesheet/schema.sql`

**Step 1: 创建表结构文件**

```sql
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS balancesheet (
  ts_code TEXT NOT NULL,
  ann_date TEXT,
  f_ann_date TEXT,
  end_date TEXT NOT NULL,
  report_type TEXT,
  comp_type TEXT,
  end_type TEXT,
  total_share REAL,
  money_cap REAL,
  accounts_receiv REAL,
  inventories REAL,
  total_cur_assets REAL,
  fix_assets REAL,
  total_assets REAL,
  st_borr REAL,
  acct_payable REAL,
  total_cur_liab REAL,
  total_liab REAL,
  undistr_porfit REAL,
  total_hldr_eqy_exc_min_int REAL,
  source TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(ts_code, ann_date, end_date, report_type)
);

CREATE INDEX IF NOT EXISTS idx_balancesheet_ts_code ON balancesheet(ts_code);
CREATE INDEX IF NOT EXISTS idx_balancesheet_end_date ON balancesheet(end_date);
CREATE INDEX IF NOT EXISTS idx_balancesheet_ts_end ON balancesheet(ts_code, end_date);
```

**Step 2: 验证SQL语法**

Run: `sqlite3 data/finance.db < analyzers/balancesheet/schema.sql`
Expected: 无错误输出

**Step 3: Commit**

```bash
git add analyzers/balancesheet/schema.sql
git commit -m "feat: add balancesheet table schema"
```

---

## Task 2: 创建数据库工具模块

**Files:**
- Create: `analyzers/balancesheet/_shared/db.py`

**Step 1: 创建数据库工具文件**

```python
# analyzers/balancesheet/_shared/db.py
"""资产负债表数据库工具"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "finance.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """连接数据库"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_table(conn: sqlite3.Connection = None):
    """初始化表结构"""
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


def upsert_balancesheet(conn: sqlite3.Connection, rows: list) -> int:
    """批量插入/更新资产负债表数据
    
    Args:
        conn: 数据库连接
        rows: 数据行列表，每行包含所有字段
        
    Returns:
        插入/更新的行数
    """
    if not rows:
        return 0
    
    # 基础列（常用字段）
    base_cols = [
        'ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type', 
        'comp_type', 'end_type', 'total_share', 'money_cap', 
        'accounts_receiv', 'inventories', 'total_cur_assets', 'fix_assets',
        'total_assets', 'st_borr', 'acct_payable', 'total_cur_liab',
        'total_liab', 'undistr_porfit', 'total_hldr_eqy_exc_min_int'
    ]
    
    # 唯一键
    unique_cols = ['ts_code', 'ann_date', 'end_date', 'report_type']
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 准备数据
    db_rows = []
    for row in rows:
        db_row = {}
        # 提取基础列
        for col in base_cols:
            db_row[col] = row.get(col)
        
        # 存储完整JSON
        db_row['payload_json'] = json.dumps(row, ensure_ascii=False, default=str)
        db_row['source'] = 'tushare'
        db_row['created_at'] = now
        db_row['updated_at'] = now
        
        # 处理唯一键中的NULL值
        for col in unique_cols:
            if db_row.get(col) is None:
                db_row[col] = ''
        
        db_rows.append(db_row)
    
    # 构建SQL
    all_cols = list(db_rows[0].keys())
    placeholders = ", ".join(["?"] * len(all_cols))
    columns_sql = ", ".join(all_cols)
    conflict_sql = ", ".join(unique_cols)
    update_cols = [c for c in all_cols if c not in unique_cols + ['created_at']]
    update_sql = ", ".join([f"{c} = excluded.{c}" for c in update_cols])
    
    sql = (
        f"INSERT INTO balancesheet ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )
    
    values = [[r.get(col) for col in all_cols] for r in db_rows]
    
    try:
        conn.executemany(sql, values)
        conn.commit()
        return len(db_rows)
    except Exception as e:
        conn.rollback()
        raise


if __name__ == "__main__":
    # CLI入口：初始化表
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="初始化表结构")
    args = parser.parse_args()
    
    if args.init:
        init_table()
        print("表结构初始化完成")
```

**Step 2: 测试导入**

Run: `python -c "from analyzers.balancesheet._shared import db; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add analyzers/balancesheet/_shared/db.py
git commit -m "feat: add balancesheet database utilities"
```

---

## Task 3: 实现数据获取模块

**Files:**
- Create: `fetchers/balancesheet.py`

**Step 1: 创建数据获取文件**

```python
# fetchers/balancesheet.py
"""从 Tushare 拉取资产负债表数据"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet._shared.db import connect, upsert_balancesheet, init_table
from fetchers.finance_basic import fetch_balancesheet, fetch_balancesheet_vip

load_dotenv(PROJECT_ROOT.parents[1] / ".env")

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    """获取 Tushare API 实例"""
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
    report_type: str = None,
    comp_type: str = None,
    use_vip: bool = False,
) -> int:
    """
    拉取资产负债表数据并保存到数据库
    
    Args:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 开始日期
        end_date: 结束日期
        period: 报告期（YYYYMMDD）
        report_type: 报表类型
        comp_type: 公司类型
        use_vip: 是否使用VIP接口（全量拉取）
        
    Returns:
        保存的记录数
    """
    # 确保表已创建
    conn = connect()
    try:
        init_table(conn)
        
        # 调用API
        if use_vip and period:
            df = fetch_balancesheet_vip(
                period=period,
                report_type=report_type,
                comp_type=comp_type
            )
        else:
            df = fetch_balancesheet(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                report_type=report_type,
                comp_type=comp_type
            )
        
        if df is None or df.empty:
            return 0
        
        # 转换为字典列表
        rows = df.to_dict('records')
        
        # 入库
        count = upsert_balancesheet(conn, rows)
        return count
        
    except Exception as e:
        print(f"拉取失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="拉取资产负债表数据")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--start-date", help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", help="结束日期 YYYYMMDD")
    parser.add_argument("--period", help="报告期 YYYYMMDD")
    parser.add_argument("--report-type", help="报表类型")
    parser.add_argument("--comp-type", help="公司类型")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口")
    
    args = parser.parse_args()
    
    count = fetch_and_save(
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        report_type=args.report_type,
        comp_type=args.comp_type,
        use_vip=args.vip
    )
    
    print(f"保存 {count} 条记录")
```

**Step 2: 测试单公司拉取**

Run: `python fetchers/balancesheet.py --ts-code 000001.SZ --start-date 20240101 --end-date 20241231`
Expected: 输出保存的记录数

**Step 3: Commit**

```bash
git add fetchers/balancesheet.py
git commit -m "feat: add balancesheet fetcher"
```

---

## Task 4: 实现查询功能

**Files:**
- Create: `analyzers/balancesheet/search.py`

**Step 1: 创建查询模块**

```python
# analyzers/balancesheet/search.py
"""资产负债表查询功能"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet._shared.db import connect


def get_balancesheet(
    ts_code: str,
    end_date: str = None,
    report_type: str = "1"
) -> Optional[Dict]:
    """
    查询单条资产负债表记录
    
    Args:
        ts_code: 股票代码
        end_date: 报告期 YYYYMMDD，默认最新
        report_type: 报表类型，默认1（合并报表）
        
    Returns:
        记录字典，包含基础列和完整字段
    """
    conn = connect()
    try:
        if end_date:
            sql = """
                SELECT * FROM balancesheet 
                WHERE ts_code = ? AND end_date = ? AND report_type = ?
                ORDER BY ann_date DESC
                LIMIT 1
            """
            cur = conn.execute(sql, (ts_code, end_date, report_type))
        else:
            sql = """
                SELECT * FROM balancesheet 
                WHERE ts_code = ? AND report_type = ?
                ORDER BY end_date DESC, ann_date DESC
                LIMIT 1
            """
            cur = conn.execute(sql, (ts_code, report_type))
        
        row = cur.fetchone()
        if not row:
            return None
        
        result = dict(row)
        # 解析完整字段
        if result.get('payload_json'):
            full_data = json.loads(result['payload_json'])
            result.update(full_data)
        
        return result
    finally:
        conn.close()


def get_balancesheet_history(
    ts_code: str,
    start_date: str = None,
    end_date: str = None,
    report_type: str = "1",
    limit: int = None
) -> List[Dict]:
    """
    查询历史资产负债表记录
    
    Args:
        ts_code: 股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        report_type: 报表类型
        limit: 限制返回数量（如4表示最近4个季度）
        
    Returns:
        记录列表，按end_date降序
    """
    conn = connect()
    try:
        conditions = ["ts_code = ?", "report_type = ?"]
        params = [ts_code, report_type]
        
        if start_date:
            conditions.append("end_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("end_date <= ?")
            params.append(end_date)
        
        sql = f"""
            SELECT * FROM balancesheet 
            WHERE {' AND '.join(conditions)}
            ORDER BY end_date DESC, ann_date DESC
        """
        
        if limit:
            sql += f" LIMIT {limit}"
        
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            result = dict(row)
            # 解析完整字段
            if result.get('payload_json'):
                full_data = json.loads(result['payload_json'])
                result.update(full_data)
            results.append(result)
        
        return results
    finally:
        conn.close()


def get_field_value(
    ts_code: str,
    field_name: str,
    end_date: str = None,
    report_type: str = "1"
) -> Optional[float]:
    """
    查询特定字段值
    
    Args:
        ts_code: 股票代码
        field_name: 字段名（如'inventories'）
        end_date: 报告期，默认最新
        report_type: 报表类型
        
    Returns:
        字段值（float），不存在返回None
    """
    record = get_balancesheet(ts_code, end_date, report_type)
    if not record:
        return None
    
    # 先查基础列
    if field_name in record:
        value = record[field_name]
        if value is not None:
            return float(value)
    
    # 再从payload_json中查找
    if 'payload_json' in record:
        full_data = json.loads(record['payload_json'])
        value = full_data.get(field_name)
        if value is not None:
            return float(value)
    
    return None


def search_by_field(
    field_name: str,
    end_date: str,
    report_type: str = "1",
    comp_type: str = None,
    limit: int = 100,
    order: str = "DESC"
) -> List[Dict]:
    """
    跨公司查询特定字段
    
    Args:
        field_name: 字段名
        end_date: 报告期
        report_type: 报表类型
        comp_type: 公司类型过滤
        limit: 返回数量限制
        order: 排序方向（DESC/ASC）
        
    Returns:
        列表，每项包含ts_code和字段值
    """
    conn = connect()
    try:
        # 先检查是否是基础列
        base_cols = [
            'total_share', 'money_cap', 'accounts_receiv', 'inventories',
            'total_cur_assets', 'fix_assets', 'total_assets', 'st_borr',
            'acct_payable', 'total_cur_liab', 'total_liab', 'undistr_porfit',
            'total_hldr_eqy_exc_min_int'
        ]
        
        conditions = ["end_date = ?", "report_type = ?"]
        params = [end_date, report_type]
        
        if comp_type:
            conditions.append("comp_type = ?")
            params.append(comp_type)
        
        if field_name in base_cols:
            # 直接从基础列查询
            sql = f"""
                SELECT ts_code, {field_name} as value
                FROM balancesheet
                WHERE {' AND '.join(conditions)} AND {field_name} IS NOT NULL
                ORDER BY {field_name} {order}
                LIMIT ?
            """
            params.append(limit)
            cur = conn.execute(sql, params)
        else:
            # 需要解析JSON（性能较差，但支持所有字段）
            sql = f"""
                SELECT ts_code, payload_json
                FROM balancesheet
                WHERE {' AND '.join(conditions)}
                LIMIT ?
            """
            params.append(limit * 2)  # 多查一些，因为可能有些记录没有该字段
            cur = conn.execute(sql, params)
            
            # 解析并过滤
            results = []
            for row in cur.fetchall():
                try:
                    data = json.loads(row['payload_json'])
                    value = data.get(field_name)
                    if value is not None:
                        results.append({
                            'ts_code': row['ts_code'],
                            'value': float(value)
                        })
                except:
                    continue
            
            # 排序
            results.sort(key=lambda x: x['value'], reverse=(order == "DESC"))
            return results[:limit]
        
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
```

**Step 2: 测试查询功能**

Run: `python -c "from analyzers.balancesheet.search import get_field_value; print(get_field_value('000001.SZ', 'inventories'))"`
Expected: 输出存货值或None

**Step 3: Commit**

```bash
git add analyzers/balancesheet/search.py
git commit -m "feat: add balancesheet search functions"
```

---

## Task 5: 实现自动拉取逻辑

**Files:**
- Modify: `analyzers/balancesheet/search.py` (添加ensure_data函数)

**Step 1: 添加自动拉取函数**

在 `search.py` 文件末尾添加：

```python
def ensure_data(
    ts_code: str,
    end_date: str = None,
    years: int = 1,
    report_type: str = "1"
) -> bool:
    """
    确保有足够的历史数据，不足时自动拉取
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期，默认当前日期
        years: 需要的数据年数
        report_type: 报表类型
        
    Returns:
        是否成功获取数据
    """
    from datetime import datetime, timedelta
    from fetchers.balancesheet import fetch_and_save
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 检查现有数据
    existing = get_balancesheet_history(
        ts_code=ts_code,
        end_date=end_date,
        report_type=report_type,
        limit=years * 4 + 4  # 多查一些确保
    )
    
    # 计算需要的日期范围（N+1年，确保有足够数据计算同比）
    need_years = years + 1
    start_date_dt = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=need_years * 365)
    start_date = start_date_dt.strftime("%Y%m%d")
    
    # 如果数据不足，拉取
    if len(existing) < years * 4:
        print(f"数据不足（{len(existing)}条），拉取 {start_date} 至 {end_date} 的数据...")
        try:
            count = fetch_and_save(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type
            )
            print(f"拉取完成，新增 {count} 条记录")
            return True
        except Exception as e:
            print(f"拉取失败: {e}")
            return False
    
    return True
```

**Step 2: 修改get_field_value使用ensure_data**

修改 `get_field_value` 函数，在查询前调用 `ensure_data`：

```python
def get_field_value(
    ts_code: str,
    field_name: str,
    end_date: str = None,
    report_type: str = "1",
    auto_fetch: bool = True
) -> Optional[float]:
    """查询特定字段值，支持自动拉取"""
    if auto_fetch:
        ensure_data(ts_code, end_date, years=1, report_type=report_type)
    
    record = get_balancesheet(ts_code, end_date, report_type)
    # ... 其余代码不变
```

**Step 3: 测试自动拉取**

Run: `python -c "from analyzers.balancesheet.search import get_field_value; print(get_field_value('000002.SZ', 'inventories'))"`
Expected: 如果数据库无数据，会自动拉取

**Step 4: Commit**

```bash
git add analyzers/balancesheet/search.py
git commit -m "feat: add auto-fetch logic for balancesheet"
```

---

## Task 6: 创建CLI入口

**Files:**
- Create: `analyzers/balancesheet/pipeline.py`

**Step 1: 创建CLI入口**

```python
# analyzers/balancesheet/pipeline.py
"""资产负债表分析流程入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet.search import (
    get_balancesheet,
    get_balancesheet_history,
    get_field_value,
    search_by_field,
    ensure_data
)
from fetchers.balancesheet import fetch_and_save


def run_fetch(**kwargs):
    """拉取数据"""
    count = fetch_and_save(**kwargs)
    print(f"保存 {count} 条记录")
    return count


def run_query(ts_code: str, field: str = None, end_date: str = None):
    """查询数据"""
    if field:
        value = get_field_value(ts_code, field, end_date)
        if value is not None:
            print(f"{ts_code} {field} = {value:,.0f}")
        else:
            print(f"未找到数据")
    else:
        record = get_balancesheet(ts_code, end_date)
        if record:
            print(f"报告期: {record.get('end_date')}")
            print(f"总资产: {record.get('total_assets', 0):,.0f}")
            print(f"存货: {record.get('inventories', 0):,.0f}")
            print(f"应收账款: {record.get('accounts_receiv', 0):,.0f}")
        else:
            print("未找到数据")


def run_history(ts_code: str, limit: int = 4):
    """查询历史数据"""
    records = get_balancesheet_history(ts_code, limit=limit)
    print(f"\n{ts_code} 最近{len(records)}期数据:")
    print("-" * 60)
    for r in records:
        print(f"{r['end_date']}: 总资产={r.get('total_assets', 0):,.0f}, "
              f"存货={r.get('inventories', 0):,.0f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="资产负债表分析")
    subparsers = parser.add_subparsers(dest="command")
    
    # fetch命令
    p_fetch = subparsers.add_parser("fetch", help="拉取数据")
    p_fetch.add_argument("--ts-code", required=True)
    p_fetch.add_argument("--start-date")
    p_fetch.add_argument("--end-date")
    p_fetch.add_argument("--period")
    p_fetch.add_argument("--report-type", default="1")
    
    # query命令
    p_query = subparsers.add_parser("query", help="查询数据")
    p_query.add_argument("--ts-code", required=True)
    p_query.add_argument("--field")
    p_query.add_argument("--end-date")
    
    # history命令
    p_history = subparsers.add_parser("history", help="查询历史")
    p_history.add_argument("--ts-code", required=True)
    p_history.add_argument("--limit", type=int, default=4)
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        run_fetch(
            ts_code=args.ts_code,
            start_date=args.start_date,
            end_date=args.end_date,
            period=args.period,
            report_type=args.report_type
        )
    elif args.command == "query":
        run_query(args.ts_code, args.field, args.end_date)
    elif args.command == "history":
        run_history(args.ts_code, args.limit)
```

**Step 2: 测试CLI**

Run: `python -m analyzers.balancesheet.pipeline query --ts-code 000001.SZ --field inventories`
Expected: 输出存货值

**Step 3: Commit**

```bash
git add analyzers/balancesheet/pipeline.py
git commit -m "feat: add balancesheet CLI pipeline"
```

---

## Task 7: 创建财务分析参考文档

**Files:**
- Create: `analyzers/financial_analysis/reference.md`

**Step 1: 创建参考文档**

```markdown
# 财务分析参考文档

## 基础指标定义

### 资产类指标
- **货币资金** (`money_cap`): 公司持有的现金及银行存款
- **应收账款** (`accounts_receiv`): 公司因销售商品、提供服务等应收取的款项
- **存货** (`inventories`): 公司持有的商品、在产品、原材料等
- **流动资产合计** (`total_cur_assets`): 一年内可变现的资产总和
- **固定资产** (`fix_assets`): 公司长期使用的有形资产
- **总资产** (`total_assets`): 公司拥有的全部资产

### 负债类指标
- **短期借款** (`st_borr`): 一年内需要偿还的借款
- **应付账款** (`acct_payable`): 公司因采购商品、接受服务等应支付的款项
- **流动负债合计** (`total_cur_liab`): 一年内需要偿还的负债总和
- **总负债** (`total_liab`): 公司需要偿还的全部负债

### 权益类指标
- **未分配利润** (`undistr_porfit`): 公司累计未分配的利润
- **股东权益合计** (`total_hldr_eqy_exc_min_int`): 股东拥有的净资产

## 常用财务比率

### 偿债能力指标
- **流动比率** = 流动资产合计 / 流动负债合计
  - 标准值: > 2 较好，< 1 有风险
- **速动比率** = (流动资产合计 - 存货) / 流动负债合计
  - 标准值: > 1 较好
- **资产负债率** = 总负债 / 总资产
  - 标准值: < 60% 较好，> 80% 风险较高

### 资产结构指标
- **存货占比** = 存货 / 总资产
- **应收账款占比** = 应收账款 / 总资产
- **固定资产占比** = 固定资产 / 总资产

## 常见问题分析模板

### "xx公司的存货如何"
1. **查询数据**: 获取存货金额 (`inventories`)
2. **计算占比**: 存货 / 总资产
3. **趋势分析**: 对比最近4个季度的存货变化
4. **风险评估**: 
   - 存货占比过高（>30%）可能积压
   - 存货快速增长但收入未增长需警惕

### "xx公司的偿债能力"
1. **查询数据**: 流动资产、流动负债、总负债、总资产
2. **计算比率**: 流动比率、速动比率、资产负债率
3. **评估**: 对比行业标准值

### "xx公司的资产结构"
1. **查询数据**: 各类资产金额
2. **计算占比**: 各类资产 / 总资产
3. **分析**: 资产配置是否合理

## 数据获取方法

### 查询单字段
```python
from analyzers.balancesheet.search import get_field_value
value = get_field_value('000001.SZ', 'inventories')
```

### 查询完整记录
```python
from analyzers.balancesheet.search import get_balancesheet
record = get_balancesheet('000001.SZ', end_date='20241231')
```

### 查询历史数据
```python
from analyzers.balancesheet.search import get_balancesheet_history
records = get_balancesheet_history('000001.SZ', limit=4)
```

### 计算同比/环比
```python
# 获取两年数据
records = get_balancesheet_history('000001.SZ', limit=8)

# 计算同比（去年同期）
if len(records) >= 4:
    current = records[0]['inventories']
    last_year = records[4]['inventories']
    yoy_growth = (current - last_year) / last_year * 100
```

## 注意事项

1. **公司类型差异**: 银行/保险/证券的资产负债表结构不同，查询时注意 `comp_type`
2. **报告类型**: 默认使用 `report_type=1`（合并报表），其他类型需明确指定
3. **数据完整性**: 某些字段可能为空（如银行没有"存货"），需要容错处理
4. **时间范围**: 计算同比需要至少4个季度数据，建议拉取N+1年数据
```

**Step 2: 验证文档格式**

Run: `cat analyzers/financial_analysis/reference.md | head -20`
Expected: 正常显示markdown内容

**Step 3: Commit**

```bash
git add analyzers/financial_analysis/reference.md
git commit -m "feat: add financial analysis reference"
```

---

## Task 8: 初始化表结构

**Step 1: 执行初始化**

Run: `python -m analyzers.balancesheet._shared.db --init`
Expected: 输出"表结构初始化完成"

**Step 2: 验证表创建**

Run: `sqlite3 data/finance.db "SELECT name FROM sqlite_master WHERE type='table' AND name='balancesheet';"`
Expected: 输出 `balancesheet`

**Step 3: Commit**

```bash
git add data/finance.db
git commit -m "chore: initialize balancesheet table"
```

---

## Task 9: 端到端测试

**Step 1: 测试完整流程**

```bash
# 1. 拉取数据
python -m analyzers.balancesheet.pipeline fetch --ts-code 000001.SZ --start-date 20240101 --end-date 20241231

# 2. 查询数据
python -m analyzers.balancesheet.pipeline query --ts-code 000001.SZ --field inventories

# 3. 查询历史
python -m analyzers.balancesheet.pipeline history --ts-code 000001.SZ --limit 4
```

Expected: 所有命令成功执行

**Step 2: Commit**

```bash
git commit -m "test: verify end-to-end balancesheet workflow"
```

---

## 完成检查清单

- [ ] 数据库表结构创建完成
- [ ] 数据获取功能正常
- [ ] 查询功能正常
- [ ] 自动拉取逻辑正常
- [ ] CLI入口可用
- [ ] 参考文档完整
- [ ] 端到端测试通过
