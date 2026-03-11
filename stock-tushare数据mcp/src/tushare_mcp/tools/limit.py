"""
涨跌停 MCP Tools

包含：limit_list_d（每日涨跌停统计）, limit_cpt_list（涨停股票连板天梯）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将涨跌停相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_limit_list_d(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        limit_type: Optional[str] = None,
        exchange: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询每日涨跌停统计(涨停/跌停/炸板)。积分要求:5000+。

        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            limit_type: 涨跌停类型(U涨停 D跌停 Z炸板)
            exchange: 交易所
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.limit_list_d(
                trade_date=trade_date,
                ts_code=ts_code,
                limit_type=limit_type,
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "limit_list_d", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_limit_cpt_list(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询涨停股票连板天梯。积分要求:8000。

        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.limit_cpt_list(
                trade_date=trade_date,
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "limit_cpt_list", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
