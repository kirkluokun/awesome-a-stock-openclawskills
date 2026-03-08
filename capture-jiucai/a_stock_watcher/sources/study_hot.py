"""热点研究 — https://www.jiuyangongshe.com/study_hot

实现方式（B计划 API拦截）：
- 拦截页面发出的 POST /v1/timeline/news 请求，注入 limit 参数
- 直接从 API JSON 响应提取文章列表和全文内容
- 无需逐篇打开链接，速度从 5-15min → ~30s

API 响应结构：
    data: [{date, list: [{article_id, title, content, timeline, user: {username}}]}]
"""

import json
import logging
from playwright.async_api import Page

from ..scraper import BaseScraper
from ..models import Article

logger = logging.getLogger("a_stock_watcher.sources.study_hot")


class StudyHotScraper(BaseScraper):
    source_name = "study_hot"
    source_url = "https://www.jiuyangongshe.com/study_hot"

    def __init__(self, headless: bool = False, scroll_rounds: int = 5):
        """
        Args:
            headless: 无头模式
            scroll_rounds: 兼容旧接口，映射为 limit（每轮约 5 条，最多 30）
        """
        super().__init__(headless=headless)
        # scroll_rounds 保持接口兼容，映射到 API limit（最大 30）
        self.limit = min(scroll_rounds * 5, 30)

    async def parse(self, page: Page) -> list[Article]:
        captured: list[dict] = []

        # 拦截 timeline/news 请求，注入 limit 参数
        async def intercept(route):
            if "/timeline/news" in route.request.url:
                await route.continue_(
                    post_data=json.dumps({"limit": self.limit}),
                )
            else:
                await route.continue_()

        async def on_response(resp):
            if "timeline/news" in resp.url and resp.request.resource_type in ("xhr", "fetch"):
                try:
                    body = await resp.json()
                    captured.append(body)
                except Exception:
                    pass

        await page.route("**/*", intercept)
        page.on("response", on_response)

        # 重新加载页面，触发 timeline/news API 请求
        await page.reload(wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)  # 等待响应处理完成

        await page.unroute("**/*", intercept)
        page.remove_listener("response", on_response)

        if not captured:
            logger.error("未捕获 timeline/news API 响应，返回空列表")
            return []

        # 取最后一次响应（可能多次触发，取数据最多的那次）
        news_body = max(captured, key=lambda b: len(b.get("data", [])))
        days: list[dict] = news_body.get("data", [])
        logger.info(f"timeline/news API 返回 {len(days)} 天数据")

        articles: list[Article] = []
        for day in days:
            for item in day.get("list", []):
                article_id = str(item.get("article_id", ""))
                title = (item.get("title") or "").strip()
                if not title or len(title) < 3:
                    continue

                content = (item.get("content") or "").strip() or title
                # date 字段是当天日期（timeline 是嵌套结构，不是日期字符串）
                pub_date = str(day.get("date") or "")[:10]
                url = (
                    f"https://www.jiuyangongshe.com/a/{article_id}"
                    if article_id else self.source_url
                )

                articles.append(Article(
                    title=title,
                    source=self.source_name,
                    url=url,
                    content=content,
                    images=[],
                    publish_date=pub_date,
                ))

        logger.info(f"共提取 {len(articles)} 篇文章")
        return articles
