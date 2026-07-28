# Export CSV Bilans GES ADEME — Schéma des 104 colonnes

Source : `https://bilans-ges.ademe.fr/api/exports/public-inventories/latest`
Fichier : CSV 55+ Mo, séparateur `;`, quote `"`, encodage UTF-8 BOM.

## Colonnes principales (1–34)

| # | Nom | Type | Description |
|---|-----|------|-------------|
| 0 | Id | UUID | Identifiant unique du bilan |
| 1 | Méthode BEGES (V4,V5) | string | `v4` ou `v5` |
| 2 | Date de publication | date | Format `JJ/MM/AAAA` |
| 3 | Type de structure | string | Association, Collectivité, Établissement public, État, Entreprise |
| 4 | Type de collectivité | string | Commune, Métropole, etc. |
| 5 | Raison sociale | string | Nom légal |
| 6 | SIREN principal | string | 9 chiffres |
| 7 | APE(NAF) associé | string | Code NAF |
| 8 | Libellé | string | Description du code NAF |
| 9 | Effectif | string | Tranche (ex: "Entre 20 et 49") |
| 10 | Population | string | Pour collectivités |
| 11 | Région | string | Nom de région |
| 12 | Code département | string | 2-3 chiffres |
| 13 | Département | string | Nom |
| 14 | Structure obligée | string | `oui` / `non` |
| 15–18 | Entités consolidées | string | SIREN, NAF, départements, statut |
| 19 | Mode de consolidation | string | `Opérationnel` / `Financier` |
| 20 | Année de reporting | int | 2004–2026 |
| 21 | Assujetti DPEF/PCAET ? | string | `oui` / `non` |
| 22–26 | Documents réglementaires | string | Liens DPEF, CSRD, pages |
| 27 | Aide diag décarbon'action | string | `oui` / `non` |
| 28–33 | Paramètres méthodologiques | string | Seuil, influence, sous-traitance, etc. |
| 34 | Justification postes écartés | string | Texte libre |

## Colonnes d'émissions (35–56) — Publication

| # | Poste | Description |
|---|-------|-------------|
| 35 | P1.1 | Émissions directes — combustibles fossiles |
| 36 | P1.2 | Émissions directes — procédés industriels |
| 37 | P1.3 | Émissions directes — fuites / gaz frigorigènes |
| 38 | P1.4 | Émissions directes — biomasse |
| 39 | P1.5 | Émissions directes — autres |
| 40 | P2.1 | Énergie — électricité, chaleur, froid |
| 41 | P2.2 | Énergie — vapeur |
| 42 | P3.1 | Achats de biens |
| 43 | P3.2 | Immobilisations |
| 44 | P3.3 | Transport amont/aval |
| 45 | P3.4 | Déchets |
| 46 | P3.5 | Déplacements professionnels |
| 47 | P4.1–P4.5 | Postes amont (5 sous-postes) |
| 52 | P5.1–P5.4 | Postes aval (4 sous-postes) |
| 56 | P6.1 | Autres |

Toutes les valeurs sont en **tCO2e** (tonnes équivalent CO2). Format : nombre décimal avec `.` ou `,` (détecter automatiquement).

## Colonnes de référence (57–80)

Même structure que 35–56 mais pour l'année de référence (57 = année calculée, 58 = année, 59–80 = valeurs).

## Colonnes qualitatives (81–96)

| # | Nom | Description |
|---|-----|-------------|
| 81 | Présentation de l'organisation | Texte libre |
| 82 | Politique développement durable | Texte libre |
| 83 | Réduction attendue émissions directes | Texte/chiffre |
| 84 | Réduction attendue émissions indirectes | Texte/chiffre |
| 85 | Objectif 2030 | Texte |
| 86 | Objectif 2050 | Texte |
| 87 | Autres horizons | Texte |
| 88 | Actions et moyens | Texte |
| 89 | Analyse résultats | Texte |
| 90 | Émissions évitées | Texte |
| 91–96 | Énergie, FE, PRG, incertitudes, sources | Texte |

## Colonnes d'identité (97–103)

| # | Nom | Description |
|---|-----|-------------|
| 97 | Siret | 14 chiffres |
| 98 | Comparaison précédent bilan | Texte |
| 99 | Lien URL rapport complet | string | 
| 100–103 | Responsable suivi | [Masqué] |

## Utilisation en Python

```python
import csv
with open('export.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    for row in reader:
        # Accès par nom de colonne
        siren = row['SIREN principal']
        scope1 = float(row['Emissions publication P1.1'] or 0)
        scope2 = float(row['Emissions publication P2.1'] or 0)
```

## Notes

- Les champs vides sont des chaînes vides, pas des NULL
- Les valeurs numériques peuvent utiliser `,` comme séparateur décimal — normaliser avec `.replace(',','.')`
- Les objectifs (colonnes 83–86) sont en texte libre, pas structurés — parser avec regex si nécessaire
- Le lien rapport (colonne 99) pointe parfois vers un PDF, parfois vers bsky.app, parfois vide
- Les données responsbles (100-103) sont systématiquement masquées dans l'export