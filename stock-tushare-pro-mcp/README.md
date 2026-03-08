# Tushare Pro MCP Server

A股金融数据 MCP 工具服务，基于 [Tushare Pro](https://tushare.pro/) API，通过 [FastMCP](https://github.com/jlowin/fastmcp) 以 stdio 模式运行。

## 概览

- **154 个 MCP Tools**，覆盖 Tushare 220 个接口的 70%
- **30 个功能模块**，按业务领域组织
- **167 个单元测试**，全部通过

## 数据覆盖

| 模块 | 文件 | Tools | 说明 |
|------|------|-------|------|
| A股行情 | stock.py | 10 | 日/周/月线、涨跌停、复权因子、停复牌、曾用名、IPO等 |
| 财务报表 | finance.py | 7 | 利润表、资产负债表、现金流量表、财务指标、审计、主营、披露日期 |
| 指数 | index.py | 8 | 指数行情（日/周/月）、基本信息、成分权重、国际指数、大盘指标 |
| 宏观经济 | macro.py | 19 | GDP、PMI、货币供应、社融、Shibor/Hibor/Libor、美国国债利率、LPR、黄金、民间借贷 |
| 业绩 | earnings.py | 3 | 业绩预告、快报、券商盈利预测 |
| 行业分类 | classify.py | 4 | 申万行业分类/成分、中信行业日行情/成分 |
| 新闻 | news.py | 2 | 新闻快讯、新闻联播 |
| 融资融券 | margin.py | 2 | 交易汇总、明细 |
| 龙虎榜 | billboard.py | 2 | 每日明细、机构交易 |
| 股东 | holder.py | 5 | 股东人数、前十大股东/流通股东、增减持、CCASS持股 |
| 公司行为 | corporate.py | 6 | 分红、回购、解禁、质押统计/明细、管理层薪酬 |
| 资金流向 | moneyflow.py | 5 | 资金流向、沪深港通资金、十大成交股、大宗交易 |
| 概念板块 | concept.py | 5 | 开盘啦概念/成分、同花顺指数/行情/成分 |
| 东财板块 | dc_board.py | 3 | 东财指数行情、板块成分、人气榜 |
| 通达信板块 | tdx_board.py | 3 | 通达信指数/日线/成分 |
| 涨跌停 | limit.py | 2 | 涨跌停统计、连板天梯 |
| 筹码分析 | chips.py | 2 | 筹码分布、筹码指标 |
| 游资 | hotmoney.py | 2 | 游资名录、每日明细 |
| 研究 | research.py | 3 | 上市公司公告、管理层、券商金股 |
| 港股 | hk.py + hk_finance.py | 9 | 基础信息、日线、复权因子、交易日历、港股通、三大财务报表、财务指标 |
| 美股 | us.py + us_finance.py | 7 | 基础信息、日线、复权因子、交易日历、三大财务报表 |
| 基金 | fund.py | 8 | 基金列表、净值、分红、持仓、管理人、经理、规模、复权因子 |
| ETF | etf.py | 4 | ETF基本信息、日线、份额规模、跟踪指数 |
| 期货 | futures.py | 9 | 主力映射、日线、仓单、涨跌停、周报、合约列表、结算参数、持仓排名、周月线 |
| 外汇 | forex.py | 2 | 基础信息、日线行情 |
| 期权 | option.py | 2 | 合约信息、日线行情 |
| 债券 | bond.py | 8 | 可转债基础/行情/发行/利率/赎回/转股结果/转股价变动、债券回购 |
| 分钟行情 | minutes.py | 6 | A股/港股/ETF/期权分钟行情、实时分钟 |

## 安装

```bash
# 克隆项目
cd openclaw-skills/tushare-pro-mcp

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"
```

## 配置

在 `~/.claude.json` 中注册 MCP 服务器：

```json
{
  "mcpServers": {
    "tushare-pro": {
      "command": "/path/to/tushare-pro-mcp/.venv/bin/python",
      "args": ["-m", "tushare_mcp.server"],
      "env": {
        "TUSHARE_API_KEY": "your_tushare_token_here"
      }
    }
  }
}
```

需要在 [Tushare Pro](https://tushare.pro/) 注册并获取 token。不同接口需要不同积分等级（120 ~ 10000+）。

> 环境变量说明：使用 `TUSHARE_API_KEY`。

## 架构

```
server.py (FastMCP) → tools/*.py → client.py → tushare API
                          ↓
                    formatter.py → JSON/Markdown
```

- **client.py**: 纯函数封装层，每个接口一个函数，统一日期格式化 + 频率限制
- **tools/*.py**: MCP tool 注册层，调用 client + formatter，捕获 TushareError
- **formatter.py**: DataFrame → `{api, total_rows, returned_rows, truncated, data}`
- **rate_limiter.py**: 300ms 最小调用间隔
- **errors.py**: TushareError / TokenError / ApiError 异常体系

## 使用

所有 tool 名称以 `tushare_` 开头，支持以下通用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `_format` | 输出格式 (`json` / `markdown`) | `json` |
| `_limit` | 最大返回行数 | `100` |

日期参数支持 `YYYYMMDD` 或 `YYYY-MM-DD` 两种格式。

示例：
```
tushare_daily(ts_code="000001.SZ", trade_date="2026-02-27")
tushare_income(ts_code="000001.SZ", period="20251231", _format="markdown")
tushare_index_daily(ts_code="000300.SH", start_date="2026-01-01", end_date="2026-02-27")
```

## 测试

```bash
.venv/bin/python -m pytest tests/ -v
```

## 未实现接口

约 66 个接口未实现，详见 [docs/remaining-apis.md](docs/remaining-apis.md)。主要包括：

- 已停用接口 (6个)
- 爬虫/实时数据 (7个)
- 技术面因子/专业版 (5个)
- 非金融数据 (8个)
- 重复/衍生接口 (8个)
- 低优先级可选 (32个)

## 开发

新增接口的标准流程：

1. `client.py` — 添加 API 函数
2. `tools/*.py` — 添加 MCP tool 注册
3. `server.py` — 注册新模块（如需新建模块）
4. `tests/` — 添加单元测试
5. `pytest tests/` — 确认全绿
