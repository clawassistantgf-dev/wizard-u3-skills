# While True — Théorie et pratique du watchdog

## Programmes qui nécessitent `while true`

| Programme | Pourquoi |
|-----------|----------|
| **OS Kernel** | Planificateur, interruptions |
| **Serveur HTTP** | `accept()` en boucle |
| **Event Loop** (Node.js, Reactor) | `epoll` / `kqueue` — attendre des événements |
| **Game Loop** | 60 FPS : input → update → render |
| **Daemon** (sshd, cron, syslog) | Toujours en vie |
| **Watchdog** (notre tx-notify) | Poll jusqu'à condition → re-poll |
| **REPL** (Python, bash) | Lire → exécuter → attendre |
| **Acteur Model** (Erlang) | `receive` → traiter → `receive` |

## Théories où `while true` n'explose pas

| Théorie | Concept | Pourquoi ça tient |
|---------|---------|-------------------|
| **π-calculus** | Processus réplicatifs `!P` | On raisonne sur les communications, pas sur la terminaison |
| **Coinduction / Bisimulation** | Comportements infinis | Deux systèmes qui bouclent sont équivalents s'ils font la même chose à chaque étape |
| **ω-automates (Büchi)** | Mots infinis | Un état acceptant doit être visité une infinité de fois |
| **FRP** | Behaviors | `time -> value` — pas de fin, l'horloge continue |
| **Acteur Model** | `receive` loop | L'acteur ne meurt pas — il traite des événements |
| **Liveness vs Safety** | Lamport, Dijkstra | Un programme infini est correct s'il est **live** (finit par arriver) et **safe** (n'atteint jamais un mauvais état) |
| **Stream fusion (lazy eval)** | Pipelines infinis | `map f (filter g (iterate succ 0))` — flux infinis transformés sans matérialisation |

## Notre tx-watch.sh comme Büchi automate

```
États : { NON_CONFIRMÉ, CONFIRMÉ }
Alphabet : { poll, confirm }
Transitions :
  NON_CONFIRMÉ --poll--> NON_CONFIRMÉ   (block_height = 0)
  NON_CONFIRMÉ --poll--> CONFIRMÉ       (block_height > 0)
  CONFIRMÉ --exit--> ∅
État acceptant : CONFIRMÉ
```

L'état `NON_CONFIRMÉ` est visité une infinité de fois. L'état `CONFIRMÉ` est l'état absorbant acceptant. Le système est **live** (finit par confirmer si la tx passe) et **safe** (aucun faux positif possible — le test est déterministe).

## Bonnes pratiques pour les boucles infinies

| Pratique | Dans tx-watch.sh |
|----------|-----------------|
| **Exit condition** | `break` quand `block_height > 0` — ✅ |
| **Rate limiting** | `sleep 10` entre chaque poll — ✅ |
| **Timeout configurable** | `MAX_POLLS=0` = infini, `-m N` pour limite — ✅ |
| **Graceful shutdown** | Pas de trap SIGTERM — acceptable (exit immédiat) |
| **Error handling** | `|| true` sur curl, protection contre API down — ✅ |
| **Idempotence** | `check_confirmation` est pur (même input → même output) — ✅ |
| **Pas de DOS** | 1 requête/10s max 8640/jour — ✅ |
| **Ressources** | curl ferme les connexions, pas de fuite mémoire — ✅ |

## Pourquoi l'Agent Loop Hermès est différent

L'Agent Loop utilise une condition de sortie **structurelle** et non **heuristique** :

```python
# VRAI code Hermès (conversation_loop.py:4264)
if assistant_message.tool_calls:
    execute_tools()
    continue   # ← prochain tour
else:
    final_response = assistant_message.content
    break       # ← SORTIE
```

La sortie est : "le LLM n'a pas généré de tool_calls". C'est une décision **basée sur le format de la réponse**, pas sur une évaluation sémantique ("est-ce que le LLM est satisfait ?"). Plus fiable que l'heuristique, mais toujours vulnérable à un LLM qui appellerait des outils à l'infini — d'où `max_iterations=90` comme garde-fou.

Garde-fous Hermès :
- `max_iterations` (défaut 90)
- `IterationBudget` avec `consume()`/`refund()`
- `_budget_grace_call` — un dernier appel de grâce
- Invalid tool retries (3 max)
- Invalid JSON retries (3 max)
- Compression automatique à 50% de la fenêtre de contexte