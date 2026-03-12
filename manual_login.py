#!/usr/bin/env python3.11
"""
手动 NotebookLM 认证脚本
解决原 login 命令在非交互式环境中无法使用的问题
"""

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# NotebookLM URLs
NOTEBOOKLM_URL = "https://notebooklm.google.com/"
GOOGLE_ACCOUNTS_URL = "https://accounts.google.com/"

# 配置路径
HOME_DIR = Path.home()
NOTEBOOKLM_DIR = HOME_DIR / ".notebooklm"
STORAGE_PATH = NOTEBOOKLM_DIR / "storage_state.json"
BROWSER_PROFILE = NOTEBOOKLM_DIR / "browser_profile"


async def manual_login():
    """启动浏览器并指导用户完成认证"""

    print("=" * 60)
    print("NotebookLM 手动认证")
    print("=" * 60)
    print()

    # 确保目录存在
    NOTEBOOKLM_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True, mode=0o700)

    print("正在启动浏览器...")
    print("请在浏览器中完成以下步骤：")
    print()
    print("1. 登录你的 Google 账号")
    print("2. 等待跳转到 NotebookLM 主页")
    print("3. 回到这里，按 Ctrl+C 结束浏览器")
    print("4. 认证信息将自动保存")
    print()

    async with async_playwright() as p:
        # 启动持久化浏览器
        browser = await p.chromium.launch_persistent_context(
            str(BROWSER_PROFILE),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--password-store=basic",
            ],
            ignore_default_args=["--enable-automation"],
        )

        # 打开 NotebookLM
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto(NOTEBOOKLM_URL)

        print(f"浏览器已打开，当前页面: {page.url}")
        print()

        try:
            # 等待用户完成登录
            while True:
                await asyncio.sleep(1)
                current_url = page.url

                # 检查是否已登录到 NotebookLM
                if "notebooklm.google.com" in current_url and "signin" not in current_url:
                    print(f"✅ 检测到 NotebookLM 页面: {current_url}")

                    # 访问 Google Accounts 确保获取 .google.com cookies
                    await page.goto(GOOGLE_ACCOUNTS_URL, wait_until="load")
                    await asyncio.sleep(2)

                    # 回到 NotebookLM
                    await page.goto(NOTEBOOKLM_URL, wait_until="load")
                    await asyncio.sleep(2)

                    # 保存认证状态
                    await browser.storage_state(path=str(STORAGE_PATH))
                    STORAGE_PATH.chmod(0o600)

                    print()
                    print("=" * 60)
                    print("✅ 认证信息已保存!")
                    print(f"保存位置: {STORAGE_PATH}")
                    print("=" * 60)
                    print()
                    print("现在可以运行: notebooklm list")
                    break

        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C，正在保存认证状态...")

            # 访问 Google Accounts 确保获取 .google.com cookies
            try:
                await page.goto(GOOGLE_ACCOUNTS_URL, wait_until="load")
                await asyncio.sleep(2)
                await page.goto(NOTEBOOKLM_URL, wait_until="load")
                await asyncio.sleep(2)
            except Exception:
                pass

            # 保存认证状态
            await browser.storage_state(path=str(STORAGE_PATH))
            STORAGE_PATH.chmod(0o600)

            print(f"✅ 认证信息已保存到: {STORAGE_PATH}")

        finally:
            await browser.close()

    # 验证保存的认证
    print()
    print("验证认证信息...")
    if STORAGE_PATH.exists():
        try:
            with open(STORAGE_PATH, 'r') as f:
                data = json.load(f)
                cookies = data.get('cookies', [])
                google_cookies = [c for c in cookies if 'google' in c.get('domain', '')]
                sid_cookies = [c for c in cookies if c.get('name') == 'SID']

                print(f"- 总 cookies: {len(cookies)}")
                print(f"- Google cookies: {len(google_cookies)}")
                print(f"- SID cookie: {'✅ 已找到' if sid_cookies else '❌ 未找到'}")

                if sid_cookies:
                    print()
                    print("🎉 认证成功! 现在可以运行: notebooklm list")
                    return True
                else:
                    print()
                    print("⚠️ 可能未正确登录，请重试")
                    return False
        except Exception as e:
            print(f"验证失败: {e}")
            return False
    else:
        print("❌ 认证文件未找到")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(manual_login())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
