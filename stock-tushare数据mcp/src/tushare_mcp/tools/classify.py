"""
行业分类 MCP Tools

包含：index_classify（申万行业分类）, index_member_all（申万行业成分）,
      ci_daily（中信行业指数日行情）, ci_index_member（中信行业成分）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将行业分类相关 tools 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_index_classify(
        index_code: Optional[str] = None,
        level: Optional[str] = None,
        src: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询申万行业分类（2014版28个一级/2021版31个一级）。积分要求：2000。用于 comps 同行筛选。

        Args:
            index_code: 指数代码
            level: 行业级别（L1一级 L2二级 L3三级）
            src: 指数版本（SW2014 或 SW2021）
            fields: 返回字段
            _format: 输出格式（json/markdown）
            _limit: 最大返回行数
        """
        try:
            df = client.index_classify(
                index_code=index_code,
                level=level,
                src=src,
                fields=fields,
            )
            return format_response(df, "index_classify", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_index_member_all(
        l1_code: Optional[str] = None,
        l2_code: Optional[str] = None,
        l3_code: Optional[str] = None,
        ts_code: Optional[str] = None,
        is_new: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询申万行业成分(分级),支持一/二/三级。积分要求:2000。

        Args:
            l1_code: 一级行业代码
            l2_code: 二级行业代码
            l3_code: 三级行业代码
            ts_code: 股票代码
            is_new: 是否最新(Y/N,默认Y)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.index_member_all(
                l1_code=l1_code,
                l2_code=l2_code,
                l3_code=l3_code,
                ts_code=ts_code,
                is_new=is_new,
                fields=fields,
            )
            return format_response(df, "index_member_all", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ci_daily(
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询中信行业指数日行情。积分要求:5000。

        Args:
            ts_code: 行业代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ci_daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
            return format_response(df, "ci_daily", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}

    @mcp.tool()
    def tushare_ci_index_member(
        l1_code: Optional[str] = None,
        l2_code: Optional[str] = None,
        l3_code: Optional[str] = None,
        ts_code: Optional[str] = None,
        is_new: Optional[str] = None,
        fields: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """查询中信行业成分股。积分要求:5000。

        Args:
            l1_code: 一级行业代码
            l2_code: 二级行业代码
            l3_code: 三级行业代码
            ts_code: 股票代码
            is_new: 是否最新(Y/N,默认Y)
            fields: 返回字段
            _format: 输出格式(json/markdown),默认json
            _limit: 最大返回行数,默认100
        """
        try:
            df = client.ci_index_member(
                l1_code=l1_code,
                l2_code=l2_code,
                l3_code=l3_code,
                ts_code=ts_code,
                is_new=is_new,
                fields=fields,
            )
            return format_response(df, "ci_index_member", _format, _limit)
        except TushareError as e:
            return {"error": str(e)}
