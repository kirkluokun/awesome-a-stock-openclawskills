# Tushare Pro MCP — 未实现接口备忘

> 220 个接口中已实现 154 个（70%），剩余 66 个按优先级分类如下。

---

## 已停用/暂停 (6个) — 不需要实现

| 接口文档 | API | 说明 |
|----------|-----|------|
| 转融券交易汇总(停) | slb_sec | 已停用 |
| 转融券交易明细(停) | slb_sec_detail | 已停用 |
| 做市借券交易汇总(停) | slb_len_mm | 已停用 |
| 股票开户数据(停) | stk_account | 已停用 |
| 股票开户数据(旧) | stk_account_old | 旧版已废弃 |
| 同花顺涨跌停榜单 | limit_list_ths | 已被 limit_list_d 替代 |

---

## 爬虫/实时数据 (7个) — 需爬虫权限，按需实现

| 接口文档 | API | 说明 |
|----------|-----|------|
| 实时Tick(爬虫) | realtime_quote | 爬虫权限 |
| 实时成交(爬虫) | realtime_tick | 爬虫权限 |
| 实时排名(爬虫) | realtime_list | 爬虫权限 |
| 实时日线 | rt_k | A股实时K线 |
| ETF实时日线 | rt_etf_k | ETF实时K线 |
| 港股实时日线 | rt_hk_k | 港股实时K线 |
| 指数实时日线 | rt_idx_k | 指数实时K线 |

---

## 技术面因子 (5个) — 需专业版/高积分

| 接口文档 | API | 说明 |
|----------|-----|------|
| 股票技术面因子 | stk_factor | 普通版 |
| 股票技术面因子(专业版) | stk_factor_pro | 专业版 |
| 基金技术面因子(专业版) | fund_factor_pro | 专业版 |
| 可转债技术面因子(专业版) | cb_factor_pro | 专业版 |
| 指数技术面因子(专业版) | idx_factor_pro | 专业版 |

---

## 非金融数据 (8个) — 与投研无关

| 接口文档 | API | 说明 |
|----------|-----|------|
| 电影日度票房 | bo_daily | 电影 |
| 电影周度票房 | bo_weekly | 电影 |
| 电影月度票房 | bo_monthly | 电影 |
| 影院日度票房 | bo_cinema | 电影 |
| 全国电影剧本备案数据 | film_record | 广电 |
| 全国电视剧备案公示数据 | teleplay_record | 广电 |
| 国家政策库 | npr | 政策文本 |
| 新闻通讯(长篇) | major_news | 长篇新闻 |

---

## 重复/衍生接口 (8个) — 功能已被现有接口覆盖

| 接口文档 | API | 说明 |
|----------|-----|------|
| 复权行情 | pro_bar | 通过 adj_factor + daily 计算即可 |
| 港股复权行情 | hk_daily + hk_adjfactor | 已有组合替代 |
| 美股复权行情 | us_daily + us_adjfactor | 已有组合替代 |
| 周_月线行情(每日更新) | stk_weekly_monthly | 已有 weekly/monthly |
| 周_月线复权行情(每日更新) | — | 已有 weekly/monthly + adj_factor |
| 备用行情 | bak_daily | daily 的备用，不常用 |
| 通用行情接口 | pro_bar | 各品种行情已分别实现 |
| 数据索引 | — | 元数据索引页，非API |

---

## 低优先级可选接口 (32个) — 按需实现

### 港股/美股补充
| 接口文档 | API |
|----------|-----|
| 港股通每月成交统计 | ggt_monthly |
| 美股财务指标数据 | us_fina_indicator |

### 基金补充
| 接口文档 | API |
|----------|-----|
| 基金销售行业数据 | fund_sales_vol |
| 各渠道公募基金销售保有规模占比 | fund_sales_ratio |
| 销售机构公募基金销售保有规模 | fund_sales_vol |

### 板块/热榜补充
| 接口文档 | API |
|----------|-----|
| 同花顺App热榜数 | ths_hot |
| 榜单数据(开盘啦) | kpl_list |
| 东财概念和行业指数行情 | dc_daily |

### 债券/柜台
| 接口文档 | API |
|----------|-----|
| 柜台流通式债券报价 | bc_otcqt |
| 柜台流通式债券最优报价 | bc_bestotcqt |
| 大宗交易(债券) | bond_blk |
| 大宗交易明细(债券) | bond_blk_detail |

### 沪深市场补充
| 接口文档 | API |
|----------|-----|
| 深圳市场每日交易情况 | sz_daily_info |
| 沪深股通持股明细 | hk_hold |
| 中央结算系统持股统计 | ccass_hold |
| 北交所新旧代码对照 | bse_mapping |
| 股票历史列表 | bak_basic |

### 盘前/竞价
| 接口文档 | API |
|----------|-----|
| 每日股本(盘前) | stk_premarket |
| 融资融券标的(盘前) | margin_secs |
| 股票开盘集合竞价数据 | stk_auction_o |
| 股票收盘集合竞价数据 | stk_auction_c |
| 开盘竞价成交(当日) | stk_auction |

### 期货补充
| 接口文档 | API |
|----------|-----|
| 历史分钟行情(期货) | ft_mins |
| 实时分钟行情(期货) | rt_fut_min |
| 日线行情(南华) | fut_daily (重复?) |

### 其他
| 接口文档 | API |
|----------|-----|
| Shibor报价数据 | shibor_quote |
| 历史Tick行情 | tick_data |
| 转融资交易汇总 | slb_len |
| 神奇九转指标 | stk_nineturn |
| 上证e互动问答 | irm_qa_sh |
| 深证易互动问答 | irm_qa_sz |
| 台湾电子产业月营收 | tmt_twincome |
| 台湾电子产业月营收明细 | tmt_twincomedetail |
| 社区捐助 | — |
