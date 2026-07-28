---
name: quality-loop
description: "Boucle qualité LLM-as-Judge : produit, juge, itère. Configurable par fichiers."
category: agent
triggers:
  - quality-loop --task <description> --criteria <type>
---

# quality-loop

## Usage

```bash
python3 ~/.hermes/scripts/quality-loop.py \
  --task "Ta tâche ici" \
  --criteria poetry|code|analysis
```

Le script :
1. Produit une réponse via Hermes
2. Envoie à un juge (LLM-as-Judge)
3. Si score ≥ threshold → agent confirme → FIN
4. Si score < threshold → round suivant avec feedback
5. Stop après max_rounds (défaut: 3)

## Config

Édite `~/.hermes/skills/quality-loop/config.yaml` :

```yaml
threshold: 8          # Note minimum pour passer
max_rounds: 5         # Nombre max d'itérations (défaut, modifiable en ligne)
inject_feedback: true # Injecter les retours du juge au round suivant ?
```

## Résultat

Le script produit :
- **stdout** : rapport complet markdown (livré par notify_on_complete dans le chat)
- **Rapport fichier** : `~/.hermes/quality-loop-report.md` (dernière exécution)
- **Logs bruts** : `~/.hermes/quality-loop-logs.jsonl` (JSONL append, historique complet)

## Critères

Ajoute des fichiers dans `~/.hermes/skills/quality-loop/criteria/*.txt` :
- `general.txt` — explications générales (clarté, justesse, complétude)
- `poetry.txt` — textes créatifs (qualité littéraire, pertinence, originalité)
- `code.txt` — code Python (correction mathématique, récursivité, exécutabilité, clarté)
- `analysis.txt` — analyses techniques (pertinence, précision, utilité, clarté)

Chaque fichier contient :
```
- Critère 1 : /4
- Critère 2 : /3
- ...

## Usage autonome par l'agent

Quand l'utilisateur demande une tâche avec contrôle qualité, l'agent exécute :

```bash
python3 ~/.hermes/scripts/quality-loop.py \
  --task "Description précise de la tâche" \
  --criteria general|poetry|code|analysis \
  [--max-rounds 5] \
  [--threshold 8]
```

### Rôle de l'agent

1. **Comprendre la tâche** — extraire la consigne exacte du message utilisateur
2. **Choisir les critères** — sélectionner le fichier `.txt` adapté :
   - `poetry` → textes créatifs, poèmes, récits
   - `code` → code Python, algorithmes, implémentations
   - `analysis` → revues de code, analyses techniques
   - `general` → explications, définitions, résumés
3. **Lancer le script** avec `terminal()` en background
4. **Récupérer le rapport** dans `~/.hermes/quality-loop-report.md`
5. **Présenter le résultat** à l'utilisateur avec la progression des scores

### Résultat attendu

Le script produit :
- Un rapport markdown dans `~/.hermes/quality-loop-report.md`
- Un log JSONL dans `~/.hermes/quality-loop-logs.jsonl`
- Le stdout avec le rapport complet (livré par notify_on_complete dans le chat)

### Exemple complet (agent)

```python
terminal(command="""
python3 ~/.hermes/scripts/quality-loop.py \\
  --task "Explique le concept de protocole selon Protocolized" \\
  --criteria general \\
  --max-rounds 5 \\
  --threshold 8
""", timeout=300, background=True, notify_on_complete=True)
```

Le résultat arrive directement dans le chat utilisateur.