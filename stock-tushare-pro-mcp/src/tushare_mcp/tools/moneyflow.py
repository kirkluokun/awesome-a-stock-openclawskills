"""
资金流向与港通 MCP Tools

包含：moneyflow（个股资金流向）, moneyflow_hsgt（沪深港通资金流向）,
      hsgt_top10（沪深港通十大成交股）, ggt_top10（港股通十大成交股）,
      block_trade（大宗交易）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将资金流向相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_moneyflow(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询个股资金流向数据,含大单/中单/小单/特大单买卖量和金额。

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
            df = client.moneyflow(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "moneyflow", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_moneyflow_hsgt(
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询沪深港通每日资金流向数据,含北向/南向资金。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD)
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.moneyflow_hsgt(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "moneyflow_hsgt", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hsgt_top10(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询沪股通/深股通每日前十大成交股详细数据。

        Args:
            ts_code: 股票代码(与 trade_date 二选一)
            trade_date: 交易日期(与 ts_code 二选一)
            start_date: 开始日期
            end_date: 结束日期
            market_type: 市场类型(1沪市 3深市)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hsgt_top10(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                market_type=market_type,
                fields=fields,
            )
            return format_response(df, "hsgt_top10", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ggt_top10(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股通每日成交数据,含沪市/深市详细数据。

        Args:
            ts_code: 股票代码(与 trade_date 二选一)
            trade_date: 交易日期(与 ts_code 二选一)
            start_date: 开始日期
            end_date: 结束日期
            market_type: 市场类型(2港股通沪 4港股通深)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ggt_top10(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                market_type=market_type,
                fields=fields,
            )
            return format_response(df, "ggt_top10", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_block_trade(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询大宗交易数据。积分要求:2000。

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
            df = client.block_trade(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "block_trade", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
