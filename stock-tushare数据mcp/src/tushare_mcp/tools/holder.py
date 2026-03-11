"""
股东数据 MCP Tools

包含：stk_holdernumber（股东户数）, top10_holders（前十大股东）,
      top10_floatholders（前十大流通股东）, stk_holdertrade（股东增减持）,
      ccass_hold（中央结算系统持股明细）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将股东数据相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_stk_holdernumber(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        enddate: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司股东户数数据,数据不定期公布。积分要求:600。

        Args:
            ts_code: 股票代码(如 000001.SZ)
            ann_date: 公告日期
            enddate: 截止日期
            start_date: 公告开始日期
            end_date: 公告结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_holdernumber(
                ts_code=ts_code,
                ann_date=ann_date,
                enddate=enddate,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_holdernumber", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_top10_holders(
        ts_code: str,
        period: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司前十大股东数据,含持有数量和比例。积分要求:2000。

        Args:
            ts_code: 股票代码(如 000001.SZ,必填)
            period: 报告期(YYYYMMDD格式)
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.top10_holders(
                ts_code=ts_code,
                period=period,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "top10_holders", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_top10_floatholders(
        ts_code: str,
        period: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司前十大流通股东数据。积分要求:2000。

        Args:
            ts_code: 股票代码(如 000001.SZ,必填)
            period: 报告期(YYYYMMDD格式)
            ann_date: 公告日期
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.top10_floatholders(
                ts_code=ts_code,
                period=period,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "top10_floatholders", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_holdertrade(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        trade_type: Optional[str] = None,
        holder_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司股东增减持数据。积分要求:2000。

        Args:
            ts_code: TS股票代码
            ann_date: 公告日期
            start_date: 公告开始日期
            end_date: 公告结束日期
            trade_type: 交易类型(IN增持 DE减持)
            holder_type: 股东类型(C公司 P个人 G高管)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_holdertrade(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                trade_type=trade_type,
                holder_type=holder_type,
                fields=fields,
            )
            return format_response(df, "stk_holdertrade", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ccass_hold(
        ts_code: Optional[str] = None,
        hk_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询中央结算系统持股明细(港股通持股)。积分要求:8000。

        Args:
            ts_code: 股票代码(如 605009.SH)
            hk_code: 港交所代码(如 95009)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ccass_hold(
                ts_code=ts_code,
                hk_code=hk_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "ccass_hold_detail", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ccass_hold_stat(
        ts_code: Optional[str] = None,
        hk_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询中央结算系统持股汇总数据。积分要求:120+。当日数据次日早9点前入库。

        Args:
            ts_code: 股票代码(如 605009.SH)
            hk_code: 港交所代码(如 95009)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ccass_hold_stat(
                ts_code=ts_code,
                hk_code=hk_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "ccass_hold", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
