"""
龙虎榜 MCP Tools

包含：top_list（龙虎榜每日明细）, top_inst（龙虎榜机构交易明细）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将龙虎榜相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_top_list(
        trade_date: str,
        ts_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询龙虎榜每日交易明细,含涨跌幅、成交额、净买入等。积分要求:2000。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD,必填)
            ts_code: 股票代码
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.top_list(
                trade_date=trade_date,
                ts_code=ts_code,
                fields=fields,
            )
            return format_response(df, "top_list", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_top_inst(
        trade_date: str,
        ts_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询龙虎榜机构成交明细,含营业部名称、买卖额等。积分要求:5000。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD,必填)
            ts_code: 股票代码
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.top_inst(
                trade_date=trade_date,
                ts_code=ts_code,
                fields=fields,
            )
            return format_response(df, "top_inst", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
