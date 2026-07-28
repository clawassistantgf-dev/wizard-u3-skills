#!/usr/bin/env python3
"""Scrape JS-rendu avec Playwright — Sorcier Bitcoin."""
import sys, json, os, asyncio
from playwright.async_api import async_playwright

DEFAULT_TIMEOUT = 15000

async def scrape(url: str, wait_selector: str = None, timeout: int = DEFAULT_TIMEOUT, headless: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="networkidle")
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            content = await page.content()
            title = await page.title()
            text = await page.inner_text("body")
            return {"title": title, "url": url, "text_len": len(text), "html_len": len(content)}
        except Exception as e:
            return {"error": str(e), "url": url}
        finally:
            await browser.close()

async def interactive_scrape(url: str, headless: bool = True):
    """Extraction structurée pour la recherche."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(url, timeout=DEFAULT_TIMEOUT, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        data = {
            "title": await page.title(),
            "url": url,
            "text": await page.inner_text("body"),
            "links": await page.eval_on_selector_all("a", "els => els.map(e => ({href: e.href, text: e.innerText})).slice(0,20)"),
        }
        await browser.close()
        return data

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    mode = sys.argv[2] if len(sys.argv) > 2 else "quick"

    if mode == "quick":
        result = asyncio.run(scrape(url))
    else:
        result = asyncio.run(interactive_scrape(url))

    print(json.dumps(result, indent=2, ensure_ascii=False))
