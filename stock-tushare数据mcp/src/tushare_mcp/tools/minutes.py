"""
分钟行情 MCP Tools

包含：stk_mins（A股分钟）, hk_mins（港股分钟）, etf_mins（ETF分钟）,
      opt_mins（期权分钟）, rt_min（实时分钟）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将分钟行情相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_stk_mins(
        ts_code: str,
        freq: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询A股分钟行情。需特殊权限。

        Args:
            ts_code: 股票代码(必填)
            freq: 频率(必填,1min/5min/15min/30min/60min)
            start_date: 开始时间(支持YYYYMMDD HH:MM:SS)
            end_date: 结束时间
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_mins", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_mins(
        ts_code: str,
        freq: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股分钟行情。积分要求:120。

        Args:
            ts_code: 港股代码(必填)
            freq: 频率(必填,1min/5min/15min/30min/60min)
            start_date: 开始时间
            end_date: 结束时间
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_mins", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_etf_mins(
        ts_code: str,
        freq: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询ETF分钟行情。

        Args:
            ts_code: ETF代码(必填)
            freq: 频率(必填,1min/5min/15min/30min/60min)
            start_date: 开始时间
            end_date: 结束时间
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.etf_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "etf_mins", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_opt_mins(
        ts_code: str,
        freq: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期权分钟行情。积分要求:120。

        Args:
            ts_code: 期权合约代码(必填)
            freq: 频率(必填,1min/5min/15min/30min/60min)
            start_date: 开始时间
            end_date: 结束时间
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.opt_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "opt_mins", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_rt_min(
        ts_code: str,
        freq: str,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询实时分钟行情。需特殊权限。

        Args:
            ts_code: 股票代码(必填)
            freq: 频率(必填)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.rt_min(
                ts_code=ts_code,
                freq=freq,
                fields=fields,
            )
            return format_response(df, "rt_min", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
