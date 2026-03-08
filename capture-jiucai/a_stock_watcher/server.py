"""
A股主题跟踪 MCP Server

通过 FastMCP 创建 MCP 服务器，提供主题抓取和多维查询工具。
定时抓取由外部 cron 调度（见 cli.py）。
启动方式：python -m a_stock_watcher
"""

from fastmcp import FastMCP

from .sources import SOURCES
from . import database
from .ai_parser import parse_article

# 创建 MCP 服务器实例
mcp = FastMCP(
    "A-Stock Watcher",
    instructions=(
        "A股主题跟踪工具。从九阳公社等平台抓取热点研究、产业链、异动等主题数据。"
        "使用 Gemini 2.5 Flash AI 自动提取股票、主题、投资逻辑，过滤噪音。"
        "支持按股票、主题、时间等多维度查询和溯源。"
    ),
)


# ─── 数据抓取 ───────────────────────────────────────────────────

@mcp.tool()
async def fetch_themes(source: str | None = None) -> dict:
    """
    抓取指定来源的主题数据 → AI 解析 → 入库（自动去重+噪音过滤）。

    Args:
        source: 数据源名称（study_hot / industry_chain / action）。
               不指定则抓取全部来源。
    """
    targets = {}
    if source:
        if source not in SOURCES:
            return {"error": f"未知数据源: {source}，可用: {list(SOURCES.keys())}"}
        targets[source] = SOURCES[source]
    else:
        targets = SOURCES

    results = {}
    for name, scraper_cls in targets.items():
        try:
            scraper = scraper_cls()
            articles = await scraper.run()
            saved, skipped, filtered = 0, 0, 0

            for article in articles:
                # 去重前置：先查DB，已存在的跳过不调AI
                if await database.check_exists(article.content_hash):
                    skipped += 1
                    continue

                # 如果已有解析结果（如 industry_chain 的图片解析），直接使用
                if article._parsed is not None:
                    parsed = article._parsed
                else:
                    parsed = await parse_article(article.title, article.content)
                result = await database.save_article(article, parsed)
                if result["status"] == "saved":
                    saved += 1
                elif result["status"] == "skipped":
                    skipped += 1
                elif result["status"] == "filtered":
                    filtered += 1

            results[name] = {
                "fetched": len(articles),
                "saved": saved,
                "skipped": skipped,
                "filtered": filtered,
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


@mcp.tool()
async def fetch_all() -> dict:
    """一次性抓取所有来源 → AI 解析 → 入库。"""
    return await fetch_themes()


# ─── 多维查询 ───────────────────────────────────────────────────

@mcp.tool()
async def list_sources() -> dict:
    """列出所有数据源及统计信息（数据量、最近抓取时间、股票/主题总数）。"""
    stats = await database.get_stats()
    sources_info = {}
    for name, scraper_cls in SOURCES.items():
        source_stats = stats.get("sources", {}).get(name, {})
        sources_info[name] = {
            "url": scraper_cls.source_url,
            "total_items": source_stats.get("count", 0),
            "last_fetch": source_stats.get("last_fetch", "从未抓取"),
        }
    sources_info["_summary"] = {
        "total_stocks": stats.get("total_stocks", 0),
        "total_themes": stats.get("total_themes", 0),
    }
    return sources_info


@mcp.tool()
async def query_by_stock(stock: str, limit: int = 50) -> list[dict]:
    """
    按股票查询相关文章和投资逻辑（时间倒序）。

    Args:
        stock: 股票代码（如 600519）或名称（如 贵州茅台）
        limit: 返回数量上限
    """
    return await database.query_by_stock(stock=stock, limit=limit)


@mcp.tool()
async def query_by_theme(theme: str, limit: int = 50) -> list[dict]:
    """
    按主题查询关联文章和股票。

    Args:
        theme: 主题名称（如 "白酒复苏"、"AI"）
        limit: 返回数量上限
    """
    return await database.query_by_theme(theme=theme, limit=limit)


@mcp.tool()
async def query_latest(days: int = 7, source: str | None = None, limit: int = 50) -> list[dict]:
    """
    查询最近 N 天的新增文章。

    Args:
        days: 天数范围，默认 7 天
        source: 可选，按数据源筛选
        limit: 返回数量上限
    """
    return await database.query_latest(days=days, source=source, limit=limit)


@mcp.tool()
async def get_stock_timeline(stock: str) -> list[dict]:
    """
    获取某只股票的逻辑演变时间线（按日期升序）。
    可用于溯源：看某公司的逻辑、段子是何时首次出现的。

    Args:
        stock: 股票代码或名称
    """
    return await database.get_stock_timeline(stock=stock)



def main() -> None:
    """启动 MCP 服务器（stdio 模式）"""
    mcp.run()


if __name__ == "__main__":
    main()
