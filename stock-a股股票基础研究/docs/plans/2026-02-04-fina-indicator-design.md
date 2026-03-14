# 财务指标数据接入 设计文档

**日期**: 2026-02-04

## 需求

接入 Tushare `fina_indicator`/`fina_indicator_vip` 接口，实现财务指标数据的拉取、存储和查询。

### 功能要求

1. **单公司查询**：随时拉取指定公司财务指标（普通接口）
2. **批量刷新**：按季度 period 全量拉取（VIP接口）
3. **区间刷新**：给定日期区间时，自动拆分为季度末 period 列表逐个拉取
4. **数据覆盖**：同一报告期数据更新时覆盖旧记录
5. **可查询字段**：明确常用指标 + 完整字段清单（`docs/financial-indicators.md`）

## 数据源

- **接口**: `fina_indicator` / `fina_indicator_vip`
- **积分要求**: 2000积分（单公司）/ 5000积分（VIP全量）
- **参数**: `ts_code`, `ann_date`, `start_date`, `end_date`, `period`
- **分页限制**: 普通接口单次最多100条（通过日期分段拉取）

## 存储方案

### 数据库表结构

**表名**: `fina_indicator`

**基础列**（常用指标 12 个）:
- `ts_code` TEXT NOT NULL
- `ann_date` TEXT
- `end_date` TEXT NOT NULL
- `roe` REAL
- `roa` REAL
- `grossprofit_margin` REAL
- `netprofit_margin` REAL
- `current_ratio` REAL
- `quick_ratio` REAL
- `debt_to_assets` REAL
- `assets_turn` REAL
- `inv_turn` REAL
- `ar_turn` REAL
- `eps` REAL
- `profit_to_gr` REAL
- `source` TEXT
- `payload_json` TEXT NOT NULL
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

**唯一约束**: `UNIQUE(ts_code, end_date)`

**索引**:
- `idx_fina_indicator_ts_code` ON fina_indicator(ts_code)
- `idx_fina_indicator_end_date` ON fina_indicator(end_date)
- `idx_fina_indicator_ts_end` ON fina_indicator(ts_code, end_date)

### 字段清单参考

- 完整字段清单：`docs/financial-indicators.md`
- 说明：该文档列出所有可用字段与中文含义，供后续 agent 查询使用

## 获取与查询设计

### 获取层（fetchers）

- `fetchers/fina_indicator.py`  
  - 支持普通接口（单公司）  
  - 支持 VIP 接口（按 period 全量）  
  - 支持 `start_date/end_date` 或 `period`  

### 分析层（analyzers）

- `analyzers/fina_indicator/schema.sql`：建表
- `analyzers/fina_indicator/_shared/db.py`：连接与 upsert
- `analyzers/fina_indicator/search.py`：查询与自动拉取
- `analyzers/fina_indicator/pipeline.py`：CLI 入口

## 批量刷新规则

### VIP 全量

- 直接指定 `period` 拉取单季度全量数据  
  示例：`period=20240331`

### 区间刷新

- 输入 `start_date/end_date` 时，自动生成区间内所有季度末：
  - 0331 / 0630 / 0930 / 1231
- 逐个 period 拉取（断点机制按 period 记录）

## 数据覆盖策略

- 使用 `ts_code + end_date` 作为唯一键  
- 同一报告期的新数据会覆盖旧数据，避免“公告日期变化导致重复”  

## 输出与使用示例

```bash
# 单公司拉取（普通接口）
python -m analyzers.fina_indicator.pipeline fetch --ts-code 000001.SZ --start-date 20240331 --end-date 20241231

# 单季度全量（VIP）
python -m analyzers.fina_indicator.pipeline fetch --period 20240331 --vip

# 区间全量（VIP，自动拆分季度）
python -m analyzers.fina_indicator.pipeline fetch --start-date 20240331 --end-date 20251231 --vip
```
