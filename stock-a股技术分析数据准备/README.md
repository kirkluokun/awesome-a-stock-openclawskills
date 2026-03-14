# stock-tech-analysis-step1

A股技术分析第一步技能：用 **tushare-mcp** 打底数据，不绕路。

## 你会得到什么
- 近1年日线（OHLCV）
- 近1年技术因子（若权限可用）
- 近3个月资金流向
- 标准落盘路径 + 一页摘要

## 目录规范
输出到：

```text
results/<project-name>/data/raw/
```

示例：

```text
results/zhenhua-tech-analysis/data/raw/
  603067SH_daily_1y.json
  603067SH_stk_factor_pro_1y.json
  603067SH_moneyflow_3m.json
```

## 前置条件
1. 已安装并可用 `mcporter`
2. 已注册 `tushare-pro` MCP 服务
3. 已配置 `TUSHARE_TOKEN`

快速自检：

```bash
mcporter config list
mcporter list tushare-pro --schema
mcporter call tushare-pro.tushare_daily ts_code=603067.SH start_date=2026-01-01 end_date=2026-03-05 _limit=10
```

## 标准流程（简化版）
1. 拉日线：`tushare_daily`
2. 拉因子：`tushare_stk_factor_pro`
3. 拉资金流：`tushare_moneyflow`
4. 存 raw 文件
5. 输出摘要：最新交易日、最新收盘、近20日涨跌幅、条数、完整性

## 这一步常见坑（简洁）
- **代码格式错**：必须 `603067.SH` 这种格式
- **返回条数不够**：记得加 `_limit`
- **因子接口权限问题**：报错就记录原因，先用日线+资金流继续
- **路径不统一**：严格写到 `results/project-name/data/raw/`

## 本次振华股份 Step1 参考
- 标的：`603067.SH`
- 已验证接口：`tushare_daily`、`tushare_stk_factor_pro`、`tushare_moneyflow`
- 输出摘要字段：
  - 最新交易日
  - 最新收盘
  - 近20日涨跌幅
  - 日线/因子/资金流条数
  - 完整性判断
