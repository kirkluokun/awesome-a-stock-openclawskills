# 基础数据调用说明

## 位置
- 脚本：`scripts/fetch_stock_basic.py`
- 数据目录：`data/`
## 财务基础数据
- 脚本：`scripts/fetch_finance_basic.py`

## 接口与参数

### 1) 股票列表（stock_basic）
- 参数：`ts_code`、`name`、`market`、`list_status`、`exchange`、`is_hs`
- 示例：

```bash
python scripts/fetch_stock_basic.py stock_basic
python scripts/fetch_stock_basic.py stock_basic --market 创业板
python scripts/fetch_stock_basic.py stock_basic --exchange SSE --list_status L
```

### 2) 股本情况（盘前）（stk_premarket）
- 参数：`ts_code`、`trade_date`、`start_date`、`end_date`
- 示例：

```bash
python scripts/fetch_stock_basic.py stk_premarket --trade_date 20260202
python scripts/fetch_stock_basic.py stk_premarket --start_date 20260101 --end_date 20260131
```

### 3) 股票历史列表（bak_basic）
- 参数：`trade_date`、`ts_code`
- 示例：

```bash
python scripts/fetch_stock_basic.py bak_basic --trade_date 20260202
python scripts/fetch_stock_basic.py bak_basic --ts_code 000001.SZ
```

### 4) 交易日历（trade_cal）
- 参数：`exchange`、`start_date`、`end_date`、`is_open`
- 示例：

```bash
python scripts/fetch_stock_basic.py trade_cal --start_date 20260101 --end_date 20260131
python scripts/fetch_stock_basic.py trade_cal --exchange SSE --is_open 1 --start_date 20260101 --end_date 20260131
```

## 输出
- 默认输出到：`scripts/output/`
- 命名规则：`<接口>_<参数>.csv`

## 现有基础数据
- 完整股票列表：`data/stock_basic_all.csv`
- 代码精简表：`data/stock_basic_codes.csv`

## 财务接口与参数（含VIP）

### 1) 业绩预告（forecast / forecast_vip）
- 参数：`ts_code`、`ann_date`、`start_date`、`end_date`、`period`、`type`
- 示例：

```bash
python scripts/fetch_finance_basic.py forecast --period 20251231
python scripts/fetch_finance_basic.py forecast_vip --period 20251231
```

### 2) 业绩快报（express / express_vip）
- 参数：`ts_code`、`ann_date`、`start_date`、`end_date`、`period`
- 示例：

```bash
python scripts/fetch_finance_basic.py express --ts_code 600000.SH --start_date 20250101 --end_date 20251231
python scripts/fetch_finance_basic.py express_vip --period 20251231
```

### 3) 预披露时间（disclosure_date）
- 参数：`ts_code`、`end_date`、`pre_date`、`ann_date`、`actual_date`
- 示例：

```bash
python scripts/fetch_finance_basic.py disclosure_date --end_date 20251231
```

### 4) 财务指标数据（fina_indicator / fina_indicator_vip）
- 参数：`ts_code`、`ann_date`、`start_date`、`end_date`、`period`
- 示例：

```bash
python scripts/fetch_finance_basic.py fina_indicator --ts_code 600000.SH
python scripts/fetch_finance_basic.py fina_indicator_vip --period 20251231
```

### 5) 利润表（income / income_vip）
- 参数：`ts_code`、`ann_date`、`f_ann_date`、`start_date`、`end_date`、`period`、`report_type`、`comp_type`
- 示例：

```bash
python scripts/fetch_finance_basic.py income --ts_code 600000.SH --start_date 20250101 --end_date 20251231
python scripts/fetch_finance_basic.py income_vip --period 20251231
```

### 6) 资产负债表（balancesheet / balancesheet_vip）
- 参数：`ts_code`、`ann_date`、`f_ann_date`、`start_date`、`end_date`、`period`、`report_type`、`comp_type`
- 示例：

```bash
python scripts/fetch_finance_basic.py balancesheet --ts_code 600000.SH --start_date 20250101 --end_date 20251231
python scripts/fetch_finance_basic.py balancesheet_vip --period 20251231
```

### 7) 现金流量表（cashflow / cashflow_vip）
- 参数：`ts_code`、`ann_date`、`f_ann_date`、`start_date`、`end_date`、`period`、`report_type`、`comp_type`、`is_calc`
- 示例：

```bash
python scripts/fetch_finance_basic.py cashflow --ts_code 600000.SH --start_date 20250101 --end_date 20251231
python scripts/fetch_finance_basic.py cashflow_vip --period 20251231
```
