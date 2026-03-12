#!/usr/bin/env python3.11
"""从浏览器配置中提取 storage state"""

import asyncio
from playwright.async_api import async_playwright
import json
import os

async def extract_storage_state():
    """使用现有的 browser profile 提取 storage state"""

    browser_profile = "/Users/jmok_studio/.notebooklm/browser_profile"
    storage_file = "/Users/jmok_studio/.notebooklm/storage_state.json"

    async with async_playwright() as p:
        # 使用现有的 browser profile 启动浏览器
        browser = await p.chromium.launch_persistent_context(
            browser_profile,
            headless=False,  # 先显示浏览器让用户确认登录状态
            args=['--disable-blink-features=AutomationControlled']
        )

        # 获取所有页面的 URL
        pages = browser.pages
        if pages:
            page = pages[0]
            print(f"当前页面: {page.url}")

            # 导航到 NotebookLM 检查登录状态
            await page.goto("https://notebooklm.google.com")
            await asyncio.sleep(3)

            print(f"导航后页面: {page.url}")

            # 检查是否已登录
            if "notebooklm.google.com" in page.url and "signin" not in page.url:
                print("✅ 检测到已登录状态！")

                # 提取 storage state
                storage_state = await browser.storage_state(path=storage_file)
                print(f"✅ Storage state 已保存到: {storage_file}")

                # 验证保存成功
                if os.path.exists(storage_file):
                    with open(storage_file, 'r') as f:
                        data = json.load(f)
                        cookies_count = len(data.get('cookies', []))
                        print(f"✅ 已保存 {cookies_count} 个 cookies")
                else:
                    print("❌ 保存失败")
            else:
                print("⚠️ 似乎未登录，请手动登录后再运行此脚本")
                await asyncio.sleep(10)  # 给用户时间手动登录
        else:
            print("❌ 没有打开的页面")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_storage_state())
