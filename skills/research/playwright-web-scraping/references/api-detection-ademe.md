# API Detection : bilans-ges.ademe.fr

Site : ADEME Bilans GES (Angular SPA)
URL : https://bilans-ges.ademe.fr/
Découverte : 2026-07-08

## Endpoints API REST publics (sans auth)

| Endpoint | Description | Méthode |
|----------|-------------|---------|
| `/api/inventories?page=N&itemsPerPage=N&publication.status[]=valide&publication.status[]=a-tr` | Liste des bilans GES publiés | GET |
| `/api/activity_sectors` | 16 secteurs d'activité | GET |
| `/api/structure_types` | 5 types (Association, Collectivité, Établissement public, État, Entreprise) | GET |
| `/api/people_number_groups` | 14 tranches d'effectifs | GET |
| `/api/regions` | 25 régions + départements | GET |
| `/api/exports/public-inventories/latest` | Lien vers l'export CSV complet (55 Mo) | GET |
| `/api/medias/{uuid}/download` | Téléchargement des fichiers (exports, images...) | GET |

## Méthode de détection

Depuis Playwright (full Chromium) :
```python
reqs = await page.evaluate('() => performance.getEntriesByType("resource").map(r => r.name)')
# Filtrer pour trouver les endpoints API
api_urls = [r for r in reqs if '/api/' in r.lower()]
```

## Structure d'un bilan (JSON)

```json
{
  "id": "uuid",
  "identitySheet": {
    "reportingYear": 2024,
    "APECode": {"id": "5813Z", "label": "Édition de journaux"},
    "consolidationMode": 0,
    "creatorEmail": "contact@example.com",
    "requiredPCAET": null,
    "collectivityType": {"label": "Communes"},
    "turnover": 338000,
    "csrd": false,
    "peopleNumberGroup": "...",
    "structureType": "...",
    "sector": "...",
    "region": "..."
  },
  "publication": {
    "status": "valide",
    "date": "2025-01-01"
  }
}
```

## Export CSV complet

L'export CSV contient 55+ Mo avec 30+ colonnes : ID, Méthode BEGES (V4/V5), Date de publication, Type de structure, Raison sociale, SIREN, APE, Année de reporting, Effectif, Secteur, Région, etc.

```bash
curl -s "https://bilans-ges.ademe.fr/api/exports/public-inventories/latest" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['file'])" \
  | xargs -I{} curl -sL "https://bilans-ges.ademe.fr{}" -o export_bilans_ges.csv
```

## Recherche paramétrée

La page `/bilans` expose un formulaire avec 30 champs qui sont envoyés en query params à `/api/inventories`. Filtres disponibles :

- SIREN (text)
- Raison sociale (text)
- Année de reporting (select: 2004-2026)
- Secteur d'activité (select: 16 valeurs)
- Région siège (select: 25 valeurs)
- Effectif (select: 14 tranches)
- Type de structure (checkbox: Association, Collectivité, Établissement public, État, Entreprise)
- Soumise à la CSRD ? (select: Oui/Non)
- Réalise un PCAET ? (select: Oui/Non)
- Aide diag decarbon'action ? (select: Oui/Non)
