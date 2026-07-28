#!/usr/bin/env python3
"""CoinGecko scraper — JS-rendu, no API."""
import asyncio, json, os
os.environ['LD_LIBRARY_PATH'] = os.path.expanduser('~/.local/usr/lib/x86_64-linux-gnu') + ':' + os.environ.get('LD_LIBRARY_PATH', '')
from playwright.async_api import async_playwright

JS_CODE = """
() => {
    const rows = [...document.querySelectorAll('table tbody tr')].slice(0, 10);
    return rows.map(row => {
        const cells = [...row.querySelectorAll('td')];
        return cells.map(td => td.innerText.trim().replace(/\\s+/g, ' '));
    });
}
"""

async def go():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://coingecko.com', timeout=45000, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)
        
        rows = await page.evaluate(JS_CODE)
        
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        await browser.close()

asyncio.run(go())