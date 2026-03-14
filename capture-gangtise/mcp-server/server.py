#!/usr/bin/env python3
"""
冈特斯开放平台 MCP Server。

直接复用 ../scripts/ 里已有的客户端和查询函数，不重复实现逻辑。
提供 5 个工具：
  - gangtise_kb_search     知识库语义搜索（研报/公告/纪要）
  - gangtise_forecast      公司盈利预测（EPS/PE/ROE 等）
  - gangtise_indicator     经济数据指标 AI 查询
  - gangtise_meetings      电话会议/路演纪要列表
  - gangtise_download_url  溯源下载 URL 获取
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 复用已有 scripts，不动原始文件
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from fastmcp import FastMCP
from _client import post, post_stream, BASE_URL
from query_kb import query_knowledge, RT_NAMES
from forecast import query_forecast, KEY_FIELDS, FIELD_NAMES
from indicator import query_indicator
from meeting_list import query_meetings, PROCESS_MAP, METHOD_MAP

mcp = FastMCP("Gangtise KB", version="1.0.0")


# ─── 工具 1：知识库搜索 ──────────────────────────────────

@mcp.tool()
def gangtise_kb_search(
    query: str,
    resource_types: str = "10,40",
    top: int = 10,
    days: int = 365,
) -> str:
    """
    冈特斯知识库语义搜索。搜索券商研报、公告、会议纪要、分析师观点等。

    参数:
      query: 查询关键词，如 "振华股份铬盐" 或 "新能源汽车行业展望"
      resource_types: 资源类型（逗号分隔）
                      10=券商研报 20=内部研报 40=分析师观点 50=公告
                      60=会议纪要 70=调研纪要 80=网络资源 90=产业公众号
                      默认 "10,40"（研报+分析师观点）
      top: 返回数量，最多 20，默认 10
      days: 搜索最近 N 天，默认 365
    返回:
      格式化的搜索结果，含标题、公司、时间、内容摘要、sourceId
    """
    types = [int(t.strip()) for t in resource_types.split(",") if t.strip()]
    result = query_knowledge(query, types, min(top, 20), days)

    if not result or result.get("code") != "000000":
        msg = result.get("msg", "无响应") if result else "无响应"
        return f"查询失败: {msg}"

    data = result.get("data", [])
    if not data:
        return "无结果。"

    lines = []
    for query_result in data:
        items = query_result.get("data", [])
        if not items:
            lines.append("无匹配结果。")
            continue

        for i, item in enumerate(items, 1):
            rt = item.get("resourceType")
            ts = item.get("time")
            date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if ts else "N/A"
            source_id = item.get("sourceId", "")
            content = item.get("content", "")
            if len(content) > 600:
                content = content[:600] + "..."

            lines.append(f"\n[{i}] {item.get('title', 'N/A')}")
            lines.append(f"    公司: {item.get('company', 'N/A')} | 类型: {RT_NAMES.get(rt, rt)} | 日期: {date_str}")
            if source_id and rt != 40:
                lines.append(f"    SourceId: {source_id}")
            if content:
                lines.append(f"    摘要: {content}")

    return "\n".join(lines) if lines else "无结果。"


# ─── 工具 2：盈利预测 ────────────────────────────────────

@mcp.tool()
def gangtise_forecast(stock_code: str) -> str:
    """
    查询公司盈利预测（一致预期）。返回历年实际值和未来预测值。

    参数:
      stock_code: 股票代码，如 "603067.SH" 或 "000858.SZ"
    返回:
      含归母净利润、EPS、PE、ROE、营收等指标的多年预测表
    """
    result = query_forecast(stock_code)

    if not result or result.get("code") != "000000":
        msg = result.get("msg", "无响应") if result else "无响应"
        return f"查询失败: {msg}"

    items = result.get("data", [])
    if not items:
        return "无预测数据。"

    items.sort(key=lambda x: x.get("fincForeYear", ""))

    lines = [f"【{stock_code} 盈利预测】"]
    for item in items:
        year = item.get("fincForeYear", "N/A")
        # A=实际值 E=预测值
        suffix = "(实际)" if str(year).endswith("A") else "(预测)"
        lines.append(f"\n── {year} {suffix} ──")
        for field in KEY_FIELDS:
            val = item.get(field)
            if val is not None and val != "":
                lines.append(f"  {FIELD_NAMES.get(field, field)}: {val}")

    return "\n".join(lines)


# ─── 工具 3：经济数据指标 ────────────────────────────────

@mcp.tool()
def gangtise_indicator(text: str) -> str:
    """
    经济数据指标 AI 查询。用自然语言查询行业数据、宏观经济、公司经营指标。
    注意：非流式模式约等待 10-30 秒。

    参数:
      text: 自然语言查询，如 "铬盐行业2025年产能" 或 "2024年GDP增速"
    返回:
      AI 生成的数据分析回答
    """
    result = query_indicator(text, stream=False)

    if not result:
        return "查询失败或无响应。"

    if isinstance(result, str):
        return result

    if result.get("code") != "000000":
        return f"查询失败: {result.get('msg', '未知错误')}"

    choices = result.get("data", {}).get("choices", [])
    if not choices:
        return "无结果。"

    msg = choices[0].get("message", {})
    content = msg.get("content", "")
    return content if content else "无内容返回。"


# ─── 工具 4：电话会议列表 ────────────────────────────────

@mcp.tool()
def gangtise_meetings(
    stock: str | None = None,
    topic: str | None = None,
    days: int = 7,
    size: int = 10,
    page: int = 1,
) -> str:
    """
    查询电话会议、路演纪要列表。

    参数:
      stock: 股票代码过滤，如 "603067.SH"（可选）
      topic: 会议主题关键词过滤，如 "铬盐" 或 "新能源"（可选）
      days: 查询最近 N 天，默认 7
      size: 每页数量，默认 10
      page: 页码，默认 1
    返回:
      会议列表，含时间、主题、机构、摘要
    """
    stock_codes = [stock] if stock else None
    topics = [topic] if topic else None

    result = query_meetings(page, size, stock_codes, topics, days)

    if not result or result.get("code") != "000000":
        msg = result.get("msg", "无响应") if result else "无响应"
        return f"查询失败: {msg}"

    page_data = result.get("data", {})
    total = page_data.get("total", 0)
    items = page_data.get("list", [])

    if not items:
        return f"最近 {days} 天无会议记录。"

    lines = [f"共 {total} 条会议，当前显示 {len(items)} 条："]
    for item in items:
        cnfr_time = item.get("cnfrTime")
        time_str = datetime.fromtimestamp(cnfr_time / 1000).strftime("%m-%d %H:%M") if cnfr_time else "N/A"
        process = PROCESS_MAP.get(item.get("process"), str(item.get("process", "")))
        method = METHOD_MAP.get(item.get("cnfrCreateMethod"), "")

        lines.append(f"\n[{time_str}] {item.get('topic', 'N/A')}")
        lines.append(f"  机构: {item.get('partyName', 'N/A')} | 行业: {item.get('blockName', 'N/A')} | 状态: {process} | 类型: {method}")

        security = item.get("securityAbbr")
        if security:
            lines.append(f"  关联股票: {security} ({item.get('securityId', '')})")

        summary = item.get("summary", "")
        if summary:
            if len(summary) > 400:
                summary = summary[:400] + "..."
            lines.append(f"  摘要: {summary}")

    return "\n".join(lines)


# ─── 工具 5：溯源下载 URL ────────────────────────────────

@mcp.tool()
def gangtise_download_url(resource_type: int, source_id: str) -> str:
    """
    获取研报/纪要的溯源下载 URL（type 40 分析师观点不支持）。

    参数:
      resource_type: 资源类型（10=券商研报 20=内部研报 50=公告 60=会议纪要 70=调研纪要 80/90=网络资源）
      source_id: 来自 gangtise_kb_search 返回的 sourceId
    返回:
      下载链接或提示信息
    """
    if resource_type == 40:
        return "类型 40（分析师观点）不支持溯源下载。"

    url = f"{BASE_URL}/application/open-data/ai/resource/download?resourceType={resource_type}&sourceId={source_id}"
    return f"下载链接：{url}\n（注：部分券商研报有白名单限制，80/90 类型返回第三方 URL）"


if __name__ == "__main__":
    mcp.run()
