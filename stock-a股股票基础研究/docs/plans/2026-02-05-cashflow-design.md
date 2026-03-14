# 现金流量表数据接入 设计文档

**日期**: 2026-02-05

## 需求

接入 Tushare `cashflow`/`cashflow_vip` 接口，实现现金流量表数据的拉取、存储和查询。

### 功能要求

1. **单公司查询**：随时拉取指定公司现金流量表（普通接口）
2. **批量刷新**：按季度 period 全量拉取（VIP接口）
3. **区间刷新**：给定日期区间时，自动拆分为季度末 period 列表逐个拉取
4. **数据覆盖**：同一报告期数据更新时覆盖旧记录
5. **自动补全**：单公司查询时若数据不足，自动补拉近 4 年

## 数据源

- **接口**: `cashflow` / `cashflow_vip`
- **积分要求**: 2000积分（单公司）/ 5000积分（VIP全量）
- **参数**: `ts_code`, `ann_date`, `f_ann_date`, `start_date`, `end_date`, `period`, `report_type`, `comp_type`, `is_calc`

## 存储方案

### 数据库表结构

**表名**: `cashflow`

**基础列（常用字段 7 个）**:
- `ts_code` TEXT NOT NULL
- `ann_date` TEXT
- `end_date` TEXT NOT NULL
- `n_cashflow_act` REAL
- `n_cashflow_inv` REAL
- `n_cashflow_fin` REAL
- `c_cash_equ_beg_period` REAL
- `c_cash_equ_end_period` REAL
- `c_inf_fr_operate_a` REAL
- `c_outf_operate_a` REAL
- `source` TEXT
- `payload_json` TEXT NOT NULL
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

**唯一约束**: `UNIQUE(ts_code, end_date)`

**索引**:
- `idx_cashflow_ts_code` ON cashflow(ts_code)
- `idx_cashflow_end_date` ON cashflow(end_date)
- `idx_cashflow_ts_end` ON cashflow(ts_code, end_date)

## 获取与查询设计

### 获取层（fetchers）

- `fetchers/cashflow.py`  
  - 支持普通接口（单公司）  
  - 支持 VIP 接口（按 period 全量）  

### 分析层（analyzers）

- `analyzers/cashflow/schema.sql`：建表
- `analyzers/cashflow/_shared/db.py`：连接与 upsert
- `analyzers/cashflow/search.py`：查询与自动拉取（默认补 4 年）
- `analyzers/cashflow/pipeline.py`：CLI 入口

## 批量刷新规则（VIP）

### 单季度

- `--period 20240331` 拉取该季度全量

### 区间刷新

- 输入 `start_date/end_date` 时，自动生成区间内所有季度末：
  - 0331 / 0630 / 0930 / 1231
- 逐个 period 拉取（断点机制按 period 记录）

## 数据覆盖策略

- 使用 `ts_code + end_date` 作为唯一键  
- 同一报告期的新数据会覆盖旧数据，避免重复

## 使用示例

```bash
# 单公司拉取（普通接口）
python -m analyzers.cashflow.pipeline fetch --ts-code 000001.SZ --start-date 20240331 --end-date 20241231

# 单季度全量（VIP）
python -m analyzers.cashflow.pipeline fetch --period 20240331 --vip

# 区间全量（VIP，自动拆分季度）
python fetchers/cashflow_vip_batch.py --start-date 20240331 --end-date 20251231
```
