"""
数据存储 MCP Tools

提供本地数据查询能力：
- tushare_data_index: 查询保存记录索引
- tushare_data_read: 从本地 DB 读取历史数据（不调 API）
"""

from typing import Optional

from fastmcp import FastMCP

from .. import client
from ..formatter import format_response
from ..errors import TushareError


def register(mcp: FastMCP) -> None:
    """将数据存储查询 tool 注册到 MCP 实例"""

    @mcp.tool()
    def tushare_data_index(
        api_name: Optional[str] = None,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        _format: str = "json",
        _limit: int = 50,
    ) -> dict:
        """查询本地已保存的数据索引。每次调用 tushare_* tool 获取的数据都会自动保存到本地 SQLite。
        使用此接口可以查看历史保存了哪些数据，方便回溯。

        Args:
            api_name: 按接口名筛选（如 daily, income, index_daily）
            ts_code: 按股票/标的代码筛选（如 000001.SZ）
            start_date: 保存时间起始（YYYY-MM-DD），筛选 saved_at 字段
            end_date: 保存时间截止（YYYY-MM-DD），筛选 saved_at 字段
            _format: 输出格式（json/markdown），默认 json
            _limit: 最大返回行数，默认 50
        """
        try:
            store = client._get_store()
            df = store.query_index(
                api_name=api_name,
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                limit=_limit,
            )
            return format_response(df, "data_index", _format, _limit)
        except Exception as e:
            return {"error": f"查询数据索引失败: {e}"}

    @mcp.tool()
    def tushare_data_read(
        query_id: Optional[int] = None,
        api_name: Optional[str] = None,
        ts_code: Optional[str] = None,
        _format: str = "json",
        _limit: int = 100,
    ) -> dict:
        """从本地数据库读取历史保存的数据，不调用 tushare API。
        三种查询模式：
        1. 按 query_id 读取某次查询的完整数据（最精确）
        2. 按 api_name 读取某类数据的最新记录
        3. 按 api_name + ts_code 读取特定标的的历史数据

        建议先用 tushare_data_index 查到 query_id，再用本接口读取。

        Args:
            query_id: 索引记录 id（从 tushare_data_index 获取）
            api_name: 接口名称（如 daily, income, index_daily）
            ts_code: 股票/标的代码（需配合 api_name 使用）
            _format: 输出格式（json/markdown），默认 json
            _limit: 最大返回行数，默认 100
        """
        try:
            store = client._get_store()
            df = store.read_data(
                query_id=query_id,
                api_name=api_name,
                ts_code=ts_code,
                limit=_limit,
            )
            source = f"local:{api_name or 'query_' + str(query_id)}"
            return format_response(df, source, _format, _limit)
        except Exception as e:
            return {"error": f"读取本地数据失败: {e}"}
