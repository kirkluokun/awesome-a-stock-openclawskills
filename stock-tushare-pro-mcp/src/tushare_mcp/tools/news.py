"""
新闻数据 MCP Tools

包含：news（新闻快讯）, cctv_news（新闻联播文字稿）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将新闻相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_news(
        start_date: str,
        end_date: str,
        src: str,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询新闻快讯（短讯）。需单独开权限。用于晨报隔夜事件。

        Args:
            start_date: 开始日期时间（格式：2024-01-01 09:00:00）
            end_date: 结束日期时间（格式：2024-01-01 18:00:00）
            src: 新闻来源（sina新浪/wallstreetcn华尔街见闻/10jqka同花顺/eastmoney东财/yuncaijing云财经）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.news(
                start_date=start_date,
                end_date=end_date,
                src=src,
                fields=fields,
            )
            return format_response(df, "news", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_cctv_news(
        date: str,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询新闻联播文字稿。需单独开权限。

        Args:
            date: 日期(必填,YYYYMMDD 或 YYYY-MM-DD)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.cctv_news(
                date=date,
                fields=fields,
            )
            return format_response(df, "cctv_news", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
