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

## Recouvrements connus à consolider (dette, déplacement différé)

Il n'y a **pas de duplication** (aucun test en double), mais quelques couches ont **deux
foyers** par héritage historique. Cible de consolidation — **à faire quand la branche
`coverage-consolidation` aura mergé**, pour éviter les conflits de déplacement :

- **Cœur** : `tests/backend/core/…` (≈6 fichiers, layout miroir de la source) → fusionner dans **`tests/core/`** (layout plat).
- **API** : `tests/backend/api/…` → fusionner dans **`tests/api/`**.
- **Vues** : `tests/backend/views/…` → conserver sous `tests/backend/` (couche projet Django) **ou** déplacer vers `tests/api/` selon ce qu'elles testent (endpoints = `tests/api/`).
- **Pipeline** : `tests/pipeline_logic/` (3 fichiers) → fusionner dans **`tests/pipeline/`**.

Le déplacement physique n'apporte **aucun gain fonctionnel** (découverte inchangée) ;
il n'est utile que pour la lisibilité. À planifier comme un sweep unique, hors période
de forte activité sur `tests/` (sessions parallèles), en vérifiant après coup les
imports relatifs et les fixtures (attention au piège **dual-namespace** `backend.core.*`
vs `core.*` — cf. la mémoire projet / `conftest.py`).
