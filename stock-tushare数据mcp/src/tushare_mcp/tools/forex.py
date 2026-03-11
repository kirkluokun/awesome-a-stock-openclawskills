"""
外汇 MCP Tools

包含：fx_obasic（外汇基础信息）, fx_daily（外汇日线行情）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将外汇相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_fx_obasic(
        exchange: Optional[str] = None,
        classify: Optional[str] = None,
        ts_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询外汇基础信息(FXCM交易商)。积分要求:2000。

        Args:
            exchange: 交易商(如FXCM)
            classify: 分类(FX/INDEX/COMMODITY/METAL/BUND/CRYPTO/FX_BASKET)
            ts_code: TS代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fx_obasic(
                exchange=exchange,
                classify=classify,
                ts_code=ts_code,
                fields=fields,
            )
            return format_response(df, "fx_obasic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fx_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询外汇日线行情。积分要求:2000。

        Args:
            ts_code: TS代码(如USDCNH.FXCM)
            trade_date: 交易日期(GMT)
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易商(如FXCM)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fx_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "fx_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
