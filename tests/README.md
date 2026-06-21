# Organisation des tests

> **Découverte** : `pytest.ini` fixe `testpaths = tests` et `pythonpath = . backend backend/api`.
> Tous les tests sont donc découverts **quel que soit** le sous-dossier — le rangement
> ci-dessous est une **convention de lisibilité**, pas une contrainte technique.
> Exécution unitaire (hors services externes) : `pytest -m "not integration"`.

## Convention cible — un foyer par couche

Le rangement suit les **couches** de l'architecture (hexagonale + Django), pas le module exact :

| Dossier | Couche testée | Exemples |
|---------|---------------|----------|
| `tests/core/` | **Cœur hexagonal** : `core/domain/services`, `core/ports`, entités, schémas | `test_emoji_service.py`, `test_config_port.py`, `test_ai_schemas.py` |
| `tests/adapters/` | **Adapters** (inference / persistence) qui implémentent les ports | `test_fallback_adapter.py`, `test_pgvector_repository_adapter.py` |
| `tests/api/` | **Endpoints DRF / consumers** (couche HTTP/WS Django) | `test_admin.py`, `test_companion.py` |
| `tests/backend/` | **Projet Django** transverse : settings, middleware, ASGI, management commands, tasks Celery, modèles | `test_settings.py`, `test_middleware_async.py`, `tasks/…` |
| `tests/pipeline/` | **Pipeline MLOps & scrapers** (ingestion, enrichissement, neo4j/chroma) | `pipeline/manga/…`, `test_enrich_db_scraper.py` |
| `tests/mlops/` | **MLOps** : datasets DPO/SFT, provenance, eval | `test_dpo_dataset_compiler.py` |
| `tests/scripts/`, `tests/security/`, `tests/deploy/` | scripts utilitaires / garde-fous sécurité / scripts de déploiement | — |
| `tests/helpers/` | **Utilitaires de test partagés** (PAS des tests) | `image_utils.py` |
| `tests/e2e/`, `tests/performance/` | bout-en-bout / perf | — |

**Règle d'or** : un test va là où vit la **couche** qu'il vérifie. Le cœur (`core.*`) →
`tests/core/`. Un endpoint DRF → `tests/api/`. Un réglage Django → `tests/backend/`.

## Consolidation des foyers (faite)

La consolidation physique des couches ayant historiquement **deux foyers** a été
réalisée (2026-06-21, après le merge de `coverage-consolidation`) — collection pytest
**inchangée à 2313 tests** avant/après, historique git préservé (`git mv`) :

- **Cœur** : `tests/backend/core/…` → fusionné dans **`tests/core/`** ✅
- **API** : `tests/backend/api/…` → fusionné dans **`tests/api/`** ✅
- **Pipeline** : `tests/pipeline_logic/…` → fusionné dans **`tests/pipeline/`** ✅ (les
  `__init__.py` redondants/identiques supprimés ; **pas** de `__init__.py` ajouté à
  `tests/api`/`tests/pipeline`, pour préserver la sémantique d'import existante).

Il n'y a **pas de duplication** (aucun test en double). Le déplacement n'apporte **aucun
gain fonctionnel** (découverte inchangée via `testpaths = tests`) — uniquement de la
lisibilité.

**Décision restante (non traitée ici)** : `tests/backend/views/…` — à conserver sous
`tests/backend/` (couche projet Django) **ou** à déplacer vers `tests/api/` selon ce que
ces vues testent (endpoints = `tests/api/`). À trancher au cas par cas.
