# Scraping CoinGecko (JS-rendered table)

## Technique

CoinGecko's frontpage loads cryptocurrency data dynamically via JavaScript. The table is a standard HTML `<table>` with `<tbody>` and `<tr>`/`<td>` elements, but is populated client-side. No API call is needed — Playwright renders the JS and we extract from the DOM.

## Script de référence

Script complet : `~/.hermes/scripts/coingecko_scrape.py`

```python
import asyncio, json, os
os.environ['LD_LIBRARY_PATH'] = os.path.expanduser('~/.local/usr/lib/x86_64-linux-gnu')
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
```

## Colonnes extraites (CoinGecko, 14 colonnes par ligne)

| Index | Contenu |
|-------|---------|
| 0 | (empty — sparkline/star) |
| 1 | Rank (1, 2, 3…) |
| 2 | Name + Ticker ("Bitcoin BTC") |
| 3 | "Buy" link or empty |
| 4 | Price |
| 5 | 1h % change |
| 6 | 24h % change |
| 7 | 7d % change |
| 8 | (unknown — volume change or metric) |
| 9 | 24h Volume |
| 10 | Market Cap |
| 11 | Fully Diluted Market Cap |
| 12 | Circulating/Max supply ratio |
| 13 | (empty) |

## Navigation strategy

- `wait_until="domcontentloaded"` — NOT `networkidle` (CoinGecko keeps websockets open, `networkidle` will timeout)
- `wait_for_timeout(5000)` — give JS 5s to render the table after DOM ready
- 45s timeout — CoinGecko can be slow to first render