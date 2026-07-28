---
name: playwright-web-scraping
description: "Scraper JS-rendu avec Playwright + Chromium headless (sans root)."
category: research
tags:
  - web-scraping
  - javascript
  - playwright
  - chromium
  - js-rendering
  - no-root
triggers:
  - user needs data from a JS-heavy or SPA site (React, Vue, Angular)
  - curl scraping returns only nav/menus, not actual content
  - CoinGecko, Twitter/X, or similar dynamic table site needs scraping
  - site hides content behind JavaScript loading
related_skills:
  - web-research
  - artifact-verification
---

# Playwright Web Scraping (JS-rendu)

## Installation (sans root)

```bash
pip3 install --break-system-packages playwright
python3 -m playwright install chromium
```

## Dépendances système manquantes (sans root)

Si Chromium lance une `TargetClosedError` avec `libnspr4.so not found` :

```bash
apt-get download libnspr4 libnss3
dpkg-deb -x libnspr4*.deb ~/.local/
dpkg-deb -x libnss3*.deb ~/.local/
export LD_LIBRARY_PATH="$HOME/.local/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
```

**Important :** La variable `LD_LIBRARY_PATH` doit être exportée **avant** d'importer `playwright` dans le script Python. Ne pas l'oublier entre deux sessions.

## Scripts disponibles

- `~/.hermes/scripts/scrape.py` — version quick/interactive
- `~/.hermes/scripts/sorcier_web.py` — version épurée avec LD_LIBRARY_PATH auto
- `~/.hermes/scripts/coingecko_scrape.py` — scraper tableau dynamique (référence)

## Patterns de scraping

### Pattern 1 : Extraction texte générale

Utilise `wait_until="domcontentloaded"` (pas `networkidle` qui peut timeout sur les sites lourds) + un `wait_for_timeout` de 3-5s pour laisser le JS finir son rendu :

```python
await page.goto(url, timeout=45000, wait_until="domcontentloaded")
await page.wait_for_timeout(5000)
text = await page.inner_text("body")
```

### Pattern 2 : Scraping de tableaux dynamiques (CoinGecko, etc.)

Utilise `page.evaluate()` avec du JavaScript pur pour extraire les cellules du DOM ligne par ligne. Cela évite les problèmes de sélecteurs CSS fragiles :

```python
rows = await page.evaluate("""
() => {
    const rows = [...document.querySelectorAll('table tbody tr')].slice(0, 10);
    return rows.map(row => {
        const cells = [...row.querySelectorAll('td')];
        return cells.map(td => td.innerText.trim().replace(/\\s+/g, ' '));
    });
}
""")
```

Les colonnes typiques d'un tableau crypto (CoinGecko) sont indexées :

| Index | Data |
|-------|------|
| 1 | Rank |
| 2 | Name + Ticker |
| 3 | "Buy" link or empty |
| 4 | Price |
| 5 | 1h % |
| 6 | 24h % |
| 7 | 7d % |
| 8 | Volume change or supply ratio |
| 9 | 24h Volume |
| 10 | Market Cap |
| 11 | Fully Diluted MC |

### Pattern 3 : Extraction de liens

```python
links = await page.eval_on_selector_all("a[href]", "els => els.map(e => ({href: e.href, text: e.innerText})).slice(0,50)")
```

### Pattern 4 : Automatisation de formulaire / login (X.com example)

X.com exige une session authentifiée pour voir la timeline. Le flow de login automatisé :

```python
# 1. Naviguer vers login
await page.goto('https://x.com/i/flow/login', timeout=30000, wait_until='domcontentloaded')

# 2. Accepter cookies
await page.query_selector('button:has-text("Accept all cookies")').click()

# 3. Cliquer "Email or username" (c'est un span cliquable, pas un input)
await page.query_selector('span:has-text("Email or username")').click()

# 4. Remplir le champ username qui apparaît
await page.fill('input[autocomplete="username"]', 'username')

# 5. Cliquer Next
await page.query_selector('button:has-text("Next")').click()

# 6. Vérifier si X demande password ou téléphone
#    - "Enter your password" → champ password visible → login normal
#    - "Enter your phone number" → X demande SMS → pas de login possible sans téléphone
```

**Pitfall :** Si X demande un numéro de téléphone après le username, le compte est lié à un SMS (pas de password-only login).

## Sites accessibles sans login

| Site | Statut | Méthode |
|------|--------|---------|
| **CoinGecko** | ✅ Données complètes | `page.evaluate()` sur le tableau |
| **Substack** | ✅ Contenu intégral | `page.inner_text("body")` simple |
| **Wikipedia** | ✅ API REST | API directe (pas besoin de Playwright) |
| **X.com** | ❌ Login wall | DuckDuckGo HTML search (fallback) |

## Pattern clé : Détection d'API REST derrière les SPAs

Avant d'essayer de scraper le HTML d'un site SPA (Angular, React, Vue), **toujours vérifier si le site expose une API REST JSON**. C'est plus rapide, plus fiable, et évite le parsing HTML.

### Méthode : Inspecter les requêtes réseau

Depuis Playwright, lire les appels réseau faits par la page :

```python
reqs = await page.evaluate('() => performance.getEntriesByType("resource").map(r => r.name)')
api_endpoints = [r for r in reqs if '/api/' in r.lower()]
```

Exemple avec **bilans-ges.ademe.fr** (Angular) qui a révélé :

```
/api/inventories?page=1&itemsPerPage=10     → Liste des bilans GES
/api/activity_sectors                        → 16 secteurs d'activité
/api/structure_types                         → 5 types de structure
/api/people_number_groups                    → 14 tranches effectif
/api/regions                                 → 25 régions
/api/exports/public-inventories/latest       → Export CSV complet (55 Mo)
/api/medias/{uuid}/download                  → Téléchargement de fichiers
```

**Résultat :** pas besoin de Playwright ni de scraping HTML — 5 appels `curl` suffisent pour télécharger toutes les données de la plateforme.

### Workflow de détection

1. Ouvrir la page SPA avec Playwright (full Chromium)
2. Attendre le chargement + 3s
3. Lire `performance.getEntriesByType("resource")`
4. Filtrer les URLs contenant `/api/`, `/graphql`, `/v1/`, `/rest/`
5. Tester chaque endpoint avec `curl -s -H "Accept: application/json"`
6. Si la réponse est du JSON valide → scraper via API, pas via HTML

### Quand utiliser cette approche

- Sites gouvernementaux, institutionnels, tableaux de bord publics
- SPAs Angular, React, Vue avec données dynamiques
- Plateformes de publication de données (Bilans GES, data.gouv.fr, etc.)
- **Toujours en première intention** avant le scraping HTML

## Gestion des timeouts

- Sites simples (example.com) : 15s suffisent
- Sites lourds (CoinGecko, Twitter) : 45s avec `domcontentloaded`
- Si `networkidle` timeout : passer à `domcontentloaded` + `wait_for_timeout`
- Toujours wrapper dans un try/except pour capturer les TimeoutError

## Best practices

1. **Jamais `networkidle` sur un site de données temps réel** — les websockets maintiennent le réseau actif, timeout garanti.
2. **LD_LIBRARY_PATH doit être dans l'environnement** avant l'import de playwright. Soit dans le script (`os.environ["LD_LIBRARY_PATH"] = ...`), soit exporté avant.
3. **Utiliser le VRAI Chromium (pas headless-shell) pour les sites difficiles** — le full Chromium (`~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`) gère mieux les cookies et la détection de bot. Le headless-shell échoue là où le full Chromium passe. Y accéder via `executable_path` :
   ```python
   browser = await p.chromium.launch(
       headless=True,
       executable_path='/home/hermes/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
   )
   ```
   Pour améliorer la furtivité anti-bot :
   ```python
   browser = await p.chromium.launch(
       headless=True,
       executable_path='.../chrome',
       args=['--disable-blink-features=AutomationControlled']
   )
   await page.add_init_script('''Object.defineProperty(navigator, 'webdriver', { get: () => undefined });''')
   ```
4. **Pour les tableaux, `page.evaluate()` > sélecteurs CSS** — plus résilient face aux changements de classes.
5. **Interaction avec les formulaires** — Playwright peut cliquer, remplir, scroller, et soumettre. Utiliser `page.query_selector()` + `.click()` / `.fill()` + attente de transition. Pour les pages avec cookie wall : cliquer le bouton "Accept all cookies" en premier.

## X/Twitter scraping (état des lieux 2026)

Scraper X.com directement est devenu **extrêmement difficile** sans login. Approches testées :

| Approche | Statut | Raison |
|----------|--------|--------|
| Playwright direct sur x.com | ❌ Login wall — plus de timeline guest |
| Nitter (toutes instances) | ❌ Morts ou Cloudflare |
| xcancel.com | ❌ Anti-bot JS détecte headless |
| r.jina.ai sur x.com | ❌ Rate limité |
| X GraphQL API (guest token) | ❌ Guest tokens restreints |
| snscrape + twikit | ❌ Cassé sur Python 3.13 / X a changé sa sécurité |
| **DuckDuckGo HTML search** | ✅ **Indexe les posts, texte dans les snippets** |

### La parade : DuckDuckGo HTML search pour X

DuckDuckGo indexe les tweets et expose leur texte dans les snippets de recherche HTML :

```bash
curl -sL "https://html.duckduckgo.com/html?q=site%3Ax.com+USERNAME" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

**Pattern d'extraction :**
```python
content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
results = re.findall(r'class="result__a"[^>]*>(.*?)</a>', content, re.DOTALL)
snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', content, re.DOTALL)
```

**Limites DuckDuckGo :** CAPTCHA après ~3-5 requêtes (bloque l'IP pour ~30 min), pas temps réel, tweets sans texte invisibles. Ne pas enchaîner les recherches DuckDuckGo sans `sleep(2)` entre les appels.

Voir :
- `references/x-twitter-scraping.md` — protocole de test complet X (7 approches échouées, 1 validée)
- `references/substack-scraping.md` — Substack (accessible sans JS, contenu intégral)
- `references/api-detection-ademe.md` — détection d'API REST derrière les SPAs (exemple ADEME Bilans GES)
- `references/coingecko-table-scrape.md` — scraping de tableaux dynamiques

## Limitations

- Pas de login / session (sans contexte utilisateur stocké)
- Les pages avec captcha strict ou Cloudflare niveau 5+ blockeront
- Timeout conseillé : 45s pour les sites lourds (60s pour X.com)
- Consommation mémoire : ~150-200 Mo par instance Chromium
- X/Twitter inaccessible directement — utiliser DuckDuckGo HTML comme fallback
- **DuckDuckGo HTML search :** CAPTCHA après 3-5 requêtes consécutives — espacer les appels de 2s minimum
- **X.com login :** même avec credentials, X peut exiger un numéro de téléphone (SMS) au lieu d'un password pour certains comptes