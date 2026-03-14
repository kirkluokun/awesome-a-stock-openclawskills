# 券商研报搜索与解析 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现券商研报的搜索、下载、PDF解析和观点提取功能

**Architecture:** 三层架构 - fetchers 拉取元数据存DB，analyzers 搜索和下载，interpreters 用 Gemini 解析 PDF 提取观点

**Tech Stack:** Python, SQLite, Tushare API, pdfplumber, google-generativeai (Gemini 2.5 Flash)

---

## Task 1: 数据库表结构

**Files:**
- Create: `analyzers/research/schema.sql`
- Modify: `analyzers/research/_shared/db.py`

**Step 1: 创建 schema.sql**

```sql
-- analyzers/research/schema.sql
CREATE TABLE IF NOT EXISTS research_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    ts_code TEXT,
    name TEXT,
    title TEXT NOT NULL,
    abstr TEXT,
    report_type TEXT,
    author TEXT,
    inst_csname TEXT,
    ind_name TEXT,
    url TEXT NOT NULL,
    local_path TEXT,
    parsed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url)
);

CREATE INDEX IF NOT EXISTS idx_rr_ts_code ON research_report(ts_code);
CREATE INDEX IF NOT EXISTS idx_rr_trade_date ON research_report(trade_date);
CREATE INDEX IF NOT EXISTS idx_rr_ind_name ON research_report(ind_name);
CREATE INDEX IF NOT EXISTS idx_rr_inst_csname ON research_report(inst_csname);
```

**Step 2: 创建目录结构和 db.py**

```bash
mkdir -p analyzers/research/_shared
touch analyzers/research/__init__.py
touch analyzers/research/_shared/__init__.py
```

```python
# analyzers/research/_shared/db.py
"""研报数据库工具"""

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
    """初始化研报表"""
    conn = connect()
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    conn.close()


def upsert_reports(rows: list[dict]) -> int:
    """批量插入研报元数据，返回插入条数"""
    if not rows:
        return 0
    conn = connect()
    sql = """
        INSERT INTO research_report 
        (trade_date, ts_code, name, title, abstr, report_type, author, inst_csname, ind_name, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            trade_date = excluded.trade_date,
            ts_code = excluded.ts_code,
            name = excluded.name,
            title = excluded.title,
            abstr = excluded.abstr,
            report_type = excluded.report_type,
            author = excluded.author,
            inst_csname = excluded.inst_csname,
            ind_name = excluded.ind_name
    """
    values = [
        (r.get("trade_date"), r.get("ts_code"), r.get("name"), r.get("title"),
         r.get("abstr"), r.get("report_type"), r.get("author"), 
         r.get("inst_csname"), r.get("ind_name"), r.get("url"))
        for r in rows
    ]
    conn.executemany(sql, values)
    conn.commit()
    count = conn.total_changes
    conn.close()
    return count


def update_local_path(report_id: int, local_path: str):
    """更新本地路径"""
    conn = connect()
    conn.execute(
        "UPDATE research_report SET local_path = ? WHERE id = ?",
        (local_path, report_id)
    )
    conn.commit()
    conn.close()


def update_parsed_at(report_id: int, parsed_at: str):
    """更新解析时间"""
    conn = connect()
    conn.execute(
        "UPDATE research_report SET parsed_at = ? WHERE id = ?",
        (parsed_at, report_id)
    )
    conn.commit()
    conn.close()
```

**Step 3: 初始化表**

```bash
cd openclaw-skills/stock-research-group
python -c "from analyzers.research._shared.db import init_table; init_table()"
```

**Step 4: Commit**

```bash
git add analyzers/research/
git commit -m "feat(research): 添加研报表结构和数据库工具"
```

---

## Task 2: Fetcher - 拉取研报元数据

**Files:**
- Create: `fetchers/research_report.py`

**Step 1: 创建 fetcher**

```python
# fetchers/research_report.py
"""从 Tushare 拉取券商研报元数据"""

import os
import sys
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.research._shared.db import upsert_reports

load_dotenv(PROJECT_ROOT.parent / ".env")

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")


def get_pro():
    ts.set_token(TUSHARE_TOKEN)
    return ts.pro_api()


def fetch_research_report(
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
    ts_code: str = None,
    ind_name: str = None,
    inst_csname: str = None,
    report_type: str = None,
    limit: int = 1000,
) -> int:
    """
    从 Tushare 拉取研报元数据，存入 DB
    
    Args:
        trade_date: 单日 YYYYMMDD
        start_date/end_date: 日期范围
        ts_code: 股票代码
        ind_name: 行业名称
        inst_csname: 券商名称
        report_type: 个股研报/行业研报
        limit: 单次最大条数
    
    Returns:
        新增/更新条数
    """
    pro = get_pro()
    
    params = {}
    if trade_date:
        params["trade_date"] = trade_date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if ts_code:
        params["ts_code"] = ts_code
    if ind_name:
        params["ind_name"] = ind_name
    if inst_csname:
        params["inst_csname"] = inst_csname
    if report_type:
        params["report_type"] = report_type
    
    df = pro.research_report(
        **params,
        fields="trade_date,ts_code,name,title,abstr,report_type,author,inst_csname,ind_name,url"
    )
    
    if df.empty:
        return 0
    
    rows = df.to_dict("records")
    return upsert_reports(rows)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="拉取券商研报")
    parser.add_argument("--date", help="单日 YYYYMMDD")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--ind", help="行业名称")
    parser.add_argument("--inst", help="券商名称")
    args = parser.parse_args()
    
    count = fetch_research_report(
        trade_date=args.date,
        start_date=args.start,
        end_date=args.end,
        ts_code=args.ts_code,
        ind_name=args.ind,
        inst_csname=args.inst,
    )
    print(f"已入库 {count} 条研报")
```

**Step 2: 测试拉取**

```bash
python fetchers/research_report.py --date 20260203
```

**Step 3: Commit**

```bash
git add fetchers/research_report.py
git commit -m "feat(research): 添加研报元数据拉取 fetcher"
```

---

## Task 3: Analyzer - 搜索报告

**Files:**
- Create: `analyzers/research/search.py`

**Step 1: 创建 search.py**

```python
# analyzers/research/search.py
"""搜索研报"""

from ._shared.db import connect


def search_reports(
    ts_code: str = None,
    ind_name: str = None,
    keyword: str = None,
    inst_csname: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
) -> list[dict]:
    """
    从 DB 搜索研报
    
    Args:
        ts_code: 股票代码
        ind_name: 行业名称（模糊匹配）
        keyword: 标题关键词（模糊匹配）
        inst_csname: 券商名称（模糊匹配）
        start_date/end_date: 日期范围
        limit: 返回条数上限
    
    Returns:
        研报元数据列表
    """
    conn = connect()
    
    conditions = []
    params = []
    
    if ts_code:
        conditions.append("ts_code = ?")
        params.append(ts_code)
    if ind_name:
        conditions.append("ind_name LIKE ?")
        params.append(f"%{ind_name}%")
    if keyword:
        conditions.append("title LIKE ?")
        params.append(f"%{keyword}%")
    if inst_csname:
        conditions.append("inst_csname LIKE ?")
        params.append(f"%{inst_csname}%")
    if start_date:
        conditions.append("trade_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("trade_date <= ?")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT id, trade_date, ts_code, name, title, abstr, report_type,
               author, inst_csname, ind_name, url, local_path, parsed_at
        FROM research_report
        WHERE {where_clause}
        ORDER BY trade_date DESC
        LIMIT ?
    """
    params.append(limit)
    
    cur = conn.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    return rows


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="搜索研报")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--ind", help="行业名称")
    parser.add_argument("--keyword", help="标题关键词")
    parser.add_argument("--inst", help="券商名称")
    parser.add_argument("--start", help="开始日期")
    parser.add_argument("--end", help="结束日期")
    parser.add_argument("--limit", type=int, default=20, help="返回条数")
    args = parser.parse_args()
    
    results = search_reports(
        ts_code=args.ts_code,
        ind_name=args.ind,
        keyword=args.keyword,
        inst_csname=args.inst,
        start_date=args.start,
        end_date=args.end,
        limit=args.limit,
    )
    
    for r in results:
        print(f"[{r['trade_date']}] {r['title'][:50]}...")
    print(f"\n共 {len(results)} 条")
```

**Step 2: 测试搜索**

```bash
python -m analyzers.research.search --keyword "茅台" --limit 5
```

**Step 3: Commit**

```bash
git add analyzers/research/search.py
git commit -m "feat(research): 添加研报搜索功能"
```

---

## Task 4: Analyzer - 下载 PDF

**Files:**
- Create: `analyzers/research/download.py`

**Step 1: 创建 download.py**

```python
# analyzers/research/download.py
"""下载研报 PDF"""

import os
import re
import time
from pathlib import Path

import requests

from ._shared.db import connect, update_local_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "reports"


def sanitize_filename(name: str) -> str:
    """清理文件名"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)[:100]


def download_report(report_id: int, force: bool = False) -> str | None:
    """
    下载单个研报 PDF
    
    Args:
        report_id: 研报 ID
        force: 强制重新下载
    
    Returns:
        本地文件路径，失败返回 None
    """
    conn = connect()
    cur = conn.execute(
        "SELECT id, ts_code, title, url, local_path FROM research_report WHERE id = ?",
        (report_id,)
    )
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print(f"研报 {report_id} 不存在")
        return None
    
    row = dict(row)
    
    # 已下载且不强制重下
    if row["local_path"] and Path(row["local_path"]).exists() and not force:
        return row["local_path"]
    
    # 按股票代码分目录
    ts_code = row["ts_code"] or "unknown"
    subdir = OUTPUT_DIR / ts_code.replace(".", "_")
    subdir.mkdir(parents=True, exist_ok=True)
    
    # 文件名
    filename = sanitize_filename(row["title"]) + ".pdf"
    local_path = subdir / filename
    
    # 下载
    try:
        resp = requests.get(row["url"], timeout=30)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)
        
        # 更新 DB
        update_local_path(report_id, str(local_path))
        print(f"已下载: {local_path}")
        return str(local_path)
    except Exception as e:
        print(f"下载失败 [{report_id}]: {e}")
        return None


def download_batch(report_ids: list[int], delay: float = 1.0) -> list[str]:
    """
    批量下载
    
    Args:
        report_ids: 研报 ID 列表
        delay: 下载间隔（秒）
    
    Returns:
        成功下载的本地路径列表
    """
    paths = []
    for i, rid in enumerate(report_ids):
        path = download_report(rid)
        if path:
            paths.append(path)
        if i < len(report_ids) - 1:
            time.sleep(delay)
    return paths


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下载研报 PDF")
    parser.add_argument("ids", nargs="+", type=int, help="研报 ID")
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    args = parser.parse_args()
    
    for rid in args.ids:
        download_report(rid, force=args.force)
```

**Step 2: 测试下载**

```bash
python -m analyzers.research.download 1
```

**Step 3: Commit**

```bash
git add analyzers/research/download.py
git commit -m "feat(research): 添加研报 PDF 下载功能"
```

---

## Task 5: Interpreter - PDF 解析与 LLM 提取

**Files:**
- Create: `interpreters/research/_shared/pdf_parser.py`
- Create: `interpreters/research/_shared/llm.py`
- Create: `interpreters/research/extract.py`

**Step 1: 创建目录结构**

```bash
mkdir -p interpreters/research/_shared
touch interpreters/research/__init__.py
touch interpreters/research/_shared/__init__.py
```

**Step 2: 创建 pdf_parser.py**

```python
# interpreters/research/_shared/pdf_parser.py
"""PDF 文本提取"""

import pdfplumber


def extract_text(pdf_path: str, max_pages: int = 3) -> str:
    """
    提取 PDF 前 N 页文本
    
    Args:
        pdf_path: PDF 文件路径
        max_pages: 最大页数
    
    Returns:
        提取的文本
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:max_pages]
        texts = []
        for p in pages:
            text = p.extract_text()
            if text:
                texts.append(text)
        return "\n\n".join(texts)
```

**Step 3: 创建 llm.py**

```python
# interpreters/research/_shared/llm.py
"""Gemini LLM 工具"""

import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def init_genai():
    """初始化 Gemini"""
    genai.configure(api_key=GEMINI_API_KEY)


def extract_insights(text: str) -> dict:
    """
    用 Gemini 提取研报摘要和观点
    
    Args:
        text: 研报文本
    
    Returns:
        {
            "summary": "摘要",
            "key_points": ["观点1", "观点2"],
            "investment_advice": "投资建议",
            "risk_warning": "风险提示"
        }
    """
    init_genai()
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""分析以下券商研报内容，提取关键信息。

要求：
1. 摘要：100字以内概括核心内容
2. 核心观点：提取 3-5 个关键观点，每个 50 字以内
3. 投资建议：如有明确建议（买入/增持/中性/减持/卖出），提取出来
4. 风险提示：如有风险提示，简要列出

输出格式（严格 JSON）：
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "investment_advice": "...",
    "risk_warning": "..."
}}

研报内容：
{text[:8000]}
"""
    
    response = model.generate_content(prompt)
    
    # 解析 JSON
    try:
        # 提取 JSON 块
        content = response.text
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    
    # 解析失败，返回原始文本
    return {
        "summary": "",
        "key_points": [],
        "investment_advice": "",
        "risk_warning": "",
        "raw_response": response.text
    }
```

**Step 4: 创建 extract.py**

```python
# interpreters/research/extract.py
"""研报内容提取"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.research._shared.db import connect, update_parsed_at
from analyzers.research.download import download_report
from interpreters.research._shared.llm import extract_insights
from interpreters.research._shared.pdf_parser import extract_text

OUTPUT_DIR = PROJECT_ROOT / "output"


def extract_report(report_id: int, force: bool = False) -> dict | None:
    """
    提取单个研报内容
    
    Args:
        report_id: 研报 ID
        force: 强制重新解析
    
    Returns:
        {
            "report_id": 123,
            "title": "...",
            "trade_date": "...",
            "inst_csname": "...",
            "summary": "...",
            "key_points": [...],
            "investment_advice": "...",
            "risk_warning": "...",
            "raw_text": "..."
        }
    """
    conn = connect()
    cur = conn.execute(
        """SELECT id, trade_date, ts_code, name, title, inst_csname, 
                  local_path, parsed_at
           FROM research_report WHERE id = ?""",
        (report_id,)
    )
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print(f"研报 {report_id} 不存在")
        return None
    
    row = dict(row)
    
    # 已解析且不强制重解析
    if row["parsed_at"] and not force:
        print(f"研报 {report_id} 已解析于 {row['parsed_at']}")
        # 从缓存文件读取
        cache_file = OUTPUT_DIR / "research" / f"{report_id}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
    
    # 确保已下载
    local_path = row["local_path"]
    if not local_path or not Path(local_path).exists():
        local_path = download_report(report_id)
        if not local_path:
            return None
    
    # 提取文本
    print(f"提取文本: {local_path}")
    raw_text = extract_text(local_path, max_pages=3)
    
    if not raw_text.strip():
        print(f"研报 {report_id} 无法提取文本")
        return None
    
    # LLM 提取
    print(f"调用 Gemini 分析...")
    insights = extract_insights(raw_text)
    
    # 组装结果
    result = {
        "report_id": report_id,
        "title": row["title"],
        "trade_date": row["trade_date"],
        "ts_code": row["ts_code"],
        "name": row["name"],
        "inst_csname": row["inst_csname"],
        "summary": insights.get("summary", ""),
        "key_points": insights.get("key_points", []),
        "investment_advice": insights.get("investment_advice", ""),
        "risk_warning": insights.get("risk_warning", ""),
        "raw_text": raw_text[:5000],  # 截断保存
    }
    
    # 保存缓存
    cache_dir = OUTPUT_DIR / "research"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{report_id}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 更新解析时间
    update_parsed_at(report_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    print(f"解析完成: {cache_file}")
    return result


def extract_batch(report_ids: list[int]) -> list[dict]:
    """批量提取"""
    results = []
    for rid in report_ids:
        result = extract_report(rid)
        if result:
            results.append(result)
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="提取研报内容")
    parser.add_argument("ids", nargs="+", type=int, help="研报 ID")
    parser.add_argument("--force", action="store_true", help="强制重新解析")
    args = parser.parse_args()
    
    for rid in args.ids:
        result = extract_report(rid, force=args.force)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
```

**Step 5: Commit**

```bash
git add interpreters/research/
git commit -m "feat(research): 添加 PDF 解析和 Gemini 观点提取"
```

---

## Task 6: Pipeline 入口

**Files:**
- Create: `analyzers/research/pipeline.py`

**Step 1: 创建 pipeline.py**

```python
# analyzers/research/pipeline.py
"""研报分析流程入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.research_report import fetch_research_report
from analyzers.research.search import search_reports
from analyzers.research.download import download_report, download_batch
from interpreters.research.extract import extract_report, extract_batch


def run_search(
    ts_code: str = None,
    ind_name: str = None,
    keyword: str = None,
    inst_csname: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    fetch_if_empty: bool = True,
) -> list[dict]:
    """
    搜索研报
    
    Args:
        fetch_if_empty: 若 DB 无数据，自动从 API 拉取
    """
    results = search_reports(
        ts_code=ts_code,
        ind_name=ind_name,
        keyword=keyword,
        inst_csname=inst_csname,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    
    if not results and fetch_if_empty:
        print("DB 无数据，从 API 拉取...")
        fetch_research_report(
            ts_code=ts_code,
            ind_name=ind_name,
            inst_csname=inst_csname,
            start_date=start_date,
            end_date=end_date,
        )
        results = search_reports(
            ts_code=ts_code,
            ind_name=ind_name,
            keyword=keyword,
            inst_csname=inst_csname,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    
    return results


def run_extract(report_id: int, force: bool = False) -> dict | None:
    """下载并解析单个研报"""
    return extract_report(report_id, force=force)


def run_batch_extract(report_ids: list[int]) -> list[dict]:
    """批量解析"""
    return extract_batch(report_ids)


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="研报分析流程")
    subparsers = parser.add_subparsers(dest="command")
    
    # 搜索
    search_p = subparsers.add_parser("search", help="搜索研报")
    search_p.add_argument("--ts-code", help="股票代码")
    search_p.add_argument("--ind", help="行业名称")
    search_p.add_argument("--keyword", help="标题关键词")
    search_p.add_argument("--inst", help="券商名称")
    search_p.add_argument("--start", help="开始日期")
    search_p.add_argument("--end", help="结束日期")
    search_p.add_argument("--limit", type=int, default=20)
    
    # 解析
    extract_p = subparsers.add_parser("extract", help="解析研报")
    extract_p.add_argument("ids", nargs="+", type=int, help="研报 ID")
    extract_p.add_argument("--force", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "search":
        results = run_search(
            ts_code=args.ts_code,
            ind_name=args.ind,
            keyword=args.keyword,
            inst_csname=args.inst,
            start_date=args.start,
            end_date=args.end,
            limit=args.limit,
        )
        for r in results:
            print(f"[{r['id']}] [{r['trade_date']}] {r['title'][:60]}")
        print(f"\n共 {len(results)} 条")
    
    elif args.command == "extract":
        for rid in args.ids:
            result = run_extract(rid, force=args.force)
            if result:
                print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
```

**Step 2: 测试完整流程**

```bash
# 搜索
python -m analyzers.research.pipeline search --ts-code 600519.SH --limit 5

# 解析
python -m analyzers.research.pipeline extract 1
```

**Step 3: Commit**

```bash
git add analyzers/research/pipeline.py
git commit -m "feat(research): 添加研报分析 pipeline 入口"
```

---

## Task 7: 更新依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 追加依赖**

```
# requirements.txt 追加
pdfplumber>=0.10.0
google-generativeai>=0.8.0
```

**Step 2: 安装**

```bash
pip install pdfplumber google-generativeai
```

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: 添加 pdfplumber 和 google-generativeai 依赖"
```

---

## 验收测试

```bash
cd openclaw-skills/stock-research-group

# 1. 初始化表
python -c "from analyzers.research._shared.db import init_table; init_table()"

# 2. 拉取数据
python fetchers/research_report.py --date 20260203

# 3. 搜索
python -m analyzers.research.pipeline search --keyword "茅台" --limit 5

# 4. 解析
python -m analyzers.research.pipeline extract 1

# 5. 查看输出
ls output/research/
cat output/research/1.json
```
