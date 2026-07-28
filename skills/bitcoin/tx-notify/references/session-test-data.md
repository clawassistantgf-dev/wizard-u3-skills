# Tests et cas d'usage — tx-notify

## Txs testées dans la session du 28 Juillet 2026

| TXID | Statut | Block | Notes |
|------|--------|-------|-------|
| `228e2fd6118ed41810a87e97f3e8fa51015bd9c172564745d0024a38bdb8e0d2` | ✅ Confirmée | 960 006 | Fee ~257 sats, 1→1 |
| `a38664af06bb9d2e9136c7aa275b5e27048f06570d4f171b4e0eefbd6d8e7908` | ✅ Confirmée | 960 005 | Fee ~1387 sats, 6→5 (consolidation) |
| `39e56c1004af0ebfe38bb404924542a84d29b296edef5467254456cb70f6a641` | ⏳ Mempool | — | Fee 282 sats, 1→2 (paiement+change) |
| `aece08fd4112656845b04055548721af494d4557c532221e2e2ea5cf6cde2e3a` | ⏳ Mempool | — | Fee 142 sats, 1→2 |
| `0e9fcb4b9399d6cfb7800181dab556e156d8f4038d106d6f97e975eba3c6447a` | ✅ Confirmée | 960 007 | Fee 28 400 sats, 1→2. Watch déclenché avec --watch -i 10, notification livrée dans le chat Telegram. Cosmetic bug fixé : le JSON était passé par interpolation shell (cassait le parsing de block_height). Corrigé via tmpfile. |

## Commandes utilisées

```bash
# Vérification unique
bash ~/.hermes/scripts/tx-watch.sh <txid>

# Watch polling 10s en background (via Hermes)
terminal(
    command='bash ~/.hermes/scripts/tx-watch.sh --watch -i 10 -m 360 <TXID>',
    background=True,
    notify_on_complete=True,
    timeout=3600,
)

# CLI wrapper
~/.local/bin/txnotify --watch <txid>
```

## Dépendances manuelles

Le wrapper CLI `~/.local/bin/txnotify` est un script bash qui forwarde vers `tx-watch.sh`. S'assurer que `~/.local/bin` est dans le PATH.

## Notes API mempool.space

- `/api/tx/{txid}` → JSON avec `status.confirmed`, `status.block_height`, `value`, `fee`, `vin[]`, `vout[]`
- `/api/mempool/recent` → TX récentes de la mempool (pour tests)
- `/api/blocks/tip/height` → hauteur du dernier block
- Les champs `value` et `fee` sont en **satoshis** (diviser par 1e8 pour BTC)