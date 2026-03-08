"""
DataFrame 格式转换

将 pandas DataFrame 转为 MCP tool 返回的标准格式。
支持 json 和 markdown 两种输出。
"""

import json
from typing import Any

import pandas as pd


def format_response(
    df: pd.DataFrame,
    api_name: str,
    output_format: str = "json",
    limit: int = 100,
) -> dict[str, Any]:
    """
    将 DataFrame 转换为 MCP tool 标准响应

    Args:
        df: tushare 返回的 DataFrame
        api_name: 接口名称，用于元信息
        output_format: 输出格式（json 或 markdown）
        limit: 最大返回行数

    Returns:
        标准响应字典，包含 api, total_rows, returned_rows, truncated, data
    """
    total_rows = len(df)
    truncated = total_rows > limit
    df_limited = df.head(limit)
    returned_rows = len(df_limited)

    if output_format == "markdown":
        data = _df_to_markdown(df_limited)
    else:
        data = _df_to_json(df_limited)

    return {
        "api": api_name,
        "total_rows": total_rows,
        "returned_rows": returned_rows,
        "truncated": truncated,
        "data": data,
    }


def _df_to_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrame → 字典列表，NaN 转为 None"""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _df_to_markdown(df: pd.DataFrame) -> str:
    """DataFrame → Markdown 表格"""
    if df.empty:
        return "*无数据*"
    return df.to_markdown(index=False)
