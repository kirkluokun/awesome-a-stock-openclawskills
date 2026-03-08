"""
期货 MCP Tools

包含：fut_mapping（主力与连续合约）, fut_daily（南华期货指数日线）,
      fut_wsr（仓单日报）, ft_limit（涨跌停价格）, fut_weekly_detail（交易周报）,
      fut_basic（期货合约列表）, fut_settle（结算参数）, fut_holding（持仓排名）,
      fut_wm（周/月线行情）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将期货相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_fut_mapping(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货主力与连续合约映射关系。积分要求:2000。

        Args:
            ts_code: 合约代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_mapping(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fut_mapping", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询南华期货指数日线行情(代码以.NH结尾)。积分要求:2000。

        Args:
            ts_code: 指数代码(以.NH结尾)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fut_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_wsr(
        trade_date: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货仓单日报。积分要求:2000。

        Args:
            trade_date: 交易日期
            symbol: 产品代码
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_wsr(
                trade_date=trade_date,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fut_wsr", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ft_limit(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货合约涨跌停价格。积分要求:5000。

        Args:
            ts_code: 合约代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ft_limit(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "ft_limit", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_weekly_detail(
        week: Optional[str] = None,
        prd: Optional[str] = None,
        start_week: Optional[str] = None,
        end_week: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货主要品种交易周报。积分要求:600。

        Args:
            week: 周期(如202001表示2020年第1周)
            prd: 期货品种(支持多品种逗号分隔)
            start_week: 开始周期
            end_week: 结束周期
            exchange: 交易所
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_weekly_detail(
                week=week,
                prd=prd,
                start_week=start_week,
                end_week=end_week,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fut_weekly_detail", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_basic(
        exchange: str,
        fut_type: Optional[str] = None,
        fut_code: Optional[str] = None,
        list_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货合约列表信息。积分要求:2000。

        Args:
            exchange: 交易所代码(必填,CFFEX/DCE/CZCE/SHFE/INE/GFEX)
            fut_type: 合约类型(1普通 2主力与连续)
            fut_code: 标准合约代码
            list_date: 上市开始日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_basic(
                exchange=exchange,
                fut_type=fut_type,
                fut_code=fut_code,
                list_date=list_date,
                fields=fields,
            )
            return format_response(df, "fut_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_settle(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货结算参数。积分要求:2000。

        Args:
            trade_date: 交易日期
            ts_code: 合约代码
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_settle(
                trade_date=trade_date,
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fut_settle", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_holding(
        trade_date: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货每日持仓排名。积分要求:2000。

        Args:
            trade_date: 交易日期
            symbol: 品种代码
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_holding(
                trade_date=trade_date,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fut_holding", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fut_wm(
        freq: str,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询期货周/月线行情。积分要求:2000。

        Args:
            freq: 频率(必填,W周线/M月线)
            ts_code: 合约代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fut_wm(
                freq=freq,
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fut_weekly_monthly", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
