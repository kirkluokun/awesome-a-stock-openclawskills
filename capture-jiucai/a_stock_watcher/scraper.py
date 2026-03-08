"""Playwright 爬虫基类 — 管理浏览器生命周期 + 登录态持久化 + 登录弹窗容错"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext

from .models import Article

logger = logging.getLogger("a_stock_watcher.scraper")

# 登录态存储路径
AUTH_DIR = Path(__file__).parent.parent / "data"
AUTH_STATE_PATH = AUTH_DIR / "auth_state.json"


class BaseScraper(ABC):
    """
    爬虫基类。子类只需实现 parse() 方法。
    
    登录态持久化：
        - 首次登录后，cookie/localStorage 保存到 data/auth_state.json
        - 后续运行自动加载，无需重复登录
        - 如果登录过期，运行 `uv run python -m a_stock_watcher.auth` 重新登录
    """

    # 子类覆盖
    source_name: str = ""
    source_url: str = ""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 是否无头模式。默认 True（无头），调试时设 False。
        """
        self.headless = headless

    async def run(self) -> list[Article]:
        """启动浏览器 → 加载登录态 → 导航到目标页面 → 解析 → 关闭浏览器"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                # 加载已保存的登录态
                context = await self._create_context(browser)
                page = await context.new_page()
                await page.goto(self.source_url, wait_until="networkidle", timeout=60000)
                await self.dismiss_login_modal(page)
                articles = await self.parse(page)
                return articles
            finally:
                await browser.close()

    async def _create_context(self, browser) -> BrowserContext:
        """创建带登录态的浏览器上下文"""
        if AUTH_STATE_PATH.exists():
            return await browser.new_context(storage_state=str(AUTH_STATE_PATH))
        return await browser.new_context()

    async def dismiss_login_modal(self, page: Page):
        """关闭登录弹窗（通用容错）

        韭菜公社页面偶尔弹出登录框，需要点击右上角叉号关闭。
        策略：先尝试点击关闭按钮，再用 JS 暴力删除弹窗 DOM。
        """
        try:
            # 1. 尝试点击关闭按钮（右上角叉号）
            close_selectors = [
                '.el-dialog__headerbtn',        # Element UI 弹窗关闭按钮
                '.el-icon-close',               # Element UI 关闭图标
                '.close-btn',                   # 通用关闭按钮
                'button[aria-label="Close"]',    # 无障碍标签
            ]
            for selector in close_selectors:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(500)
                    logger.info("  关闭登录弹窗（点击关闭按钮）")
                    return

            # 2. 回退：JS 删除弹窗 DOM
            removed = await page.evaluate("""() => {
                let removed = 0;
                document.querySelectorAll('.el-dialog__wrapper, .v-modal, .login-modal').forEach(el => {
                    el.remove();
                    removed++;
                });
                document.body.classList.remove('el-popup-parent--hidden');
                return removed;
            }""")
            if removed:
                logger.info(f"  关闭登录弹窗（JS删除 {removed} 个元素）")
        except Exception:
            pass  # 弹窗处理失败不影响主流程

    @abstractmethod
    async def parse(self, page: Page) -> list[Article]:
        """
        子类实现：从页面中提取文章数据。
        
        Args:
            page: 已导航到 source_url 的 Playwright Page 对象
            
        Returns:
            解析出的 Article 列表（含 title, content, images, url 等）
        """
        ...
