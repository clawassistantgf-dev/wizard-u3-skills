# Substack Scraping Reference

## Accessibilité
- ✅ **Accessible sans JS** (curl suffit pour le HTML)
- ✅ **Contenu intégral** rendu côté serveur — pas de rendu client nécessaire
- ✅ **Articles, dates, auteurs, métriques** (likes, comments) tous dans le HTML
- ✅ **Aucun captcha, aucune limite de rate** constatée

## Avec curl (suffisant pour le texte)

```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://EXAMPLE.substack.com"
```

## Avec Playwright (pour scroller + charger plus d'articles)

```python
await page.goto(url, timeout=20000, wait_until="domcontentloaded")
await page.wait_for_timeout(3000)

# Scroller pour charger plus d'articles
await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
await page.wait_for_timeout(2000)

# Récupérer tous les articles
articles = await page.evaluate("""
() => {
    const posts = [...document.querySelectorAll('a[href*="/p/"]')];
    return [...new Set(posts.map(a => a.href))].slice(0,20);
}
""")
```

## Extraction des articles

```python
# Extraire les liens vers les articles
links = await page.evaluate("""
() => {
    const allLinks = [...document.querySelectorAll('a[href*="/p/"]')];
    return [...new Set(allLinks.map(a => a.href))];
}
""")
```

## Pour lire un article complet

```python
await page.goto(url, timeout=20000, wait_until="domcontentloaded")
await page.wait_for_timeout(3000)
title = await page.title()
text = await page.inner_text("body")
lines = [l.strip() for l in text.split("\\n") if l.strip() and len(l.strip()) > 15]
```

## Pattern de filtre des lignes

Les lignes à ignorer au début : "Subscribe", "Sign in", "By subscribing, you agree..."
Le vrai contenu commence après la première occurrence d'une ligne de >80 caractères qui n'est pas dans les mots-clés ci-dessus.

## Exemple : Protocolized

URL: https://protocolized.summerofprotocols.com/
Articles récents (Juin 2026) :
- A Visitor's Guide to the Disposition (fiction longue, 30 juin)
- Durable AI Adoption (guide pratique, 25 juin)
- The Character of Public Transit Systems (analyse, 22 juin)
- Jamverse Jam (appel à contributions, 16 juin)
- The Big Man (fiction, 12 juin)

Tous accessibles avec le même pattern.