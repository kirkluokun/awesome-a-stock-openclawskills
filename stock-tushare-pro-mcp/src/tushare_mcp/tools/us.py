"""
美股行情 MCP Tools

包含：us_basic（美股基础信息）, us_tradecal（美股交易日历）,
      us_daily（美股日线）, us_adjfactor（美股复权因子）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将美股行情相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_us_basic(
        ts_code: Optional[str] = None,
        classify: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美股列表基础信息。积分要求:5000。

        Args:
            ts_code: 股票代码(如 AAPL)
            classify: 股票分类(ADR/GDR/EQ)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_basic(
                ts_code=ts_code,
                classify=classify,
                fields=fields,
            )
            return format_response(df, "us_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_tradecal(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_open: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美股交易日历。

        Args:
            start_date: 开始日期
            end_date: 结束日期
            is_open: 是否交易(0休市 1交易)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_tradecal(
                start_date=start_date,
                end_date=end_date,
                is_open=is_open,
                fields=fields,
            )
            return format_response(df, "us_tradecal", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美股日线行情(未复权)。积分不足时会返回错误,可 fallback 到其他数据源。

        Args:
            ts_code: 股票代码(如 AAPL)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_us_adjfactor(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询美股复权因子。需开通美股日线权限。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.us_adjfactor(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "us_adjfactor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
