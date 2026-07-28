# Tests de la boucle qualité

## Test 1 — Poème Bitcoin (poetry criteria)

**Résultat :** 9.5/10 ✅ (1 round, PAS de boucle nécessaire)

## Test 2 — Fonctions récursives π + exponentielle (code criteria)

**Résultat :** 10/10 ✅ (1 round)

## Test 3 — Analyse de code Hermes (analysis criteria)

**Résultat :** 10/10 ✅ (1 round)

## Test 4 — Fibonacci Binet (code criteria, tâche volontairement complexe)

**Premier round :** 7/10 ❌ (sous le seuil de 8)
**Deuxième round :** 9/10 ✅ (amélioration après injection du feedback)

**Boucle validée :** 7 → 9 sur 2 rounds avec feedback automatique.

## Leçons

- **Critères adaptés = scores justes.** `code` pour du code technique a donné 7/10 au premier essai (Binet oublié, pas de récursion pure), `general` pour une explication a donné 10/10 direct.
- **Le feedback injecté fonctionne.** Le round 2 a explicitement ajouté `Decimal`, `fib_recursive`, et les tests comparatifs suite au feedback du juge.
- **2 rounds suffisent** pour la plupart des tâches. 5 rounds max évite les boucles infinies sans être trop restrictif.