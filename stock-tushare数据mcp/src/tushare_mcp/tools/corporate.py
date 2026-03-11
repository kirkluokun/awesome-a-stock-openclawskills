"""
公司行为 MCP Tools

包含：dividend（分红送股）, repurchase（股票回购）, share_float（限售股解禁）,
      pledge_stat（股权质押统计）, pledge_detail（股权质押明细）, stk_surv（机构调研）,
      stk_rewards（管理层薪酬和持股）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将公司行为相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_dividend(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        record_date: Optional[str] = None,
        ex_date: Optional[str] = None,
        imp_ann_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询分红送股数据,含每股分红、送转比例、除权除息日等。积分要求:2000。
        注意:参数中至少一个不能为空。

        Args:
            ts_code: 股票代码(如 000001.SZ)
            ann_date: 预案公告日
            record_date: 股权登记日期
            ex_date: 除权除息日
            imp_ann_date: 实施公告日
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.dividend(
                ts_code=ts_code,
                ann_date=ann_date,
                record_date=record_date,
                ex_date=ex_date,
                imp_ann_date=imp_ann_date,
                fields=fields,
            )
            return format_response(df, "dividend", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_repurchase(
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司回购股票数据。积分要求:600。

        Args:
            ann_date: 公告日期
            start_date: 公告开始日期
            end_date: 公告结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.repurchase(
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "repurchase", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_share_float(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        float_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询限售股解禁数据。积分要求:120。

        Args:
            ts_code: 股票代码
            ann_date: 公告日期
            float_date: 解禁日期
            start_date: 解禁开始日期
            end_date: 解禁结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.share_float(
                ts_code=ts_code,
                ann_date=ann_date,
                float_date=float_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "share_float", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_pledge_stat(
        ts_code: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询股票质押统计数据,含质押次数、质押比例等。积分要求:500。

        Args:
            ts_code: 股票代码
            end_date: 截止日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.pledge_stat(
                ts_code=ts_code,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "pledge_stat", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_pledge_detail(
        ts_code: str,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询股票质押明细数据,含质押方、质押数量、起止日期等。积分要求:500。

        Args:
            ts_code: 股票代码(如 000001.SZ,必填)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.pledge_detail(
                ts_code=ts_code,
                fields=fields,
            )
            return format_response(df, "pledge_detail", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_surv(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司机构调研记录数据。积分要求:5000。

        Args:
            ts_code: 股票代码
            trade_date: 调研日期
            start_date: 调研开始日期
            end_date: 调研结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_surv(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_surv", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_rewards(
        ts_code: str,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询管理层薪酬和持股数据。积分要求:2000。

        Args:
            ts_code: TS股票代码(必填,支持多个)
            end_date: 报告期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_rewards(
                ts_code=ts_code,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_rewards", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
