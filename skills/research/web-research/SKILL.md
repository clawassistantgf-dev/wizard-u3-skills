---
name: web-research
description: >-
  Research topics on the web using terminal + curl when no web_search tool or
  browser is available. Covers scraping strategies, API-first approach, content
  extraction, and bypassing JS-heavy sites.
category: research
tags:
  - web-scraping
  - curl
  - research
  - search-engine
  - fallback
triggers:
  - user asks to "search", "look up", "research", "find", "google", "browse the web" for something
  - you need to fetch information from a known site
  - web_search or browser tools are unavailable
related_skills:
  - playwright-web-scraping
---

# Web Research via Terminal (No Browser / No web_search)

When `web_search` or browser tools are unavailable, use `terminal` + `curl` to research topics directly. The key insight: **skip search engines, query content sites directly.** DuckDuckGo, Google, and Bing heavily block programmatic scraping; content sites (Wikipedia, Know Your Meme, Medium, news outlets, APIs) are far more permissive.

## Workflow

### 1. Identify the right content site for the task

| Task | Target Site | Method |
|------|-------------|--------|
| Meme / internet culture | knowyourmeme.com | HTML scrape |
| General encyclopedic | en.wikipedia.org | API → JSON |
| News / current events | news site or RSS | HTML scrape |
| Academic papers | arxiv.org | API → JSON |
| Social media / X/Twitter | DuckDuckGo HTML search | HTML scrape (indexed tweets in snippets, mais CAPTCHA après 3-5 requêtes) |
| Social media / Reddit | reddit.com (old.reddit.com) | HTML scrape (requires auth/REST) |
| Long-form articles / newsletters | medium.com, **substack.com** | HTML scrape — **Substack fonctionne sans JS** (curl suffit) |
| Product / tech docs | official docs site | HTML scrape |
| Code / dev Q&A | stackoverflow.com | HTML scrape |
| Music / video info | site-specific public API | API call |

### 2. Try the API first (always preferred)

Many sites have public APIs that return clean JSON. This avoids HTML parsing entirely.

```bash
# Wikipedia API example
curl -s "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=YOUR_QUERY&format=json&srlimit=5"
```

### 3. Fall back to HTML scraping

Use a descriptive User-Agent (real browser string) and `-sL` for silent + follow redirects.

```python
# Pattern for extracting text from HTML
import sys, re, html
d = sys.stdin.read()
# Remove <script> and <style> blocks
text = re.sub(r'<script[^>]*>.*?</script>', '', d, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
# Strip all remaining tags
text = re.sub(r'<[^>]+>', '\n', text)
# Extract meaningful lines
lines = [html.unescape(l.strip()) for l in text.split('\n')
         if l.strip() and len(l.strip()) > 15]
# Deduplicate
seen = set()
for l in lines:
    if l not in seen:
        print(l[:300])
        seen.add(l)
```

### 4. Content extraction strategies by site

**Know Your Meme** — scrape the bodycopy section or use broad regex:
```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://knowyourmeme.com/memes/SLUG"
```
Look for: `class="bodycopy"`, `class="entry-page-section"`, `About</h2>`. The entry slug is usually the hyphenated meme name.

**Wikipedia** — use the API, then extract page text:
```bash
curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/Page_Title"
```

**Old Reddit** (more scrape-friendly than new Reddit):
```bash
curl -sL -H "User-Agent: YOUR_UNIQUE_DESCRIPTIVE_AGENT" "https://old.reddit.com/r/SUBREDDIT/comments/ID/"
```
⚠️ Reddit now blocks with "Your request has been blocked" for most anonymous scraping. Use the REST API with credentials when available.

**Substack** — **accessible sans JS** (curl suffit). Le contenu complet (articles, titres, auteurs, métriques) est rendu côté serveur :
```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://EXAMPLE.substack.com"
```
Pour les articles individuels, le texte intégral est dans le HTML. Utiliser le même pattern d'extraction que ci-dessus. Playwright peut aussi scroller la page d'accueil pour charger plus d'articles.

**Know Your Meme image URLs** — look for `i.kym-cdn.com` paths. The entry thumbnail is typically at:
`https://i.kym-cdn.com/entries/icons/facebook/XXXXX/magic.jpg` (where XXXXX is the entry ID).

## Pitfalls

1. **No web_search tool exists** — don't call it; it won't be there. Use terminal + curl.
2. **Search engines block scraping** — DuckDuckGo, Google, and Bing all serve minimal/no content to `curl` for general web search. **Exception:** DuckDuckGo HTML search (`html.duckduckgo.com/html?q=...`) **does** index X/Twitter posts and exposes their text in search result snippets. This is the only reliable way to get X/Twitter content without login. **⚠️ CAPTCHA risk:** DuckDuckGo bloque l'IP après ~3-5 requêtes HTML consécutives (CAPTCHA "Select all squares containing a duck"). Espacer les appels de 2s minimum et alterner User-Agent si possible. See pitfall #5 for the Playwright alternative for other JS-rendered sites.
3. **Reddit blocks anonymous scraping** — old.reddit.com used to work but now blocks most requests. If scraping fails, acknowledge the limitation and use what other sources are available.
4. **Medium requires JavaScript** — the article body won't load in curl alone. You'll only get the title, subtitle, and metadata. Acknowledge this to the user.
5. **JavaScript-rendered sites** — any site that loads content via JS (React, Vue, etc.) won't work with curl alone. **Use the `playwright-web-scraping` skill** for JS-rendered sites. Playwright + Chromium headless handles SPA, real-time data, and dynamic tables (CoinGecko, Twitter, etc.). Fallback: check for `window.__INITIAL_STATE__` or JSON-LD in the raw HTML. Do NOT tell the user JS scraping is impossible — just use Playwright.
   - **Full Chromium vs headless-shell:** Pour les sites avec anti-bot (Cloudflare, xcancel.com), utiliser le full Chromium (`~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`) avec `executable_path` — le headless-shell échoue là où le full Chromium passe. Ajouter aussi `args=['--disable-blink-features=AutomationControlled']` et `page.add_init_script()` pour cacher `navigator.webdriver`.
6. **Rate limiting** — some sites add rate limits on rapid scraping. Add `sleep(1)` between requests when querying multiple pages.
7. **Cloudflare / bot protection** — some sites use Cloudflare or similar. Nothing to do but find an alternative source.
8. **Always check exit codes** — an empty string response with exit 0 may mean the site silently redirected to a JS-required page. Pipe output to a length check before processing.

## Intellectual Synthesis — Transformer la recherche en document de référence

Une fois le contenu récupéré, une étape souvent nécessaire est la **synthèse intellectuelle** : extraire les concepts, le vocabulaire, les thèmes, et les organiser en un document portable.

### Workflow de synthèse

1. **Identifier le corpus** — lister les articles/pages lues avec URL, titre, date
2. **Extraire le langage** — relever les termes spécifiques, les définitions, les oppositions conceptuelles
3. **Distinguer ce qui est fait vs ce qui est nommé** — un projet peut avoir une contribution réelle dans la *nomination* sans avoir de livrable technique. C'est une contribution légitime à part entière
4. **Organiser en livres / sections** — par thème, pas par source
5. **Ajouter une couche Builder** — que retenir pour l'action ?

### Posture analytique

**Ne pas exiger d'output d'ingénierie des projets théoriques.** Nommer très bien, c'est déjà penser. La taxonomie précède l'ingénierie. Protocolized, par exemple, n'a pas construit de protocole concret — mais leur vocabulaire (Signal, Fausse Réponse, Tas Satellite, Aplatissement) est un prérequis pour qui veut en construire. **Utiliser leur travail comme lentille, pas comme forge.**

### Structure type d'une synthèse

```
# 📜 [Projet]
## LIVRE I — Le Langage (vocabulaire forgé)
## LIVRE II — Le Corps (ce qui a été réellement produit)
## LIVRE III — L'Atelier (leçons pour le Builder)
## LIVRE IV — La Carte (phases d'action)
```

### Référence

Le fichier `references/grimoire-protocolized.md` dans ce skill est un exemple concret de ce workflow : synthèse complète de Protocolized produite en scrapant leurs articles via Playwright, lisant le contenu intégral, extrayant le vocabulaire terme par terme, et distillant les thèmes en 10 lois actionnables. Utilisable comme template pour tout projet intellectuel à analyser.

## Verification

- Did you actually get meaningful text content, not just navigation/menu text?
- Are you missing the substantive content (JS-rendered)?
- Did you include the image URL if the user asked for visual content?
- For Bitcoin/Magic Internet Money wizard: the KYM entry is at `/memes/magic-internet-money-bitcoin-wizard`