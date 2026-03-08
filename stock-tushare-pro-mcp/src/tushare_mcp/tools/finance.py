"""
财务报表 MCP Tools

包含：income, balancesheet, cashflow, fina_indicator, fina_audit, fina_mainbz, disclosure_date
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将财务相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_income(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        report_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司利润表。积分要求：2000。单次最多返回100条，可通过日期分批获取。

        Args:
            ts_code: 股票代码（必填），如 000001.SZ
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            period: 报告期（如 20231231 表示年报）
            report_type: 报告类型（1合并报表 2单季合并等）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.income(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                report_type=report_type,
                fields=fields,
            )
            return format_response(df, "income", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_balancesheet(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        report_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司资产负债表。积分要求：2000。单次最多返回100条。

        Args:
            ts_code: 股票代码（必填）
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            period: 报告期
            report_type: 报告类型
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.balancesheet(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                report_type=report_type,
                fields=fields,
            )
            return format_response(df, "balancesheet", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_cashflow(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        report_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司现金流量表。积分要求：2000。单次最多返回100条。

        Args:
            ts_code: 股票代码（必填）
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            period: 报告期
            report_type: 报告类型
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.cashflow(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                report_type=report_type,
                fields=fields,
            )
            return format_response(df, "cashflow", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fina_indicator(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询财务指标数据（ROE、净利润率、毛利率等）。积分要求：2000。单次最多返回100条。

        Args:
            ts_code: 股票代码（必填）
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            period: 报告期（如 20231231）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.fina_indicator(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                fields=fields,
            )
            return format_response(df, "fina_indicator", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fina_audit(
        ts_code: str,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询财务审计意见。积分要求:500。

        Args:
            ts_code: 股票代码(必填)
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            period: 报告期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fina_audit(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                fields=fields,
            )
            return format_response(df, "fina_audit", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fina_mainbz(
        ts_code: str,
        period: Optional[str] = None,
        type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询主营业务构成,含按产品和按地区分类。积分要求:2000。

        Args:
            ts_code: 股票代码(必填)
            period: 报告期(YYYYMMDD)
            type: 类型(P按产品 D按地区,默认P)
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fina_mainbz(
                ts_code=ts_code,
                period=period,
                type=type,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fina_mainbz", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_disclosure_date(
        ts_code: Optional[str] = None,
        end_date: Optional[str] = None,
        pre_date: Optional[str] = None,
        actual_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询财报披露日期表。积分要求:500。

        Args:
            ts_code: 股票代码
            end_date: 财报周期(如20231231)
            pre_date: 计划披露日期
            actual_date: 实际披露日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.disclosure_date(
                ts_code=ts_code,
                end_date=end_date,
                pre_date=pre_date,
                actual_date=actual_date,
                fields=fields,
            )
            return format_response(df, "disclosure_date", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
