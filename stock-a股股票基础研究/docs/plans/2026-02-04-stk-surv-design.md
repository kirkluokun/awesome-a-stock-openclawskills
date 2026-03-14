# 机构调研数据接入 设计文档

**日期**: 2026-02-04

## 需求

接入 Tushare `stk_surv` 接口，实现机构调研数据的拉取、检索和查询功能。

### 功能要求

1. **检索功能**：查询某公司是否有调研，返回列表
2. **拉取功能**：拉取最近30天所有被调研公司的数据
3. **数据库累计存储**：增量更新
4. **详细查询**：查看某公司某次调研的详细内容（包括content）

## 数据结构分析

- 一条记录 = 一个参与人员
- 同一调研事件（ts_code + surv_date）有多条记录（多个参与人员）
- 同一调研事件的 content 完全相同
- 同一公司同一天只有一场调研（一个content）

## 数据库设计

### 1. stk_surv_event（调研事件表）

```sql
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
```

### 2. stk_surv_participant（参与人员表）

```sql
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

## 模块结构

```
stock-research-group/
├── fetchers/
│   └── stk_surv.py              # 拉取调研数据
│
├── analyzers/
│   └── stk_surv/                # 调研分析
│       ├── _shared/
│       │   └── db.py            # 数据库工具
│       ├── schema.sql           # 表结构
│       ├── search.py            # 检索功能
│       └── pipeline.py          # 流程入口
```

## 核心接口

### fetchers/stk_surv.py

```python
def fetch_stk_surv(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
    include_content: bool = True,
) -> int:
    """拉取调研数据，存入两张表，返回新增事件数"""
```

### analyzers/stk_surv/search.py

```python
def search_by_company(company_name: str, days: int = None) -> list[dict]:
    """按公司名称搜索调研（支持日期范围）"""

def search_by_org(org_name: str, days: int = None) -> list[dict]:
    """按机构名称搜索（该机构参加了哪些调研）"""

def search_by_person(person_name: str, days: int = None) -> list[dict]:
    """按参与人员姓名搜索"""

def get_survey_detail(event_id: int) -> dict:
    """获取某次调研的详细信息（包括content和所有参与人员）"""
```

### analyzers/stk_surv/pipeline.py

```python
def run_fetch_recent(days: int = 30) -> int:
    """拉取最近N天的所有调研数据"""

def run_search(query: str, query_type: str = "company", days: int = None) -> list[dict]:
    """统一搜索入口"""
```

## 使用流程

```bash
# 拉取最近30天数据
python -m analyzers.stk_surv.pipeline fetch --days 30

# 搜索某公司调研
python -m analyzers.stk_surv.pipeline search --company "比亚迪"

# 搜索某机构参与的调研
python -m analyzers.stk_surv.pipeline search --org "中信证券"

# 查看某次调研详情
python -m analyzers.stk_surv.pipeline detail --event-id 123
```
