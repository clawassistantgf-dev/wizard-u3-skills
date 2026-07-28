# X/Twitter Scraping — Techniques et état des lieux (2026)

## TL;DR

**X.com ne se laisse plus scraper sans login.** Toutes les approches directes échouent. La seule méthode fiable testée : **DuckDuckGo HTML search** qui indexe les tweets et expose leur texte dans les snippets de recherche.

---

## Approches testées

### 1. Playwright direct sur x.com ❌

```python
await page.goto('https://x.com/elonmusk', ...)
text = await page.inner_text('body')
```

**Résultat :** page de login wall. Aucune API interceptée (pas de calls GraphQL). Le contenu des tweets n'est pas chargé sans cookies de session.

**Status :** impossible sans session authentifiée.

### 2. Nitter instances ❌

Toutes les instances nitter.net testées (privacydev, lunar.icu, space, smnz.de) sont soit mortes (ERR_CONNECTION_REFUSED), soit bloquées par Cloudflare, soit timeout.

**Status :** Nitter est un projet mort/dormant. Les instances disparaissent une à une.

### 3. xcancel.com ❌

Anti-bot JS lourd (obfuscation, eval, challenges). Même Playwright avec `--disable-blink-features=AutomationControlled` et `add_init_script` pour cacher `navigator.webdriver` n'a pas passé le test.

**Status :** anti-bot trop agressif pour un headless standard.

### 4. Jina Reader (r.jina.ai) ❌

```
curl -s -H "Accept: text/plain" "https://r.jina.ai/https://x.com/elonmusk"
```

**Résultat :** `AbuseAlleviationError: Anonymous access to domain x.com blocked until ...`

**Status :** rate limité, Jina a blacklisté x.com pour cet utilisateur.

### 5. X GraphQL API avec guest token ❌

```bash
# Obtenir un guest token
GUEST_TOKEN=$(curl -s -X POST "https://api.x.com/1.1/guest/activate.json" \
  -H "Authorization: Bearer AAAAA..." -d '{}' | python3 -c "import sys,json; print(...)")

# Appel UserTweets
curl -s "https://api.x.com/graphql/QUERY_ID/UserTweets" \
  -H "X-Guest-Token: $GUEST_TOKEN" -d '{"variables":{...}}'
```

**Résultat :** le guest token s'obtient, mais le GraphQL endpoint `UserTweets` ne retourne plus les tweets (réponse vide). Les query hashes changent fréquemment et la sécurité `x-client-transaction` bloque les appels non-signés.

**Status :** X a verrouillé son API anonyme.

### 6. snscrape ❌

```python
import snscrape.modules.twitter as sntwitter
```

**Résultat :** `AttributeError: 'FileFinder' object has no attribute 'find_module'` — le module utilise `imp.find_module()` qui a été supprimé en Python 3.12+.

**Status :** cassé, nécessite Python ≤ 3.11.

### 7. twikit ❌

```python
from twikit import Client
client = Client('en-US')
user = await client.get_user_by_screen_name('elonmusk')
```

**Résultat :** `Exception: Couldn't get KEY_BYTE indices` — la sécurité X Client Transaction a changé et twikit n'a pas été mis à jour.

**Status :** dépassé par les changements de sécurité X.

### 8. DuckDuckGo HTML search ✅

**La seule approche qui a fonctionné.**

```bash
curl -sL "https://html.duckduckgo.com/html?q=site%3Ax.com+elonmusk" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

**Résultat :** les tweets indexés apparaissent dans les résultats de recherche avec leur texte, métriques (likes, retweets, replies), et date approximative.

**Exemple de snippet récupéré :**
```
"Grok 4.5, based on our 1.5T V9 foundation model, with Cursor data added
in supplemental training, is now in private beta at SpaceX & Tesla..."
```

**Limites :**
- CAPTCHA DuckDuckGo après ~3-5 requêtes
- Pas de données temps réel (délai d'indexation)
- Les tweets sans texte (images, vidéos) n'ont pas de snippet utile
- Métriques parfois partielles ou manquantes

---

## Recommandations

1. **Pour un tweet spécifique** : utiliser `fxtwitter.com/TWEET_ID` ou `vxtwitter.com/TWEET_ID` (rendu embed, pas de timeline)
2. **Pour une timeline** : DuckDuckGo HTML search (voir `scripts/duckduckgo_search.py` dans le skill `web-research`)
3. **Pour du scraping structuré** : utiliser une API tierce payante (SocialData, Brandwatch, etc.) — X ne permet plus l'accès gratuit
4. **Pour contourner les CAPTCHA DuckDuckGo** : alterner User-Agent, ajouter `sleep(2)` entre requêtes, ou utiliser un pool de proxies