# Tool 完整索引

158 个 MCP tool，按场景分类。调用前需先 `ToolSearch("+tushare <关键词>")` 加载。

---

## A股行情

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_stock_basic` | 股票列表 | exchange, list_status |
| `tushare_daily` | 日线行情 | ts_code, trade_date, start_date, end_date |
| `tushare_weekly` | 周线行情 | ts_code, trade_date, start_date, end_date |
| `tushare_monthly` | 月线行情 | ts_code, trade_date, start_date, end_date |
| `tushare_daily_basic` | 每日指标（PE/PB/换手率/市值） | ts_code, trade_date |
| `tushare_adj_factor` | 复权因子 | ts_code, trade_date |
| `tushare_stk_limit` | 涨跌停价格 | ts_code, trade_date |
| `tushare_suspend_d` | 停复牌信息 | ts_code, trade_date, suspend_type |
| `tushare_stk_mins` | A股分钟行情 | ts_code, freq, start_date, end_date |
| `tushare_rt_min` | 实时分钟行情 | ts_code |

## A股基本信息

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_namechange` | 股票曾用名 | ts_code |
| `tushare_stock_company` | 上市公司信息 | ts_code, exchange |
| `tushare_new_share` | 新股上市信息 | start_date, end_date |
| `tushare_stock_st` | ST 标记 | ts_code |
| `tushare_stock_hsgt` | 沪深港通成分 | ts_code, hs_type |
| `tushare_stk_managers` | 管理层信息 | ts_code |
| `tushare_stk_rewards` | 管理层薪酬持股 | ts_code, end_date |
| `tushare_trade_cal` | 交易日历 | exchange, start_date, end_date |
| `tushare_daily_info` | 每日市场总貌 | trade_date, exchange |

## 财务数据

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_income` | 利润表 | ts_code, period, start_date, end_date |
| `tushare_balancesheet` | 资产负债表 | ts_code, period, start_date, end_date |
| `tushare_cashflow` | 现金流量表 | ts_code, period, start_date, end_date |
| `tushare_fina_indicator` | 财务指标（ROE/毛利率等） | ts_code, period, start_date, end_date |
| `tushare_fina_audit` | 审计意见 | ts_code, period |
| `tushare_fina_mainbz` | 主营业务构成 | ts_code, period, type |
| `tushare_disclosure_date` | 财报披露日期 | end_date |

## 盈利预测 & 研报

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_forecast` | 业绩预告 | ts_code, ann_date, period |
| `tushare_express` | 业绩快报 | ts_code, ann_date, period |
| `tushare_report_rc` | 卖方盈利预测 | ts_code |
| `tushare_broker_recommend` | 券商月度金股 | month |
| `tushare_research_report` | 券商研究报告（含PDF链接） | ts_code, start_date, end_date |
| `tushare_anns` | 上市公司公告 | ts_code, trade_date, start_date, end_date |

## 股东数据

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_stk_holdernumber` | 股东人数 | ts_code, end_date |
| `tushare_top10_holders` | 十大股东 | ts_code, period |
| `tushare_top10_floatholders` | 十大流通股东 | ts_code, period |
| `tushare_stk_holdertrade` | 股东增减持 | ts_code, ann_date |
| `tushare_ccass_hold` | 中央结算系统持股明细 | ts_code, hk_code, trade_date |
| `tushare_ccass_hold_stat` | 中央结算系统持股汇总 | ts_code, hk_code, trade_date |

## 公司行为

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_dividend` | 分红送股 | ts_code, ann_date |
| `tushare_repurchase` | 股票回购 | ts_code, ann_date |
| `tushare_share_float` | 限售解禁 | ts_code, ann_date |
| `tushare_pledge_stat` | 股权质押统计 | ts_code |
| `tushare_pledge_detail` | 股权质押明细 | ts_code |
| `tushare_stk_surv` | 机构调研明细 | ts_code, trade_date |

## 技术分析

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_stk_factor_pro` | 技术面因子（MA/MACD/KDJ/BOLL/RSI） | ts_code, start_date, end_date |
| `tushare_stk_nineturn` | 神奇九转指标 | ts_code, trade_date |
| `tushare_cyq_chips` | 筹码分布 | ts_code, trade_date |
| `tushare_cyq_perf` | 筹码绩效 | ts_code, trade_date |

## 龙虎榜

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_top_list` | 龙虎榜每日明细 | trade_date |
| `tushare_top_inst` | 龙虎榜机构明细 | trade_date |

## 融资融券

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_margin` | 融资融券交易汇总 | trade_date, exchange_id |
| `tushare_margin_detail` | 融资融券交易明细 | ts_code, trade_date |

## 资金流向

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_moneyflow` | 个股资金流向 | ts_code, trade_date |
| `tushare_moneyflow_hsgt` | 沪深港通资金流向 | trade_date |
| `tushare_hsgt_top10` | 沪深股通十大成交股 | trade_date, market_type |
| `tushare_ggt_top10` | 港股通十大成交股 | trade_date, market_type |
| `tushare_block_trade` | 大宗交易 | ts_code, trade_date |

## 涨跌停

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_limit_list_d` | 涨跌停列表 | trade_date, limit_type |
| `tushare_limit_cpt_list` | 涨停板封单统计 | trade_date |

## 游资

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_hm_list` | 游资名录 | — |
| `tushare_hm_detail` | 游资每日操作明细 | trade_date, hm_name |

## 指数数据

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_index_basic` | 指数基本信息 | market, category |
| `tushare_index_daily` | 指数日线 | ts_code, trade_date, start_date, end_date |
| `tushare_index_weekly` | 指数周线 | ts_code, start_date, end_date |
| `tushare_index_monthly` | 指数月线 | ts_code, start_date, end_date |
| `tushare_index_weight` | 指数成分和权重 | index_code, trade_date |
| `tushare_index_dailybasic` | 大盘指数每日指标 | ts_code, trade_date |
| `tushare_index_global` | 国际主要指数 | ts_code, trade_date |

## 行业分类

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_index_classify` | 申万行业分类 | level, src |
| `tushare_index_member_all` | 申万行业成分 | index_code, is_new |
| `tushare_sw_daily` | 申万行业日线 | ts_code, trade_date |
| `tushare_ci_daily` | 中信行业日线 | ts_code, trade_date |
| `tushare_ci_index_member` | 中信行业成分 | ts_code |

## 板块

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_concept` | 概念板块列表 | src |
| `tushare_concept_detail` | 概念板块成分 | id, ts_code |
| `tushare_ths_index` | 同花顺板块指数 | exchange, type |
| `tushare_ths_daily` | 同花顺板块日线 | ts_code, trade_date |
| `tushare_ths_member` | 同花顺板块成分 | ts_code |
| `tushare_dc_index` | 东财板块列表 | — |
| `tushare_dc_member` | 东财板块成分 | ts_code |
| `tushare_dc_hot` | 东财热门板块 | trade_date |
| `tushare_tdx_index` | 通达信板块列表 | — |
| `tushare_tdx_daily` | 通达信板块日线 | ts_code, trade_date |
| `tushare_tdx_member` | 通达信板块成分 | ts_code |

## ETF

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_etf_basic` | ETF 列表 | market |
| `tushare_fund_daily` | ETF/基金日线行情 | ts_code, trade_date |
| `tushare_etf_share_size` | ETF 规模变动 | ts_code, trade_date |
| `tushare_etf_index` | ETF 关联指数 | ts_code |
| `tushare_etf_mins` | ETF 分钟行情 | ts_code, freq, start_date, end_date |

## 基金

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_fund_basic` | 基金列表 | market, status |
| `tushare_fund_nav` | 基金净值 | ts_code, end_date |
| `tushare_fund_div` | 基金分红 | ts_code, ann_date |
| `tushare_fund_portfolio` | 基金持仓 | ts_code, ann_date |
| `tushare_fund_company` | 基金公司 | — |
| `tushare_fund_manager` | 基金经理 | ts_code |
| `tushare_fund_share` | 基金份额变动 | ts_code, trade_date |
| `tushare_fund_adj` | 基金复权因子 | ts_code, trade_date |

## 港股

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_hk_basic` | 港股列表 | list_status |
| `tushare_hk_tradecal` | 港股交易日历 | start_date, end_date |
| `tushare_hk_daily` | 港股日线 | ts_code, trade_date |
| `tushare_hk_adjfactor` | 港股复权因子 | ts_code, trade_date |
| `tushare_ggt_daily` | 港股通每日成交 | trade_date |
| `tushare_hk_mins` | 港股分钟行情 | ts_code, freq, start_date, end_date |

## 港股财务

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_hk_income` | 港股利润表 | ts_code, period | 需 15000 积分 |
| `tushare_hk_balancesheet` | 港股资产负债表 | ts_code, period | 需 15000 积分 |
| `tushare_hk_cashflow` | 港股现金流量表 | ts_code, period | 需 15000 积分 |
| `tushare_hk_fina_indicator` | 港股财务指标 | ts_code, period | 需 15000 积分 |

## 美股

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_us_basic` | 美股列表 | classify |
| `tushare_us_tradecal` | 美股交易日历 | start_date, end_date |
| `tushare_us_daily` | 美股日线 | ts_code, trade_date |
| `tushare_us_adjfactor` | 美股复权因子 | ts_code, trade_date |

## 美股财务

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_us_income` | 美股利润表 | ts_code, period | 需 15000 积分 |
| `tushare_us_balancesheet` | 美股资产负债表 | ts_code, period | 需 15000 积分 |
| `tushare_us_cashflow` | 美股现金流量表 | ts_code, period | 需 15000 积分 |

## A/H 对比

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_stk_ah_comparison` | A/H 股溢价率 | ts_code, trade_date |

## 期货

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_fut_basic` | 期货合约列表 | exchange, fut_type |
| `tushare_fut_mapping` | 主力/连续合约映射 | ts_code, trade_date |
| `tushare_fut_daily` | 期货日线 | ts_code, trade_date |
| `tushare_fut_wsr` | 仓单日报 | trade_date, symbol |
| `tushare_ft_limit` | 期货涨跌停 | ts_code, trade_date |
| `tushare_fut_weekly_detail` | 期货交易所周报 | trade_date, symbol |
| `tushare_fut_settle` | 期货结算参数 | ts_code, trade_date |
| `tushare_fut_holding` | 期货持仓排名 | trade_date, symbol, exchange |
| `tushare_fut_wm` | 期货周/月行情 | ts_code, trade_date, date_type |

## 外汇

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_fx_obasic` | 外汇基本信息 | exchange, classify |
| `tushare_fx_daily` | 外汇日线 | ts_code, trade_date |

## 期权

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_opt_basic` | 期权合约列表 | exchange, opt_code |
| `tushare_opt_daily` | 期权日线 | ts_code, trade_date |
| `tushare_opt_mins` | 期权分钟行情 | ts_code, freq, start_date, end_date |

## 可转债

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_cb_basic` | 可转债基本信息 | ts_code |
| `tushare_cb_daily` | 可转债日线 | ts_code, trade_date |
| `tushare_cb_issue` | 可转债发行 | ts_code |
| `tushare_cb_rate` | 可转债票面利率 | ts_code |
| `tushare_cb_call` | 可转债赎回信息 | ts_code |
| `tushare_cb_share` | 可转债转股结果 | ts_code |
| `tushare_cb_price_chg` | 可转债转股价变动 | ts_code |
| `tushare_repo_daily` | 债券回购日线 | ts_code, trade_date |

## 新闻

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_news` | 新闻快讯 | start_date, end_date, src |
| `tushare_cctv_news` | 新闻联播文字 | date |

## 利率

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_shibor` | Shibor 利率 | start_date, end_date |
| `tushare_lpr` | LPR 贷款基准利率 | start_date, end_date |
| `tushare_hibor` | Hibor（香港） | start_date, end_date |
| `tushare_libor` | Libor（伦敦） | start_date, end_date |
| `tushare_yc_cb` | 中国国债收益率曲线 | ts_code, trade_date |

## 美国利率 & 国债

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_us_tycr` | 美国国债收益率 | start_date, end_date |
| `tushare_us_trycr` | 美国实际国债收益率 | start_date, end_date |
| `tushare_us_tltr` | 美国长期国债利率 | start_date, end_date |
| `tushare_us_trltr` | 美国实际长期国债利率 | start_date, end_date |
| `tushare_us_tbr` | 美国短期国债利率 | start_date, end_date |

## 宏观经济

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_cn_gdp` | GDP | q（季度） |
| `tushare_cn_pmi` | PMI | start_date, end_date |
| `tushare_cn_m` | 货币供应量（M0/M1/M2） | start_date, end_date |
| `tushare_eco_cal` | 经济日历 | start_date, end_date |
| `tushare_sf_month` | 社会融资规模 | start_date, end_date |

## 黄金 & 民间借贷

| Tool | 说明 | 关键参数 |
|------|------|---------|
| `tushare_sge_basic` | 上海金交所基本信息 | — |
| `tushare_sge_daily` | 上海金交所日线 | ts_code, trade_date |
| `tushare_gz_index` | 广州民间借贷利率指数 | start_date, end_date |
| `tushare_wz_index` | 温州民间借贷利率指数 | start_date, end_date |
