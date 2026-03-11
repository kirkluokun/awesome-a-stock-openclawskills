"""
融资融券 MCP Tools

包含：margin（融资融券汇总）, margin_detail（融资融券交易明细）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将融资融券相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_margin(
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange_id: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询融资融券每日交易汇总数据。积分要求:2000。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD)
            start_date: 开始日期
            end_date: 结束日期
            exchange_id: 交易所代码(SSE上交所/SZSE深交所/BSE北交所)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.margin(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange_id=exchange_id,
                fields=fields,
            )
            return format_response(df, "margin", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_margin_detail(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询沪深两市每日融资融券明细数据。积分要求:2000。

        Args:
            ts_code: 股票代码(如 000001.SZ)
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD)
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.margin_detail(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "margin_detail", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
