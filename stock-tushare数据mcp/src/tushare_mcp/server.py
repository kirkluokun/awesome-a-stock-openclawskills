"""
Tushare Pro MCP Server 入口

通过 FastMCP 创建 MCP 服务器，注册所有 tool 模块。
启动方式：python -m tushare_mcp.server
"""

from fastmcp import FastMCP

from .tools import (
    stock, finance, index, macro, earnings, classify, news,
    margin, billboard, holder, corporate, moneyflow, concept,
    hk, hk_finance, us, us_finance, fund, etf,
    futures, forex, option, bond, research,
    dc_board, tdx_board, limit, chips, hotmoney, minutes,
    data_store,
)

# 创建 MCP 服务器实例
mcp = FastMCP(
    "Tushare Pro",
    instructions=(
        "A股金融数据服务。通过 tushare_* 系列工具获取股票行情、财务报表、指数数据等。"
        "所有日期参数支持 YYYYMMDD 或 YYYY-MM-DD 格式。"
        "返回结果默认限制 100 行，可通过 _limit 参数调整。"
    ),
)

# 注册各模块的 tools
stock.register(mcp)
finance.register(mcp)
index.register(mcp)
macro.register(mcp)
earnings.register(mcp)
classify.register(mcp)
news.register(mcp)
margin.register(mcp)
billboard.register(mcp)
holder.register(mcp)
corporate.register(mcp)
moneyflow.register(mcp)
concept.register(mcp)
hk.register(mcp)
hk_finance.register(mcp)
us.register(mcp)
us_finance.register(mcp)
fund.register(mcp)
etf.register(mcp)
futures.register(mcp)
forex.register(mcp)
option.register(mcp)
bond.register(mcp)
research.register(mcp)
dc_board.register(mcp)
tdx_board.register(mcp)
limit.register(mcp)
chips.register(mcp)
hotmoney.register(mcp)
minutes.register(mcp)
data_store.register(mcp)


def main() -> None:
    """启动 MCP 服务器（stdio 模式）"""
    mcp.run()


if __name__ == "__main__":
    main()
