---
name: llm-as-judge
description: "Quality loop with subagent judges: produce output → judge scores it → iterate if below threshold. Class-level pattern for code review, writing, analysis, any generative task with criteria."
category: software-development
tags:
  - quality
  - evaluation
  - subagent
  - delegate_task
  - iteration
  - loop
  - judge
  - review
triggers:
  - quality loop
  - judge output
  - llm-as-judge
  - evaluate response
  - score output
---

# LLM-as-Judge — Quality Loop

## Description

Pattern : l'agent produit un output, un subagent juge l'évalue sur des critères, et si le score est insuffisant, l'agent ré-itère avec les retours.

```
Agent (output) → delegate_task → Judge (/10) → PASS (< 8/10) → Re-try avec feedback
                                                  ↓
                                               PASS (≥ 8/10) → "Tâche finie ?" → FIN
```

## Protocole exact

### 1. L'agent produit le livrable
Utiliser les outils normaux (terminal, write_file, etc.)

### 2. Appel du juge via delegate_task

```python
delegate_task(
    context=f"""Tâche originale : {task}

Output à évaluer :
{output}

Critères de notation /10 :
- Critère 1 (description) : /3
- Critère 2 (description) : /3
- Critère 3 (description) : /2
- Critère 4 (description) : /2

Règle : réponds EXACTEMENT au format :
SCORE: X/10
FEEDBACK: (2 phrases max)
PASS: YES (si ≥ 8/10) ou NO (si < 8/10)""",
    goal="Évalue cet output selon les critères. Retourne SCORE: X/10 et PASS: YES/NO"
)
```

### 3. Décision sur le résultat

| Condition | Action |
|-----------|--------|
| `PASS: YES` + score ≥ 8 | Demander "n'estimes-tu pas que la tâche est terminée ?" |
| `PASS: NO` + score < 8 | Recommencer l'output avec le FEEDBACK en tête |
| Score baisse 2× de suite | Stop (stagnation) |
| Après N=3 rounds | Stop (hard limit) |

### 4. Boucle manuelle (prototype)

Ne pas automatiser complètement — faire les rounds un par un pour observer le comportement du judge et la qualité des itérations.

```text
Round 1 : output → judge → score 6/10 → feedback "manque X"
Round 2 : output corrigé → judge → score 8/10 → PASS → FIN
```

## Exemples de critères par type de tâche

| Type | Critères |
|------|----------|
| **Code** | Correction mathématique /3, Implémentation récursive propre /3, Exécutable /2, Clarté /2 |
| **Texte créatif** | Qualité littéraire /3, Pertinence thématique /3, Originalité /2, Structure /2 |
| **Analyse** | Précision /3, Profondeur /3, Sources /2, Clarté /2 |
| **Code review** | Bugs détectés /3, Style /2, Performance /2, Complétude /3 |

## Le prompt du judge

Le prompt judge est dans le `context` de `delegate_task`, PAS dans le système prompt de l'agent principal. Le subagent reçoit :

1. La **tâche originale** (ce qui était demandé)
2. L'**output à évaluer** (ce qui a été produit)
3. Les **critères de notation** (avec pondération)
4. Le **format de réponse attendu** (SCORE + FEEDBACK + PASS)

Le `goal` de delegate_task est une instruction courte : "Évalue selon les critères fournis."

**Important :** le format `SCORE: X/10, FEEDBACK: ..., PASS: YES/NO` est parsable par regex ou parsing simple, ce qui permet d'automatiser la boucle avec execute_code si besoin.

## Orchestrateur autonome (quality-loop.py)

Pour automatiser la boucle complète, un script Python lit la config, les critères et le prompt juge depuis des fichiers, et orchestre production → jugement → itération.

### Architecture fichiers

```
~/.hermes/skills/quality-loop/
├── config.yaml              ← Seuil, rounds max, options
├── criteria/
│   ├── poetry.txt           ← Critères pour textes créatifs
│   ├── code.txt             ← Critères pour code Python
│   ├── analysis.txt         ← Critères pour analyses techniques
│   └── general.txt          ← Critères pour explications générales
├── prompts/
│   └── judge_default.txt    ← Template juge (variables: {task} {output} {criteria} {threshold})
└── SKILL.md
```

**Principe :** le script ne contient AUCUNE indication contextuelle. Tout est dans les fichiers `.txt` et `.yaml`. Le fichier de critères et le prompt du juge sont modifiables sans toucher au script.

### Usage

```bash
python3 ~/.hermes/scripts/quality-loop.py \
  --task "Ta tâche ici" \
  --criteria poetry|code|analysis|general \
  [--max-rounds 5] \
  [--threshold 8]
```

### Ce que fait le script

1. Charge `config.yaml` (seuil, rounds max, injection feedback)
2. Charge le fichier critères (ex: `criteria/poetry.txt`)
3. Charge le template juge (`prompts/judge_default.txt`)
4. Pour chaque round (1 à max_rounds) :
   - **Produit** : appelle `hermes chat -q <task>` (avec feedback du round précédent si injecté)
   - **Juge** : appelle `hermes chat -q <prompt_rempli>` avec output + critères
   - **Parse** : extrait SCORE, FEEDBACK, PASS de la réponse du juge (regex)
   - **Décide** : si PASS=YES, demande à l'agent de confirmer "FINI" → sortie. Sinon, round suivant avec le feedback injecté dans le prompt
5. Journalise chaque round dans `~/.hermes/quality-loop-logs.jsonl`
6. Produit un rapport markdown dans `~/.hermes/quality-loop-report.md`

### Appel autonome par l'agent

```python
terminal(command="""
python3 ~/.hermes/scripts/quality-loop.py \\
  --task "Explique le concept de protocole selon Protocolized" \\
  --criteria general \\
  --max-rounds 5 \\
  --threshold 8
""", timeout=300, background=True, notify_on_complete=True)
```

Le rapport (stdout + fichier) arrive dans le chat utilisateur automatiquement.

### Résultats de la session de prototypage (Juillet 2026)

| Test | Tâche | Scores | Rounds | Verdict |
|------|-------|--------|--------|---------|
| 1 | Poème Bitcoin (style épique, 14 vers) | **9.5/10** | 1 | ✅ PASS direct |
| 2 | Fonctions récursives π + exponentielle | **10/10** | 1 | ✅ PASS direct |
| 3 | Analyse code Hermes (IterationBudget) | **10/10** | 1 | ✅ PASS direct |
| 4 | Fibonacci Binet (tâche complexe) | **7→9/10** | 2 | ✅ Boucle qualité active |

Le test 4 prouve la boucle d'amélioration : round 1 à 7/10 (feedback du juge sur précision manquante, pas de version récursive), round 2 à 9/10 avec Decimal, version récursive, et tests comparatifs. **Amélioration de +2 points en 1 itération.**

### Pitfalls du script orchestrateur

- **`hermes chat -q`** n'est pas disponible si la session Hermes n'a pas de binaire CLI accessible. Dans ce cas, utiliser `delegate_task` à la place.
- **Timeout** : 60s par défaut pour chaque appel Hermes. Pour des tâches longues, augmenter avec un paramètre.
- **`pyyaml`** requis pour lire `config.yaml`. Installer avec `pip3 install --break-system-packages pyyaml`.
- **Critères inadaptés** : si le juge donne un score faible à cause de critères qui ne correspondent pas à la tâche (ex: `code` pour un texte), le problème est dans le fichier critères, pas dans le script. Choisir le bon fichier ou le modifier.

### Nommer avant de construire

Leçon de la session Protocolized : la plus grande valeur d'un framework conceptuel est souvent dans sa **taxonomie** — les noms qu'il donne aux phénomènes — pas dans son implémentation. Avant de construire un outil quality-loop, le travail de nommer les critères, les états (PASS/FAIL), et les métriques (SCORE/10) EST le premier acte de construction. La boucle qualité n'a fonctionné que parce que le juge et l'agent partageaient un vocabulaire commun (SCORE, FEEDBACK, PASS, round). Le nommer précède et conditionne le faire.

## Pitfalls

- **Judge sans output** : si le contexte ne contient pas l'output à juger, le judge répond "je ne vois pas l'output". Toujours inclure l'output complet dans le context, pas seulement la tâche.
- **Score trop élevé au premier tour** : un score ≥ 8/10 avec PASS: YES dès le premier round est possible (ex: poème 9.5/10). Dans ce cas, demander à l'agent principal "selon toi, la tâche est-elle terminée ?" avant de conclure.
- **Itérations infinies** : le judge peut ne jamais donner ≥ 8/10. Toujours prévoir un max_rounds (5 recommandé) et un critère de stagnation (score baisse ou stagne 2 tours).
- **Modèle du judge** : le judge utilise le même modèle que l'agent principal (via delegation.default_model). Si le modèle est faible, le judge peut être incohérent.
- **Asynchronicité** : delegate_task retourne le résultat plus tard dans le fil de conversation. Ne pas essayer de boucler avec une `while` Python synchrone — faire les rounds manuellement un par un.

## Références théoriques

- Voir `references/while-true-theory.md` sous tx-notify pour l'analyse des boucles infinies bien élevées
- Voir `references/session-protocol-tests.md` dans cette skill pour les résultats concrets des tests de la session de prototypage (Juillet 2026)
- Le pattern LLM-as-Judge est un cas particulier de **Büchi automaton** : l'état acceptant (score ≥ 8) doit être visité avant un nombre fini d'itérations. Sans cela, la boucle est un `while true` sans garde-fou formel.