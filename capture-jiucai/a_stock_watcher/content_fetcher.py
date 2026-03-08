"""Playwright 全文抓取模块 — 在已登录浏览器中逐篇获取文章全文 + 日期

功能：
- 复用 Playwright 浏览器会话（已登录状态）
- 逐篇打开文章 URL，提取全文 + 精确发布日期
- 自动等待 JS 渲染
- 请求间隔控制避免触发反爬
"""

import asyncio
import re
import logging
from dataclasses import dataclass
from playwright.async_api import Page, Browser

logger = logging.getLogger("a_stock_watcher.content_fetcher")


@dataclass
class FetchedContent:
    """单篇文章的全文抓取结果"""
    url: str
    full_text: str = ""
    publish_date: str = ""
    success: bool = False
    error: str = ""


def _extract_date(text: str) -> str:
    """从文本中提取发布日期"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})\s*\d{2}:\d{2}:\d{2}', text)
    if match:
        return match.group(1)
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)
    return ""


# JS 脚本：提取文章全文 + 日期
EXTRACT_ARTICLE_JS = r"""() => {
    // 提取日期
    const allText = document.body.innerText || '';
    const dateMatch = allText.match(/(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})/);
    const publishDate = dateMatch ? dateMatch[1].substring(0, 10) : '';
    
    // 提取正文：优先找文章内容容器
    let content = '';
    
    // 九阳公社文章页的内容选择器
    const selectors = [
        '.article-content',
        '.rich-text',
        '.post-content',
        '.detail-content',
        '[class*="content"]',
        '[class*="article"]',
    ];
    
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText.length > 200) {
            content = el.innerText;
            break;
        }
    }
    
    // 如果选择器没找到，取 body 文本但去掉导航
    if (!content || content.length < 200) {
        content = document.body.innerText || '';
    }
    
    return {
        content: content.substring(0, 15000),  // 限制长度
        publishDate: publishDate,
    };
}"""


async def fetch_full_content_playwright(
    page: Page,
    urls: list[str],
    delay: float = 1.5,
) -> dict[str, FetchedContent]:
    """
    在已打开的 Playwright page 中逐篇获取文章全文。

    Args:
        page: 已登录的 Playwright Page 对象
        urls: 要抓取的 URL 列表（自动去重）
        delay: 每篇之间的延迟（秒）

    Returns:
        {url: FetchedContent} 字典
    """
    # URL 去重（保持顺序）
    unique_urls = list(dict.fromkeys(urls))
    if len(unique_urls) < len(urls):
        logger.info(f"  URL 去重: {len(urls)} → {len(unique_urls)} 个唯一 URL")

    results: dict[str, FetchedContent] = {}

    for i, url in enumerate(unique_urls):
        try:
            await page.goto(url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)  # 额外等待 JS 渲染

            data = await page.evaluate(EXTRACT_ARTICLE_JS)
            content = data.get("content", "")
            pub_date = data.get("publishDate", "")

            if content and len(content) > 100:
                results[url] = FetchedContent(
                    url=url,
                    full_text=content,
                    publish_date=pub_date,
                    success=True,
                )
            else:
                results[url] = FetchedContent(
                    url=url,
                    success=False,
                    error=f"content_len={len(content)}",
                )
        except Exception as e:
            logger.error(f"  抓取异常 {url}: {e}")
            results[url] = FetchedContent(
                url=url,
                success=False,
                error=str(e)[:100],
            )

        # 进度日志
        if (i + 1) % 5 == 0:
            ok = sum(1 for v in results.values() if v.success)
            logger.info(f"  全文抓取进度: {i+1}/{len(unique_urls)} (成功={ok})")

        # 延迟避免反爬
        if delay > 0:
            await asyncio.sleep(delay)

    return results
