"""
通达信板块 MCP Tools

包含：tdx_index（通达信板块指数行情）, tdx_daily（通达信板块日线行情）, tdx_member（通达信板块成分）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将通达信板块相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_tdx_index(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        idx_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询通达信板块指数行情。积分要求:6000。

        Args:
            ts_code: 指数代码
            trade_date: 交易日期
            idx_type: 指数类型
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.tdx_index(
                ts_code=ts_code,
                trade_date=trade_date,
                idx_type=idx_type,
                fields=fields,
            )
            return format_response(df, "tdx_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_tdx_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询通达信板块指数日线行情。积分要求:6000。

        Args:
            ts_code: 指数代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.tdx_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "tdx_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_tdx_member(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询通达信板块成分股。积分要求:6000。

        Args:
            ts_code: 板块指数代码
            trade_date: 交易日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.tdx_member(
                ts_code=ts_code,
                trade_date=trade_date,
                fields=fields,
            )
            return format_response(df, "tdx_member", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
