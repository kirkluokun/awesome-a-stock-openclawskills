# 常见查询模式

## 个股全景分析

一只股票的完整画像，需组合以下 tool：

| 步骤 | Tool | 说明 |
|------|------|------|
| 1 | `tushare_stock_basic` | 基本信息（行业、上市日期） |
| 2 | `tushare_daily` | 近期行情 |
| 3 | `tushare_daily_basic` | 估值指标（PE/PB/换手率） |
| 4 | `tushare_income` + `tushare_balancesheet` + `tushare_cashflow` | 财务三表 |
| 5 | `tushare_fina_indicator` | 财务指标（ROE/毛利率等） |
| 6 | `tushare_top10_holders` | 十大股东 |
| 7 | `tushare_stk_factor_pro` | 技术面因子（MA/MACD/KDJ/BOLL） |
| 8 | `tushare_moneyflow` | 资金流向 |
| 9 | `tushare_concept_detail` | 所属概念板块 |

## 财务三表分析（3-Statements）

```
tushare_income       → 利润表（营收、净利润、毛利）
tushare_balancesheet → 资产负债表（总资产、负债、股东权益）
tushare_cashflow     → 现金流量表（经营/投资/筹资现金流）
tushare_fina_indicator → 衍生指标（ROE/ROA/毛利率/净利率）
tushare_fina_mainbz  → 主营业务构成（按产品/地区）
```

典型参数：`ts_code='600000.SH', period='20240930'`

## DCF 估值所需数据

| 数据 | Tool |
|------|------|
| 历史营收/净利润 | `tushare_income` |
| 历史自由现金流 | `tushare_cashflow` |
| 资本结构 | `tushare_balancesheet` |
| 行业 beta | `tushare_daily` + `tushare_index_daily` 回归计算 |
| 无风险利率 | `tushare_yc_cb`（国债收益率曲线） |
| 行业可比公司 | `tushare_index_member_all` 找同行业 |
| 可比公司估值 | `tushare_daily_basic` 批量取 PE/PB |

## 可比公司分析（Comps）

```
1. tushare_index_classify     → 找到目标公司所属申万行业
2. tushare_index_member_all   → 获取同行业所有公司
3. tushare_daily_basic        → 批量获取 PE/PB/PS/市值
4. tushare_fina_indicator     → 批量获取 ROE/毛利率/净利率
5. tushare_income             → 营收增速对比
```

## 盈利预测 & 研报

```
tushare_forecast         → 公司业绩预告（预增/预减/扭亏）
tushare_express          → 业绩快报
tushare_broker_recommend → 券商月度金股推荐
tushare_research_report  → 券商研究报告（含PDF下载链接）
tushare_report_rc        → 卖方盈利预测一致预期
```

## 行业/板块分析

```
# 申万行业
tushare_index_classify   → 行业分类列表
tushare_index_member_all → 行业成分股
tushare_sw_daily         → 行业指数日线
tushare_ci_daily         → 中信行业日线

# 概念板块
tushare_concept          → 概念列表
tushare_concept_detail   → 概念成分股

# 同花顺板块
tushare_ths_index        → 同花顺板块列表
tushare_ths_daily        → 同花顺板块日线
tushare_ths_member       → 同花顺板块成分

# 东财板块
tushare_dc_index         → 东财板块列表
tushare_dc_member        → 东财板块成分
tushare_dc_hot           → 东财热门板块
```

## 市场情绪 & 异动

```
tushare_limit_list_d     → 当日涨跌停列表
tushare_limit_cpt_list   → 涨停板封单统计
tushare_top_list         → 龙虎榜明细
tushare_top_inst         → 龙虎榜机构明细
tushare_hm_detail        → 游资每日操作
tushare_moneyflow        → 个股资金流向
tushare_block_trade      → 大宗交易
tushare_stk_holdertrade  → 股东增减持
```

## 宏观经济

```
tushare_cn_gdp     → GDP
tushare_cn_pmi     → PMI
tushare_cn_m       → 货币供应量（M0/M1/M2）
tushare_sf_month   → 社会融资规模
tushare_eco_cal    → 经济日历
tushare_shibor     → Shibor
tushare_lpr        → LPR
tushare_yc_cb      → 国债收益率曲线
```

## 跨市场对比

```
# A/H 溢价
tushare_stk_ah_comparison → A/H 股溢价率

# 沪深港通
tushare_moneyflow_hsgt    → 北向/南向资金流向
tushare_hsgt_top10        → 沪深股通十大成交股
tushare_ggt_top10         → 港股通十大成交股
tushare_ggt_daily         → 港股通每日成交统计

# 全球指数
tushare_index_global      → 全球主要指数行情
```

## 基金分析

```
tushare_fund_basic     → 基金列表（场内E/场外O）
tushare_fund_nav       → 基金净值
tushare_fund_portfolio → 基金持仓明细
tushare_fund_manager   → 基金经理信息
tushare_fund_share     → 基金份额变动（申购赎回）
tushare_fund_div       → 基金分红
tushare_fund_company   → 基金公司列表
```

## ETF 分析

```
tushare_etf_basic      → ETF 列表
tushare_fund_daily     → ETF 日线行情
tushare_etf_share_size → ETF 规模变动
tushare_etf_index      → ETF 关联指数
tushare_etf_mins       → ETF 分钟行情
```
