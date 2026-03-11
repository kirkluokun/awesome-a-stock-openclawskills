"""产业链 — https://www.jiuyangongshe.com/industryChain

实现方式（B计划 API拦截）：
- 拦截页面发出的 POST /v1/industry/list 请求
- 直接从 API JSON 响应提取产业链结构化数据
- 无需点击详情页、截图、Gemini Vision 识别
- 速度从 ~5min → ~30s，且去掉了 Gemini 图像识别依赖

去重策略：
- content_hash 基于 industry_id（UUID），与 title 里的日期无关
- 同一产业链有新版本时，数据库做 upsert 保留最新内容

API 响应结构：
    data.result: [{
        industry_id, title, keyword, content,
        imgs: [...],  # 产业链信息图 URL 列表
    }]
"""

import hashlib
import json
import logging
from playwright.async_api import Page

from ..scraper import BaseScraper
from ..models import Article

logger = logging.getLogger("a_stock_watcher.industry_chain")


class IndustryChainScraper(BaseScraper):
    source_name = "industry_chain"
    source_url = "https://www.jiuyangongshe.com/industryChain"

    def __init__(self, headless: bool = False, max_items: int = 15):
        """
        Args:
            headless: 无头模式
            max_items: 最多返回的产业链条数（API 分页，pageSize 传入）
        """
        super().__init__(headless=headless)
        self.max_items = max_items

    async def parse(self, page: Page) -> list[Article]:
        captured: list[dict] = []

        # 只监听响应，不修改请求（修改 body 会导致 token 校验失败）
        async def on_response(resp):
            if "/industry/list" in resp.url and resp.request.resource_type in ("xhr", "fetch"):
                try:
                    body = await resp.json()
                    captured.append(body)
                except Exception:
                    pass

        page.on("response", on_response)

        # 重新加载页面，触发 industry/list API 请求
        await page.reload(wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        page.remove_listener("response", on_response)

        if not captured:
            logger.error("未捕获 industry/list API 响应，返回空列表")
            return []

        # 取数据最多的那次响应
        best = max(captured, key=lambda b: len((b.get("data") or {}).get("result", [])))
        result: list[dict] = (best.get("data") or {}).get("result", [])
        logger.info(f"industry/list API 返回 {len(result)} 条产业链")

        articles: list[Article] = []
        for rank, item in enumerate(result[:self.max_items], start=1):
            title = (item.get("title") or "").strip()
            industry_id = str(item.get("industry_id") or "")
            if not title:
                continue

            # content 字段：产业链文字描述（替代 Gemini Vision OCR）
            content = (item.get("content") or "").strip()
            keyword = (item.get("keyword") or "").strip()
            if keyword and keyword not in content:
                content = f"关键词：{keyword}\n\n{content}" if content else f"关键词：{keyword}"

            # imgs 字段：产业链信息图 URL（JSON 字符串，需要 parse）
            raw_imgs = item.get("imgs") or "[]"
            try:
                imgs: list[str] = json.loads(raw_imgs) if isinstance(raw_imgs, str) else raw_imgs
            except Exception:
                imgs = []

            article = Article(
                title=f"[产业链#{rank}] {title}",
                source=self.source_name,
                url=f"{self.source_url}/{industry_id}",  # URL 含 ID，便于查询
                content=content or title,
                images=imgs,
                publish_date="",
            )
            # 用 industry_id 建稳定 hash：同一产业链不同版本 hash 相同 → upsert 保留最新
            article.content_hash = hashlib.sha256(
                f"industry_chain:{industry_id}".encode()
            ).hexdigest()[:16]
            articles.append(article)

        logger.info(f"共提取 {len(articles)} 条产业链")
        return articles
