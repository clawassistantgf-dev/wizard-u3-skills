#!/usr/bin/env python3
"""Sorcier Web — Playwright-powered JS scraping et recherche web."""
import sys, json, os, asyncio
from playwright.async_api import async_playwright

# Chemin des libs système manuelles (installées sans root via apt-get download + dpkg-deb -x)
os.environ["LD_LIBRARY_PATH"] = f"{os.path.expanduser('~/.local/usr/lib/x86_64-linux-gnu')}:{os.environ.get('LD_LIBRARY_PATH','')}"

async def fetch(url, wait_until="networkidle", timeout=15000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=timeout, wait_until=wait_until)
        await page.wait_for_timeout(2000)

        data = {
            "title": await page.title(),
            "url": url,
            "text_len": 0,
            "content": None,
            "error": None,
        }
        try:
            text = await page.inner_text("body")
            data["text_len"] = len(text)
            data["content"] = text[:50000]
        except Exception as e:
            data["error"] = str(e)

        await browser.close()
        return data

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = asyncio.run(fetch(url))
    print(json.dumps(result, indent=2, ensure_ascii=False))