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