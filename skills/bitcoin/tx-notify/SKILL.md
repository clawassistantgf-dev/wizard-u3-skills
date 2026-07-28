---
name: tx-notify
description: "Surveille une transaction Bitcoin et notifie quand elle est confirmée. Déclenché par 'watch <txid>', 'surveille <txid>', ou 'tx-notify <txid>'."
category: bitcoin
tags:
  - bitcoin
  - mempool
  - transaction
  - watchtower
  - notification
  - email
  - infinity-loop
triggers:
  - watch <txid>
  - surveille <txid>
  - tx-notify <txid>
---

# tx-notify — Bitcoin Transaction Watcher

## Description

Surveille une transaction Bitcoin via **mempool.space** (ou toute instance mempool compatible) et notifie sur Telegram dès confirmation.

Deux modes :

| Mode | Usage | Quand |
|------|-------|-------|
| **Watchdog** (cron) | Check unique par tick | Notification silencieuse, pas de process permanent |
| **Auto-poll** (`--watch`) | Boucle interne avec interval configurable | Polling rapide (10s, 30s) |

## Architecture

```
/tx-notify <txid>  →  Script bash → mempool.space /api/tx/{txid}
                              ↓
                    ┌──── non confirmé (silence)
                    │
                    └──── confirmé → message formaté → origin
                                      + arrêt auto
```

## Script

`~/.hermes/scripts/tx-watch.sh` — bash modulaire, 200+ lignes. Supporte `--watch`, `--interval`, `--max`, et envoi email via SMTP OVH.

### Modes

| Mode | Commande | Usage |
|------|----------|-------|
| Check unique | `tx-watch.sh <txid>` | Vérifie et affiche si confirmé |
| Watch infini | `tx-watch.sh --watch -i 10 <txid>` | Poll toutes les 10s sans timeout |
| Watch limité | `tx-watch.sh --watch -i 10 -m 360 <txid>` | Stop après 360 polls |

### Livraison

- **Telegram** : `terminal(background=True, notify_on_complete=True)` → stdout livré dans le chat
- **Email** : pas via notify_on_complete (réservé Telegram). Le script envoie directement via `send_email()` (SMTP OVH, credentials dans `.env`). Appelé AVANT le stdout.

```bash
# Vérification unique (watchdog pour cron)
bash ~/.hermes/scripts/tx-watch.sh <txid>

# Auto-poll toutes les 10s jusqu'à confirmation (infini par défaut)
bash ~/.hermes/scripts/tx-watch.sh --watch <txid>

# Auto-poll toutes les 30s avec max 50 tentatives (~25 min)
bash ~/.hermes/scripts/tx-watch.sh --watch -i 30 -m 50 <txid>

# Instance mempool custom
MEMPOOL_URL=http://localhost:3000 bash ~/.hermes/scripts/tx-watch.sh <txid>
```

### Modes de livraison

| Canal | Mécanisme | Quand |
|-------|-----------|-------|
| **Telegram** | `notify_on_complete=True` sur `terminal()` | Automatique par Hermes |
| **Email** | `send_email()` dans le script (SMTP OVH) | Automatique à la confirmation |
| **Les deux** | `notify_on_complete=True` + SMTP inline | Les deux canaux simultanément |

Configuration email (credentials dans `.env`) :
```
EMAIL_ADDRESS=wizard-u3@hxmt.xyz
EMAIL_SMTP_HOST=smtp.mail.ovh.net
EMAIL_SMTP_PORT=587
EMAIL_HOME_ADDRESS=galoisfield2718@gmail.com
```

Le script utilise `smtplib` de Python — pas de dépendance Himalaya nécessaire. La fonction `send_email()` envoie directement au moment de la confirmation, indépendamment du mécanisme Hermes.

### Messages de notification

```
═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══ ═══

✅ TX CONFIRMÉE

📍 TXID : 228e2fd6118ed418...bdb8e0d2
📦 Block : 960 006
💰 Value : 0.00123456 BTC
⛽ Fee   : 0.00000257 BTC
🔗 I/O   : 1 → 1

🔗 https://mempool.space/tx/<txid>
```

Pour les coinbase : `⛏️  COINBASE — Block N`.

### Watchdog pattern (théorie)

Le script suit le pattern **Büchi watchdog** : boucle infinie (`while true`) qui ne produit de output que quand la condition est remplie — sinon silence.

```text
while true:
    block_height = check_confirmation(txid)
    if block_height > 0:
        send_email()
        echo notification()
        break
    sleep(interval)
```

Caractéristiques :
- **Silencieux en état stable** — pas de heartbeat, pas de spam
- **Auto-stoppant** — exit immédiat après confirmation
- **Idempotent** — redémarrer ne duplique pas la notif
- **Timeout configurable** : `-m N` pour une limite, `MAX_POLLS=0` = infini (défaut)

## Architecture modulaire

Le script a une section explicite `# === FUTURE FEATURES : ajouter ici ===` avec des exemples prêts :

```bash
# check_price_move(threshold_pct) { ... }
# check_address_txs(address) { ... }
# check_mempool_fees() { ... }
```

Écrire une fonction, l'appeler dans `main()`, et le mécanisme de livraison est identique.

## Création du cron job (mode watchdog)

```python
cronjob(
    action='create',
    name='tx-watch-<8-premiers-car-hex>',
    schedule='every 1m',
    script='~/.hermes/scripts/tx-watch.sh <TXID>',
    no_agent=True,
    deliver='origin',
)
```

## Création du watch en polling rapide (mode --watch)

```python
terminal(
    command='bash ~/.hermes/scripts/tx-watch.sh --watch -i 10 <TXID>',
    background=True,
    notify_on_complete=True,
)
```

## API mempool.space utilisée

- `GET /api/tx/{txid}` — infos de la transaction
- Rate limit : safe à 1 req/10s — les valeurs par défaut (10s-60s) sont conservatrices

## Variables d'environnement

- `MEMPOOL_URL` — URL du mempool (défaut: https://mempool.space, compatible toute instance open-source)

## Dépendances

- `curl` — appels API
- `python3` — parsing JSON + formatage

## Pitfalls

- **Interpolation shell dans format_notification** : ne PAS passer le JSON brut via `${tx_json}` dans une heredoc python3. Les caractères spéciaux (guillemets, sauts de ligne) cassent le parsing de `block_height`. **Fix confirmé** : écrire dans un tmpfile avec `mktemp` et lire depuis Python avec `open()`. Voir la fonction `format_notification()` dans le script.
- **Block height à 0 dans la notification** : symptôme direct du bug ci-dessus. Si une notification arrive avec `📦 Block: 0` mais que la tx est confirmée, le parsing JSON a échoué. Vérifier avec `curl` direct sur mempool.space.
- **`notify_on_complete`** : mécanisme intégré à Hermes, pas du code de l'agent. Le script n'a pas besoin de gérer la livraison Telegram.
- **Infinity timeout par défaut** : `MAX_POLLS=0` depuis la session. Si un timeout est souhaité, passer `--max N` ou `-m N`. Ne PAS utiliser `MAX_POLLS=N` avec une valeur finie comme dérivée de la première version (360 × 10s = 1h). Le bon défaut est **0 = infini**.
- **Dual delivery (email + Telegram)** : les deux canaux peuvent coexister. `notify_on_complete=True` livre sur Telegram automatiquement. L'appel `send_email()` dans le script envoie l'email indépendamment. Pas besoin de choisir l'un ou l'autre.