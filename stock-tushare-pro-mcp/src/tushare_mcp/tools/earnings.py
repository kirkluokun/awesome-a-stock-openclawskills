"""
业绩数据 MCP Tools

包含：forecast（业绩预告）, express（业绩快报）, report_rc（券商预测）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将业绩相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_forecast(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询业绩预告数据。积分要求：2000。ts_code 和 ann_date 至少填一个。

        Args:
            ts_code: 股票代码（与 ann_date 二选一）
            ann_date: 公告日期（与 ts_code 二选一）
            start_date: 公告开始日期
            end_date: 公告结束日期
            period: 报告期（如 20231231 年报、20240630 半年报）
            type: 预告类型（预增/预减/扭亏/首亏/续亏/续盈/略增/略减）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.forecast(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                type=type,
                fields=fields,
            )
            return format_response(df, "forecast", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_express(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询业绩快报数据。积分要求：2000。

        Args:
            ts_code: 股票代码（必填）
            ann_date: 公告日期
            start_date: 公告开始日期
            end_date: 公告结束日期
            period: 报告期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.express(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                fields=fields,
            )
            return format_response(df, "express", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_report_rc(
        ts_code: Optional[str] = None,
        report_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询券商（卖方）盈利预测数据，包含EPS预期、目标价、评级等。积分要求：8000。

        Args:
            ts_code: 股票代码
            report_date: 报告日期
            start_date: 报告开始日期
            end_date: 报告结束日期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.report_rc(
                ts_code=ts_code,
                report_date=report_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "report_rc", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
