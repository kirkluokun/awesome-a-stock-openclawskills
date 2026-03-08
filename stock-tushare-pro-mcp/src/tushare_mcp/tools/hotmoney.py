"""
游资 MCP Tools

包含：hm_list（游资名录）, hm_detail（游资每日明细）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将游资相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_hm_list(
        name: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询游资名录。积分要求:5000。

        Args:
            name: 游资名称
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hm_list(
                name=name,
                fields=fields,
            )
            return format_response(df, "hm_list", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hm_detail(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        hm_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询游资每日交易明细。积分要求:10000。

        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            hm_name: 游资名称
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hm_detail(
                trade_date=trade_date,
                ts_code=ts_code,
                hm_name=hm_name,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hm_detail", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
