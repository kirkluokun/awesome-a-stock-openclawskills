"""CLI 入口 — 供 cron / launchd 等外部调度器调用

用法：
    # 抓取全部数据源
    uv run python -m a_stock_watcher.cli fetch

    # 抓取指定来源
    uv run python -m a_stock_watcher.cli fetch --source study_hot

    # 回补全文（对已有短内容文章用 crawl4ai 拉全文 + 重新 AI 解析）
    uv run python -m a_stock_watcher.cli backfill

    # 查看统计
    uv run python -m a_stock_watcher.cli stats

crontab 示例（每小时执行）：
    0 * * * * cd /path/to/capture-韭菜公社 && uv run python -m a_stock_watcher.cli fetch >> data/cron.log 2>&1
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def _load_dotenv():
    """从 skill 目录或上级目录加载 .env（不依赖第三方库）"""
    skill_dir = Path(__file__).parent.parent
    for env_path in [skill_dir / ".env", skill_dir.parent / ".env"]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:  # 已有环境变量的不覆盖
                os.environ[k] = v


_load_dotenv()

from .sources import SOURCES
from . import database
from .ai_parser import parse_article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("a_stock_watcher.cli")


async def cmd_fetch(source: str | None = None):
    """抓取→AI解析→入库"""
    targets = {source: SOURCES[source]} if source else SOURCES
    logger.info(f"开始抓取: {list(targets.keys())}")

    for name, scraper_cls in targets.items():
        try:
            scraper = scraper_cls()
            articles = await scraper.run()
            saved, skipped, filtered = 0, 0, 0

            updated = 0
            for article in articles:
                # 产业链：跳过前置去重，让 save_article 内部做 upsert（保留最新版本）
                # 其他来源：先查 DB，已存在的跳过，不浪费 AI 配额
                if article.source != "industry_chain":
                    if await database.check_exists(article.content_hash):
                        skipped += 1
                        continue

                # 如果已有解析结果，直接使用；否则调 Gemini 解析
                if article._parsed is not None:
                    parsed = article._parsed
                else:
                    parsed = await parse_article(article.title, article.content)
                result = await database.save_article(article, parsed)
                if result["status"] == "saved":
                    saved += 1
                elif result["status"] == "updated":
                    updated += 1
                elif result["status"] == "skipped":
                    skipped += 1
                elif result["status"] == "filtered":
                    filtered += 1

            logger.info(f"  [{name}] 抓取={len(articles)} 新增={saved} 更新={updated} 跳过={skipped} 过滤={filtered}")
        except Exception as e:
            logger.error(f"  [{name}] 错误: {e}")


async def cmd_backfill():
    """回补全文：用 Playwright 打开文章链接获取全文 + 重新 AI 解析"""
    from playwright.async_api import async_playwright
    from .scraper import AUTH_STATE_PATH
    from .content_fetcher import fetch_full_content_playwright

    articles = await database.get_articles_needing_backfill(max_content_len=500)
    logger.info(f"需要回补全文的文章: {len(articles)} 篇")

    if not articles:
        logger.info("无需回补，所有文章已有全文")
        return

    # 1. 启动 Playwright 浏览器（复用登录态）
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        if AUTH_STATE_PATH.exists():
            context = await browser.new_context(storage_state=str(AUTH_STATE_PATH))
        else:
            context = await browser.new_context()
        page = await context.new_page()

        # 2. Playwright 逐篇获取全文
        urls = [a["url"] for a in articles]
        fetched = await fetch_full_content_playwright(page, urls, delay=1.5)

        await browser.close()

    success_count = sum(1 for v in fetched.values() if v.success)
    logger.info(f"全文获取: {success_count}/{len(urls)} 成功")

    # 3. 逐篇更新内容 + 重新 AI 解析
    updated, ai_parsed, failed = 0, 0, 0
    for art in articles:
        fc = fetched.get(art["url"])
        if not fc or not fc.success or not fc.full_text:
            failed += 1
            continue

        # 用全文重新 AI 解析
        parsed = await parse_article(art["title"], fc.full_text)
        ai_parsed += 1

        # 更新数据库
        await database.update_article_content(
            article_id=art["id"],
            content=fc.full_text,
            publish_date=fc.publish_date,
            parsed=parsed if not parsed.parse_failed else None,
        )
        updated += 1

        if updated % 20 == 0:
            logger.info(f"  AI解析进度: {updated}/{len(articles)}")

    logger.info(f"回补完成: 更新={updated} AI解析={ai_parsed} 失败={failed}")


async def cmd_stats():
    """输出统计信息"""
    stats = await database.get_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="A股主题跟踪 CLI")
    sub = parser.add_subparsers(dest="command")

    fetch_parser = sub.add_parser("fetch", help="抓取数据")
    fetch_parser.add_argument("--source", choices=list(SOURCES.keys()), help="指定数据源")

    sub.add_parser("backfill", help="回补全文（crawl4ai 拉全文 + 重新AI解析）")
    sub.add_parser("stats", help="查看统计")

    args = parser.parse_args()

    if args.command == "fetch":
        asyncio.run(cmd_fetch(args.source))
    elif args.command == "backfill":
        asyncio.run(cmd_backfill())
    elif args.command == "stats":
        asyncio.run(cmd_stats())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
