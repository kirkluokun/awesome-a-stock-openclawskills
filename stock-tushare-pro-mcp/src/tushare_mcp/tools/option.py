"""
期权 MCP Tools

包含：opt_basic（期权合约信息）, opt_daily（期权日线行情）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将期权相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_opt_basic(
        ts_code: Optional[str] = None,
        exchange: Optional[str] = None,
        opt_code: Optional[str] = None,
        call_put: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期权合约信息。积分要求:5000。

        Args:
            ts_code: TS期权代码
            exchange: 交易所代码(SSE/SZSE/CFFEX/DCE/SHFE/CZCE)
            opt_code: 标准合约代码
            call_put: 期权类型(C认购 P认沽)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.opt_basic(
                ts_code=ts_code,
                exchange=exchange,
                opt_code=opt_code,
                call_put=call_put,
                fields=fields,
            )
            return format_response(df, "opt_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_opt_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期权日线行情。积分要求:2000。

        Args:
            ts_code: TS合约代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.opt_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "opt_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
