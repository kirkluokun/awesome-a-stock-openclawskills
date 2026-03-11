"""异动 — https://www.jiuyangongshe.com/action

实现方式（B计划 API拦截）：
- 拦截页面发出的 POST /v1/action/field 请求（带 date 参数）
- 一次请求返回当天全部板块 + 每板块内所有个股的异动解析
- 无需逐天导航 + 点击展开 DOM

API 响应结构：
    data: [{
        name,       # 板块名，如"电力"、"算力"
        reason,     # 板块整体解析
        date,       # 日期
        list: [{
            code,   # 股票代码，如 sh688525
            name,   # 股票名称
            article: {
                title,
                action_info: {
                    expound,  # 异动解析全文
                    price, shares_range, time, ...
                }
            }
        }]
    }]
"""

import json
import logging
from datetime import datetime, timedelta
from playwright.async_api import Page

from ..scraper import BaseScraper
from ..models import Article

logger = logging.getLogger("a_stock_watcher.action")


class ActionScraper(BaseScraper):
    source_name = "action"
    source_url = "https://www.jiuyangongshe.com/action"

    def __init__(self, headless: bool = False, lookback_days: int = 6):
        super().__init__(headless=headless)
        self.lookback_days = lookback_days

    async def parse(self, page: Page) -> list[Article]:
        today = datetime.now()
        dates = [
            (today - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(self.lookback_days)
        ]

        articles: list[Article] = []
        for date_str in dates:
            day_articles = await self._fetch_day(page, date_str)
            articles.extend(day_articles)
            logger.info(f"  action [{date_str}] 提取 {len(day_articles)} 个板块")

        return articles

    async def _fetch_day(self, page: Page, date_str: str) -> list[Article]:
        """拦截 action/field API，获取单日全部板块异动数据"""
        captured: list[dict] = []

        async def on_response(resp):
            if "/action/field" in resp.url and resp.request.resource_type in ("xhr", "fetch"):
                try:
                    body = await resp.json()
                    captured.append(body)
                except Exception:
                    pass

        page.on("response", on_response)
        await page.goto(
            f"{self.source_url}/{date_str}",
            wait_until="networkidle",
            timeout=30000,
        )
        await page.wait_for_timeout(2000)

        # 点"全部异动解析" tab 触发 action/field 请求
        tab = await page.query_selector('text="全部异动解析"')
        if tab:
            await tab.click()
            await page.wait_for_timeout(2000)

        page.remove_listener("response", on_response)

        if not captured:
            logger.warning(f"  [{date_str}] 未捕获 action/field 响应")
            return []

        # 取数据最多的响应
        best = max(captured, key=lambda b: len(b.get("data") or []))
        fields: list[dict] = best.get("data") or []

        articles: list[Article] = []
        for field in fields:
            field_name = (field.get("name") or "").strip()
            # 跳过"简图"（纯图表，无股票列表）
            if not field_name or field_name == "简图":
                continue

            stocks = field.get("list") or []
            if not stocks:
                continue

            # 每个板块聚合成一篇 Article
            lines: list[str] = []
            reason = (field.get("reason") or "").strip()
            if reason:
                lines.append(f"板块逻辑：{reason}\n")

            for stock in stocks:
                code = (stock.get("code") or "").strip()
                name = (stock.get("name") or "").strip()
                article = stock.get("article") or {}
                action_info = article.get("action_info") or {}
                expound = (action_info.get("expound") or "").strip()
                price = action_info.get("price")
                shares = action_info.get("shares_range")

                meta = ""
                if price:
                    meta += f" 价格={price}"
                if shares:
                    meta += f" 异动量={shares}万"

                if name:
                    line = f"【{name} {code}】{meta}"
                    if expound:
                        line += f"\n{expound}"
                    lines.append(line)

            content = "\n\n".join(lines)
            if not content.strip():
                continue

            articles.append(Article(
                title=f"[{date_str}异动] {field_name}（{len(stocks)}股）",
                source=self.source_name,
                url=f"{self.source_url}/{date_str}",
                content=content,
                images=[],
                publish_date=date_str,
            ))

        return articles
