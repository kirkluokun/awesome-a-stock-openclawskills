"""
股票数据 MCP Tools

包含：stock_basic, daily, daily_basic, adj_factor, weekly, monthly, stk_limit,
      namechange, suspend_d, new_share, stock_company, stock_hsgt, stock_st,
      stk_ah_comparison, stk_factor_pro
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将股票相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_stock_basic(
        ts_code: Optional[str] = None,
        name: Optional[str] = None,
        market: Optional[str] = None,
        list_status: Optional[str] = None,
        exchange: Optional[str] = None,
        is_hs: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询股票列表基础信息（代码、名称、上市日期、行业等）。积分要求：2000。

        Args:
            ts_code: TS股票代码，如 000001.SZ
            name: 股票名称
            market: 市场类别（主板/创业板/科创板/CDR/北交所）
            list_status: 上市状态（L上市 D退市 P暂停），默认L
            exchange: 交易所（SSE上交所 SZSE深交所 BSE北交所）
            is_hs: 是否沪深港通（N否 H沪股通 S深股通）
            fields: 返回字段，逗号分隔
            _format: 输出格式（json/markdown），默认json
            _limit: 最大返回行数，默认100
        """
        try:
            df = client.stock_basic(
                ts_code=ts_code,
                name=name,
                market=market,
                list_status=list_status,
                exchange=exchange,
                is_hs=is_hs,
                fields=fields,
            )
            return format_response(df, "stock_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询A股日线行情（开高低收、成交量等）。积分要求：2000。
        ts_code 和 trade_date 必须至少填一个。

        Args:
            ts_code: 股票代码，如 000001.SZ
            trade_date: 交易日期（YYYYMMDD 或 YYYY-MM-DD）
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_daily_basic(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询每日指标（PE、PB、总市值、流通市值、换手率等）。积分要求：2000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.daily_basic(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "daily_basic", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_adj_factor(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询复权因子，用于计算前复权/后复权价格。积分要求：2000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.adj_factor(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "adj_factor", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_weekly(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询A股周线行情。积分要求:2000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.weekly(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "weekly", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_monthly(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询A股月线行情。积分要求:2000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.monthly(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "monthly", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_limit(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询每日涨跌停价格。积分要求:2000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_limit(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_limit", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_namechange(
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询股票曾用名,历次更名记录。

        Args:
            ts_code: TS股票代码
            start_date: 公告开始日期
            end_date: 公告结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.namechange(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "namechange", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_suspend_d(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        suspend_type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询每日停复牌信息。

        Args:
            ts_code: 股票代码(可输入多值)
            trade_date: 交易日期
            start_date: 停复牌查询开始日期
            end_date: 停复牌查询结束日期
            suspend_type: 停复牌类型(S-停牌 R-复牌)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.suspend_d(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                suspend_type=suspend_type,
                fields=fields,
            )
            return format_response(df, "suspend_d", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_new_share(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询IPO新股列表。积分要求:120。

        Args:
            start_date: 上网发行开始日期
            end_date: 上网发行结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.new_share(
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "new_share", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stock_company(
        ts_code: Optional[str] = None,
        exchange: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询上市公司基本信息(注册地、法人、总经理、董秘等)。积分要求:120。

        Args:
            ts_code: 股票代码
            exchange: 交易所代码(SSE/SZSE/BSE)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stock_company(
                ts_code=ts_code,
                exchange=exchange,
                fields=fields,
            )
            return format_response(df, "stock_company", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stock_hsgt(
        type: str,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询沪深港通股票列表。积分要求:3000。

        Args:
            type: 类型(必填,HK_SZ深股通 SZ_HK港股通深 HK_SH沪股通 SH_HK港股通沪)
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stock_hsgt(
                type=type,
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stock_hsgt", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stock_st(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询ST股票列表。积分要求:3000。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stock_st(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stock_st", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_ah_comparison(
        hk_code: Optional[str] = None,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询AH股比价数据。积分要求:5000。

        Args:
            hk_code: 港股股票代码(xxxxx.HK)
            ts_code: A股股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_ah_comparison(
                hk_code=hk_code,
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_ah_comparison", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_factor_pro(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询股票每日技术面因子(专业版)，含MA/MACD/KDJ/BOLL/RSI/WR/CCI等指标。积分要求:5000。

        输出字段后缀说明：_bfq不复权，_qfq前复权，_hfq后复权。
        建议通过fields参数指定所需因子，避免数据过大。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段，如 'ts_code,trade_date,close_qfq,macd_qfq,kdj_k_qfq'
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_factor_pro(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_factor_pro", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_stk_nineturn(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        freq: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询神奇九转指标(TD序列)，识别股价潜在反转点。积分要求:6000。

        数据从20230101开始，每天21点更新。日线配合60min效果更佳。
        日期格式：YYYY-MM-DD HH:MM:SS 或 YYYYMMDD。

        Args:
            ts_code: 股票代码
            trade_date: 交易日期(YYYY-MM-DD HH:MM:SS)
            freq: 频率(daily)
            start_date: 开始时间
            end_date: 结束时间
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.stk_nineturn(
                ts_code=ts_code,
                trade_date=trade_date,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "stk_nineturn", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
