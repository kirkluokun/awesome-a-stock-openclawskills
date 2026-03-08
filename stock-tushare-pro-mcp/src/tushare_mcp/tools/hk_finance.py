"""
港股财务 MCP Tools

包含：hk_income（港股利润表）, hk_balancesheet（港股资产负债表）,
      hk_cashflow（港股现金流量表）, hk_fina_indicator（港股财务指标）

注意：这些接口需要 15000 积分或单独开权限。积分不足时返回错误信息,
调用方可据此 fallback 到 Yahoo Finance 等其他数据源。
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将港股财务相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_hk_income(
        ts_code: str,
        period: Optional[str] = None,
        ind_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股利润表。需15000积分或单独开权限,积分不足会返回错误。

        Args:
            ts_code: 股票代码(如 00001.HK,必填)
            period: 报告期(YYYYMMDD)
            ind_name: 指标名(如 营业额)
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_income(
                ts_code=ts_code,
                period=period,
                ind_name=ind_name,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_income", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_balancesheet(
        ts_code: str,
        period: Optional[str] = None,
        ind_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股资产负债表。需15000积分或单独开权限,积分不足会返回错误。

        Args:
            ts_code: 股票代码(必填)
            period: 报告期(YYYYMMDD)
            ind_name: 指标名
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_balancesheet(
                ts_code=ts_code,
                period=period,
                ind_name=ind_name,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_balancesheet", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_cashflow(
        ts_code: str,
        period: Optional[str] = None,
        ind_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股现金流量表。需15000积分或单独开权限,积分不足会返回错误。

        Args:
            ts_code: 股票代码(必填)
            period: 报告期(YYYYMMDD)
            ind_name: 指标名
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_cashflow(
                ts_code=ts_code,
                period=period,
                ind_name=ind_name,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_cashflow", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_hk_fina_indicator(
        ts_code: str,
        period: Optional[str] = None,
        report_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询港股财务指标(PE/PB/ROE等)。需15000积分或单独开权限,积分不足会返回错误。

        Args:
            ts_code: 股票代码(必填)
            period: 报告期(YYYYMMDD)
            report_type: 报告期类型(Q1/Q2/Q3/Q4)
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.hk_fina_indicator(
                ts_code=ts_code,
                period=period,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "hk_fina_indicator", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
