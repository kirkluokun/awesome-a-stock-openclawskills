"""
港股行情 MCP Tools

包含：hk_basic（港股基础信息）, hk_tradecal（港股交易日历）,
      hk_daily（港股日线）, hk_adjfactor（港股复权因子）, ggt_daily（港股通每日成交）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将港股行情相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_hk_basic(
        ts_code: Optional[str] = None,
        list_status: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股列表基础信息。积分要求:2000。

        Args:
            ts_code: TS代码(如 00001.HK)
            list_status: 上市状态(L上市 D退市 P暂停)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_basic(
                ts_code=ts_code,
                list_status=list_status,
                fields=fields,
            )
            return format_response(df, "hk_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_tradecal(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_open: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股交易日历。积分要求:2000。

        Args:
            start_date: 开始日期
            end_date: 结束日期
            is_open: 是否交易(0休市 1交易)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_tradecal(
                start_date=start_date,
                end_date=end_date,
                is_open=is_open,
                fields=fields,
            )
            return format_response(df, "hk_tradecal", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股日线行情。需单独开权限。积分不足时会返回错误,可 fallback 到其他数据源。

        Args:
            ts_code: 股票代码(如 00001.HK)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_adjfactor(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股每日复权因子。需开通港股日线权限。

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
            df = client.hk_adjfactor(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_adjfactor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ggt_daily(
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股通每日成交统计,数据从2014年开始。积分要求:2000。

        Args:
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ggt_daily(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "ggt_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
