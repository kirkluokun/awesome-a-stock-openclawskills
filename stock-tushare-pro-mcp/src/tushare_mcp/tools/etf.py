"""
ETF MCP Tools

包含：fund_daily（场内基金/ETF日线行情）, etf_basic（ETF基本信息）,
      etf_share_size（ETF每日份额规模）, etf_index（ETF跟踪指数基准）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将 ETF 相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_fund_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询场内基金/ETF日线行情。积分要求:5000。

        Args:
            ts_code: 基金/ETF代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fund_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_etf_basic(
        ts_code: Optional[str] = None,
        index_code: Optional[str] = None,
        list_status: Optional[str] = None,
        exchange: Optional[str] = None,
        mgr: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询国内ETF基础信息,含QDII。积分要求:8000。

        Args:
            ts_code: ETF代码
            index_code: 跟踪指数代码
            list_status: 上市状态(L上市 D退市 P待上市)
            exchange: 交易所(SH上交所 SZ深交所)
            mgr: 管理人简称
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.etf_basic(
                ts_code=ts_code,
                index_code=index_code,
                list_status=list_status,
                exchange=exchange,
                mgr=mgr,
                fields=fields,
            )
            return format_response(df, "etf_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_etf_share_size(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询ETF每日份额规模。积分要求:8000。

        Args:
            ts_code: ETF代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所(SH/SZ)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.etf_share_size(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "etf_share_size", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_etf_index(
        ts_code: Optional[str] = None,
        pub_date: Optional[str] = None,
        base_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询ETF跟踪指数基准信息。积分要求:8000。

        Args:
            ts_code: ETF代码
            pub_date: 发布日期
            base_date: 基日
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.etf_index(
                ts_code=ts_code,
                pub_date=pub_date,
                base_date=base_date,
                fields=fields,
            )
            return format_response(df, "etf_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
