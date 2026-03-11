"""
基金 MCP Tools

包含：fund_basic（基金列表）, fund_nav（基金净值）, fund_div（基金分红）,
      fund_portfolio（基金持仓）, fund_company（基金管理人）,
      fund_manager（基金经理）, fund_share（基金规模）, fund_adj（基金复权因子）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将基金相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_fund_basic(
        ts_code: Optional[str] = None,
        market: Optional[str] = None,
        status: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金列表,含场内和场外基金。积分要求:2000。

        Args:
            ts_code: 基金代码
            market: 交易市场(E场内 O场外),默认E
            status: 存续状态(D摘牌 I发行 L上市中)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_basic(
                ts_code=ts_code,
                market=market,
                status=status,
                fields=fields,
            )
            return format_response(df, "fund_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_nav(
        ts_code: Optional[str] = None,
        nav_date: Optional[str] = None,
        market: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金净值数据。积分要求:2000。

        Args:
            ts_code: 基金代码(与 nav_date 二选一)
            nav_date: 净值日期(与 ts_code 二选一)
            market: E场内 O场外
            start_date: 净值开始日期
            end_date: 净值结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_nav(
                ts_code=ts_code,
                nav_date=nav_date,
                market=market,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fund_nav", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_div(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        ex_date: Optional[str] = None,
        pay_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金分红数据。积分要求:400。

        Args:
            ts_code: 基金代码(四选一)
            ann_date: 公告日(四选一)
            ex_date: 除息日(四选一)
            pay_date: 派息日(四选一)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_div(
                ts_code=ts_code,
                ann_date=ann_date,
                ex_date=ex_date,
                pay_date=pay_date,
                fields=fields,
            )
            return format_response(df, "fund_div", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_portfolio(
        ts_code: Optional[str] = None,
        symbol: Optional[str] = None,
        ann_date: Optional[str] = None,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金持仓数据,季度更新。积分要求:5000。

        Args:
            ts_code: 基金代码(三选一)
            symbol: 股票代码(三选一)
            ann_date: 公告日期(三选一)
            period: 季度
            start_date: 报告期开始日期
            end_date: 报告期结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_portfolio(
                ts_code=ts_code,
                symbol=symbol,
                ann_date=ann_date,
                period=period,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fund_portfolio", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_company(
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金管理人列表。积分要求:1500。

        Args:
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_company(fields=fields)
            return format_response(df, "fund_company", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_manager(
        ts_code: Optional[str] = None,
        ann_date: Optional[str] = None,
        name: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询公募基金经理数据,含简历信息。积分要求:500。

        Args:
            ts_code: 基金代码(支持多只,逗号分隔)
            ann_date: 公告日期
            name: 基金经理姓名
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_manager(
                ts_code=ts_code,
                ann_date=ann_date,
                name=name,
                fields=fields,
            )
            return format_response(df, "fund_manager", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_share(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询基金规模数据,含ETF份额。积分要求:2000。

        Args:
            ts_code: 基金代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            market: 市场代码(SH上交所 SZ深交所)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_share(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                market=market,
                fields=fields,
            )
            return format_response(df, "fund_share", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_fund_adj(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询基金复权因子。积分要求:600。

        Args:
            ts_code: 基金代码(支持多只输入)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.fund_adj(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "fund_adj", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
