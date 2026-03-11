"""
公告与研究 MCP Tools

包含：anns（上市公司公告）, stk_managers（管理层）, broker_recommend（券商月度金股）,
      research_report（券商研究报告）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将公告研究相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_anns(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司全量公告。需单独权限。

        Args:
            ts_code: 股票代码
            ann_date: 公告日期(YYYYMMDD 或 YYYY-MM-DD)
            start_date: 公告开始日期
            end_date: 公告结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.anns(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "anns_d", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_managers(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司管理层信息。积分要求:2000。

        Args:
            ts_code: 股票代码(支持多个)
            ann_date: 公告日期
            start_date: 公告开始日期
            end_date: 公告结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_managers(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_managers", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_broker_recommend(
        month: str,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询券商每月荐股(金股)数据。积分要求:6000。

        Args:
            month: 月度(YYYYMM格式,必填)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.broker_recommend(
                month=month,
                fields=fields,
            )
            return format_response(df, "broker_recommend", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_research_report(
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_type: Optional[str] = None,
        ts_code: Optional[str] = None,
        inst_csname: Optional[str] = None,
        ind_name: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询券商研究报告(含PDF下载链接)。需单独开权限。单次最大1000条。

        Args:
            trade_date: 研报日期(YYYYMMDD 或 YYYY-MM-DD)
            start_date: 研报开始日期
            end_date: 研报结束日期
            report_type: 研报类别(个股研报/行业研报)
            ts_code: 股票代码
            inst_csname: 券商名称
            ind_name: 行业名称
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.research_report(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type,
                ts_code=ts_code,
                inst_csname=inst_csname,
                ind_name=ind_name,
                fields=fields,
            )
            return format_response(df, "research_report", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
