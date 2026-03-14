# 券商月度金股数据接入 设计文档

**日期**: 2026-02-04

## 需求

接入 Tushare `broker_recommend` 接口，实现券商月度金股数据的拉取、存储、统计和报告生成。

### 功能要求

1. **数据拉取**：每月月初拉取当月金股数据
2. **数据存储**：存入 SQLite 数据库
3. **统计功能**：
   - 本月公司被推荐次数排序
   - 历史月份对比（连续推荐）
   - 券商维度统计
4. **报告生成**：CSV/文本格式

## 数据库设计

```sql
CREATE TABLE IF NOT EXISTS broker_recommend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,              -- 月度 YYYYMM
    broker TEXT NOT NULL,             -- 券商名称
    ts_code TEXT NOT NULL,            -- 股票代码
    name TEXT NOT NULL,               -- 股票简称
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(month, broker, ts_code)     -- 同一券商同一月不重复推荐同一股票
);

CREATE INDEX IF NOT EXISTS idx_br_month ON broker_recommend(month);
CREATE INDEX IF NOT EXISTS idx_br_ts_code ON broker_recommend(ts_code);
CREATE INDEX IF NOT EXISTS idx_br_broker ON broker_recommend(broker);
```

## 模块结构

```
stock-research-group/
├── fetchers/
│   └── broker_recommend.py      # 拉取月度金股数据
│
├── analyzers/
│   └── broker_recommend/        # 金股分析
│       ├── _shared/
│       │   └── db.py            # 数据库工具
│       ├── schema.sql           # 表结构
│       ├── stats.py             # 统计功能
│       └── pipeline.py          # 流程入口
│
└── interpreters/
    └── broker_recommend/        # 报告生成
        └── report.py            # 生成统计报告
```

## 核心接口

### fetchers/broker_recommend.py

```python
def fetch_broker_recommend(month: str) -> int:
    """从 Tushare 拉取指定月份的金股数据，存入 DB，返回新增条数"""
```

### analyzers/broker_recommend/stats.py

```python
def get_monthly_stats(month: str) -> dict:
    """获取指定月份的统计
    返回: {
        "month": "202602",
        "by_company": [{"ts_code": "...", "name": "...", "count": 5, "brokers": [...]}],
        "by_broker": [{"broker": "...", "count": 10}]
    }
    """

def get_continuous_recommendations(ts_code: str, months: int = 3) -> list[str]:
    """获取连续被推荐的月份列表"""

def get_broker_recommendations(broker: str, month: str = None) -> list[dict]:
    """获取某券商的金股列表（可选指定月份）"""
```

### analyzers/broker_recommend/pipeline.py

```python
def run_fetch(month: str = None) -> int:
    """拉取数据，month=None 时自动使用当前月份"""

def run_stats(month: str = None) -> dict:
    """运行统计，返回统计结果"""
```

### interpreters/broker_recommend/report.py

```python
def generate_report(month: str, output_format: str = "csv") -> str:
    """生成报告，返回文件路径"""
```

## 使用流程

```bash
# 拉取当前月份
python -m analyzers.broker_recommend.pipeline fetch

# 拉取指定月份
python -m analyzers.broker_recommend.pipeline fetch --month 202602

# 查看统计
python -m analyzers.broker_recommend.pipeline stats --month 202602

# 生成报告
python interpreters/broker_recommend/report.py --month 202602
```

## 输出格式

### CSV 报告

```csv
排名,股票代码,股票名称,推荐次数,推荐券商
1,002594.SZ,比亚迪,15,国金证券|中信证券|东吴证券|...
```

### 统计 JSON

```json
{
  "month": "202602",
  "by_company": [
    {"ts_code": "002594.SZ", "name": "比亚迪", "count": 15, "brokers": ["国金证券", "中信证券"]}
  ],
  "by_broker": [
    {"broker": "国金证券", "count": 10}
  ],
  "continuous": {
    "002594.SZ": ["202501", "202502", "202503"]
  }
}
```

## 后续任务

- [ ] 初始化时拉取 202501 以来的所有历史数据
