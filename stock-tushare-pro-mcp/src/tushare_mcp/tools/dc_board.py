"""
东财板块 MCP Tools

包含：dc_index（东财概念和行业指数行情）, dc_member（东财板块成分）, dc_hot（东财人气榜）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将东财板块相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_dc_index(
        ts_code: Optional[str] = None,
        name: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询东财概念和行业指数行情。积分要求:6000。

        Args:
            ts_code: 指数代码
            name: 指数名称
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.dc_index(
                ts_code=ts_code,
                name=name,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "dc_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_dc_member(
        ts_code: Optional[str] = None,
        con_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询东财概念和行业板块成分。积分要求:6000。

        Args:
            ts_code: 板块指数代码
            con_code: 成分股代码
            trade_date: 交易日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.dc_member(
                ts_code=ts_code,
                con_code=con_code,
                trade_date=trade_date,
                fields=fields,
            )
            return format_response(df, "dc_member", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_dc_hot(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        market: Optional[str] = None,
        hot_type: Optional[str] = None,
        is_new: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询东财人气榜(热股数据)。积分要求:8000。

        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            market: 市场
            hot_type: 热度类型
            is_new: 是否最新
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.dc_hot(
                trade_date=trade_date,
                ts_code=ts_code,
                market=market,
                hot_type=hot_type,
                is_new=is_new,
                fields=fields,
            )
            return format_response(df, "dc_hot", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
