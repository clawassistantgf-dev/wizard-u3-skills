# Quality Loop — Résultats des tests (Juillet 2026)

## Test 1 : Poème Bitcoin

- **Tâche** : Écrire un poème sur Bitcoin (style épique/mystique, 14 vers)
- **Critères** : poetry (qualité littéraire /4, pertinence Bitcoin /3, originalité /3)
- **Résultat** : **9.5/10** au round 1 — PASS direct
- **Feedback** : "Poème très réussi alliant lexique technique et imagerie épique"
- **Leçon** : les tâches créatives obtiennent souvent un score élevé dès le premier round si les critères sont bien calibrés

## Test 2 : Fonctions récursives π + exponentielle

- **Tâche** : Écrire deux fonctions récursives Python : exp(x) par série de Taylor, π par Leibniz
- **Critères** : code (correction mathématique /3, récursivité /3, exécutable /2, clarté /2)
- **Résultat** : **10/10** au round 1 — PASS direct
- **Feedback** : "Code récursif exemplaire"
- **Leçon** : le code bien structuré passe facilement. Les critères techniques sont plus objectifs pour le juge.

## Test 3 : Analyse de code Hermes

- **Tâche** : Analyser la classe IterationBudget d'Hermes
- **Critères** : analysis (pertinence /3, précision technique /3, utilité /2, clarté /2)
- **Résultat** : **10/10** — le juge a vérifié CHAQUE affirmation contre le code source réel
- **Leçon** : le juge vérifie les faits. Une analyse qui cite des chiffres exacts (62 lignes, 5 méthodes, 1 verrou) obtient un score parfait.

## Test 4 : Fibonacci par Binet (boucle d'amélioration)

- **Tâche** : Fibonacci par formule de Binet avec précision numérique, version récursive, tests
- **Critères** : code
- **Résultat** : **7/10 → 9/10** en 2 rounds ✅
- **Round 1** : 7/10 — code fonctionnel mais juge demande précision Decimal et version récursive
- **Round 2** : 9/10 — ajout de Decimal pour la précision, version récursive pure avec accumulateur, tests 21/21 identiques
- **Amélioration** : +2 points en 1 itération
- **Leçon** : la boucle qualité fonctionne. Le feedback du juge injecté améliore visiblement l'output.

## Problème identifié : critères inadaptés

Un test de l'explication du minage de Bitcoin avec les critères `code` a obtenu 3/10. Les critères demandaient "correction mathématique" et "récursivité" pour un texte explicatif. **Le problème n'est pas le juge mais le fichier critères.** Depuis, un fichier `general.txt` a été ajouté pour les tâches non techniques.

## Stats globales

- 4 tests dont 1 avec boucle d'amélioration active
- Score moyen : 9.6/10
- Rounds moyens : 1.25
- Taux de PASS direct : 75%
- Amélioration moyenne par itération : +2 pts