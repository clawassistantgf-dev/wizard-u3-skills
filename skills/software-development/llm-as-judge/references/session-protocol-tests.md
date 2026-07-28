# Session Prototype — Tests LLM-as-Judge

Tests réalisés le 28 Juillet 2026 sur le pattern quality loop.

## Test 1 — Poème Bitcoin

| Champ | Valeur |
|-------|--------|
| Tâche | Poème épique/mystique sur Bitcoin, 12 vers min |
| Output | 14 vers, style rimé, vocabulaire crypto (HODL, mining, wallet, proof-of-work) |
| Judge | 9.5/10 — PASS: YES |
| Feedback | "Poème très réussi alliant lexique technique et imagerie épique. Métaphore du phénix numérique couronne une structure solide." |
| Iterations | 1 (score ≥ 8/10 dès le premier round) |

**Conclusion :** le judge fonctionne. Un output de bonne qualité obtient un score élevé sans itération nécessaire.

## Test 2 — Fonctions récursives Python (π + exponentielle)

| Champ | Valeur |
|-------|--------|
| Tâche | Deux fonctions récursives : calc_exp(x,n) par Taylor, calc_pi(n) par Leibniz |
| Output | Code exécutable, tests passent, erreurs: exp 4e-16, pi 2e-3 (500 termes) |
| Judge | ⏳ En cours |

**Bug corrigé en cours de route :** la convergence de Leibniz est lente (500 termes → 3.1395, erreur 0.2%). L'assertion était trop serrée (1e-3 → relaxée à 5e-3). Le judge a été notifié de cette limitation dans le contexte.

## Architecture du prompt judge

```
Context (transmis au subagent) :
1. Tâche originale demandée
2. Output produit (texte complet + output d'exécution si code)
3. Critères /10 avec pondération
4. Format de réponse strict : SCORE + FEEDBACK + PASS

Goal (instruction au subagent) :
"Évalue selon les critères fournis. Retourne SCORE: X/10 et PASS: YES/NO"
```

## Observations

- Le judge a besoin de l'output COMPLET dans le context — ne pas le mettre dans le goal
- Le format SCORE/PASS/FEEDBACK est bien respecté et parsable
- Un score ≥ 8/10 dès le premier round arrive (output de bonne qualité)
- Le juge n'a pas halluciné de score — les feedbacks étaient cohérents avec l'output
- La délégation asynchrone (delegate_task background) fonctionne bien mais empêche l'itération automatique synchrone → préférer les rounds manuels pour le prototypage