"""登录工具 — 自动登录韭菜公社，保存登录态

用法（自动登录）：
    cd /path/to/capture-韭菜公社 && source .env && uv run python -m a_stock_watcher.auth

会打开浏览器 → 自动输入手机号和密码 → 登录 → 保存 cookie 到 data/auth_state.json。
后续所有爬虫运行会自动加载此文件，无需重复登录。

如需手动登录（自动登录失败时）：
    uv run python -m a_stock_watcher.auth --manual
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logger = logging.getLogger("a_stock_watcher.auth")

AUTH_DIR = Path(__file__).parent.parent / "data"
AUTH_STATE_PATH = AUTH_DIR / "auth_state.json"


def _load_credentials() -> tuple[str, str]:
    """三级加载凭据：环境变量 > skill目录.env > 上级目录.env，全部缺失则报错退出"""
    phone = os.environ.get("JIUCAI_PHONE") or os.environ.get("JIUCAI_ACCOUNT")
    password = os.environ.get("JIUCAI_PASSWORD")
    if phone and password:
        return phone, password

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
            if k in ("JIUCAI_PHONE", "JIUCAI_ACCOUNT"):
                phone = v
            elif k == "JIUCAI_PASSWORD":
                password = v
        if phone and password:
            return phone, password

    print("❌ 未找到 JIUCAI_PHONE / JIUCAI_PASSWORD，请设置环境变量或创建 .env 文件", file=sys.stderr)
    sys.exit(1)


# 账号信息：优先环境变量，其次 .env 文件
PHONE, PASSWORD = _load_credentials()


async def auto_login():
    """自动登录：打开浏览器 → 输入账号密码 → 保存登录态"""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔄 正在打开韭菜公社...")
        await page.goto("https://www.jiuyangongshe.com", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # 触发登录弹窗 — 点击需要登录的功能
        print("🔄 触发登录弹窗...")
        try:
            await page.click('text=交易计划', timeout=5000)
        except Exception:
            # 备选方案：直接跳转到需要登录的页面
            await page.goto("https://www.jiuyangongshe.com/tradingPlan", timeout=30000)
        await page.wait_for_timeout(3000)

        # 切换到"账号密码登录"
        pwd_tab = await page.query_selector('text=账号密码登录')
        if pwd_tab:
            await pwd_tab.click()
            await page.wait_for_timeout(1000)
            print("✅ 已切换到账号密码登录")
        else:
            print("⚠️  未找到'账号密码登录'，尝试继续...")

        # 查找并填写手机号
        phone_filled = False
        phone_selectors = [
            'input[placeholder*="手机"]',
            'input[placeholder*="账号"]',
            'input[type="tel"]',
        ]
        for sel in phone_selectors:
            phone_input = await page.query_selector(sel)
            if phone_input:
                await phone_input.click()
                await phone_input.fill("")
                await phone_input.fill(PHONE)
                phone_filled = True
                print(f"✅ 已输入手机号: {PHONE[:3]}****{PHONE[-4:]}")
                break

        if not phone_filled:
            # 回退：查找弹窗内所有非密码输入框
            inputs = await page.query_selector_all('.el-dialog input:not([type="password"]):not([type="hidden"])')
            if inputs:
                await inputs[0].click()
                await inputs[0].fill("")
                await inputs[0].fill(PHONE)
                phone_filled = True
                print(f"✅ 已输入手机号（回退选择器）")

        if not phone_filled:
            print("❌ 未找到手机号输入框！请使用 --manual 手动登录")
            await browser.close()
            return False

        # 查找并填写密码
        pwd_input = await page.query_selector('input[type="password"]')
        if pwd_input:
            await pwd_input.click()
            await pwd_input.fill("")
            await pwd_input.fill(PASSWORD)
            print("✅ 已输入密码")
        else:
            print("❌ 未找到密码输入框！请使用 --manual 手动登录")
            await browser.close()
            return False

        # 点击登录按钮
        login_clicked = False
        login_selectors = [
            '.el-dialog button:has-text("登录")',
            'button:has-text("登录")',
            '.login-btn',
        ]
        for sel in login_selectors:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                login_clicked = True
                print("✅ 已点击登录")
                break

        if not login_clicked:
            # 回退：按回车
            await pwd_input.press("Enter")
            print("✅ 已按回车提交登录")

        # 等待登录完成
        await page.wait_for_timeout(5000)

        # 验证登录状态
        cookies = await context.cookies()
        cookie_names = [c['name'] for c in cookies]
        has_auth = any('token' in n.lower() or 'session' in n.lower()
                       or 'user' in n.lower() or 'auth' in n.lower()
                       for n in cookie_names)

        if has_auth or len(cookies) > 5:
            # 保存登录态
            await context.storage_state(path=str(AUTH_STATE_PATH))
            print(f"\n🎉 登录成功！登录态已保存到 {AUTH_STATE_PATH}")
            print(f"   Cookies 数量: {len(cookies)}")
            await browser.close()
            return True
        else:
            print(f"\n⚠️  登录可能未成功（Cookies: {len(cookies)}）")
            print("请检查浏览器窗口，手动完成登录后按回车保存...")
            input("\n按回车保存登录态...")
            await context.storage_state(path=str(AUTH_STATE_PATH))
            print(f"✅ 登录态已保存到 {AUTH_STATE_PATH}")
            await browser.close()
            return True


async def manual_login():
    """手动登录：打开浏览器，等待用户手动操作"""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.jiuyangongshe.com", wait_until="networkidle")
        print("\n" + "=" * 50)
        print("浏览器已打开，请手动完成登录。")
        print("登录成功后，回到这里按 回车 保存登录态。")
        print("=" * 50)

        input("\n按回车保存登录态...")

        await context.storage_state(path=str(AUTH_STATE_PATH))
        print(f"\n✅ 登录态已保存到 {AUTH_STATE_PATH}")
        await browser.close()


if __name__ == "__main__":
    if "--manual" in sys.argv:
        asyncio.run(manual_login())
    else:
        asyncio.run(auto_login())
