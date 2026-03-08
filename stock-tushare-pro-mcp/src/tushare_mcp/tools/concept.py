"""
概念板块 MCP Tools

包含：concept（概念板块列表）, concept_detail（概念板块成分股）,
      ths_index（同花顺指数列表）, ths_daily（同花顺指数行情）, ths_member（同花顺概念成分）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将概念板块相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_concept(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        name: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询概念题材列表(开盘啦数据源),每日盘后更新。积分要求:5000。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD)
            ts_code: 题材代码(xxxxxx.KP格式)
            name: 题材名称
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.kpl_concept(
                trade_date=trade_date,
                ts_code=ts_code,
                name=name,
                fields=fields,
            )
            return format_response(df, "kpl_concept", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_concept_detail(
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        con_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询概念题材的成分股(开盘啦数据源)。积分要求:5000。

        Args:
            trade_date: 交易日期(YYYYMMDD 或 YYYY-MM-DD)
            ts_code: 题材代码(xxxxxx.KP格式)
            con_code: 成分股代码(如 000001.SZ)
            fields: 返回字段,逗号分隔
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.kpl_concept_cons(
                trade_date=trade_date,
                ts_code=ts_code,
                con_code=con_code,
                fields=fields,
            )
            return format_response(df, "kpl_concept_cons", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ths_index(
        ts_code: Optional[str] = None,
        exchange: Optional[str] = None,
        type: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询同花顺概念和行业指数列表。积分要求:6000。

        Args:
            ts_code: 指数代码
            exchange: 市场类型(A-A股 HK-港股 US-美股)
            type: 指数类型(N-概念 I-行业 R-地域 S-特色 ST-风格 TH-主题 BB-宽基)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ths_index(
                ts_code=ts_code,
                exchange=exchange,
                type=type,
                fields=fields,
            )
            return format_response(df, "ths_index", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ths_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询同花顺板块指数行情。积分要求:6000。

        Args:
            ts_code: 指数代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ths_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "ths_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ths_member(
        ts_code: Optional[str] = None,
        con_code: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询同花顺概念板块成分股。积分要求:6000。

        Args:
            ts_code: 板块指数代码
            con_code: 股票代码
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ths_member(
                ts_code=ts_code,
                con_code=con_code,
                fields=fields,
            )
            return format_response(df, "ths_member", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
