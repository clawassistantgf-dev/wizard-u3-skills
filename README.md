# 🧙 wizard-u3-skills

Skills Hermès personnelles de **wizard-u3** — agent Bitcoin Sorcier.

## Skills

| Skill | Description | Catégorie |
|-------|-------------|-----------|
| **tx-notify** | Watcher Bitcoin via mempool.space. Notifie Telegram et email à la confirmation d'une transaction | 🔗 Bitcoin |
| **quality-loop** | LLM-as-Judge. Boucle qualité : produit → juge → itère jusqu'à seuil (max 5 rounds) | 🤖 Agent |
| **playwright-web-scraping** | Scraping JS avec Chromium headless (Playwright). Fonctionne sans root | 🕸️ Web |
| **web-research** | Recherche web structurée avec Playwright + outils associés | 📚 Recherche |
| **bitcoin-wizard-persona** | Persona complet du Sorcier Bitcoin pour les sessions Hermès | 🎭 Personnalité |
| **llm-as-judge** | Documentation et protocole du pattern LLM-as-Judge avec tests | ⚖️ Dev |

## Installation

```bash
git clone git@github.com:clawassistantgf-dev/wizard-u3-skills.git ~/.hermes
```

## Scripts

- `scripts/tx-watch.sh` — Watchdog Bitcoin (bash + curl)
- `scripts/quality-loop.py` — Orchestrateur boucle qualité
- `scripts/sorcier_web.py` — Scraping Playwright
- `scripts/coingecko_scrape.py` — Scraper CoinGecko

---

*Maintenu par wizard-u3 ✨*