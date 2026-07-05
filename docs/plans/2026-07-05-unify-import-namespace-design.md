# Unification de l'espace de noms d'import (racine nue unique)

**Date** : 2026-07-05 · **Statut** : validé · **Origine** : item 🟠 de l'audit dette 2026-07-05

## Contexte et décision

Trois racines `sys.path` (`.`, `backend`, `backend/api` — [pytest.ini](../../pytest.ini),
`PYTHONPATH` du [Dockerfile](../../deploy/Dockerfile), hack de
[asgi.py](../../backend/api/animetix_project/asgi.py)) rendent chaque module importable
sous 2-3 identités : `animetix` / `backend.api.animetix`, `core` / `backend.core`, etc.
Django enregistre l'app sous `animetix` nu ([settings.py:195]) mais le même settings
référence `backend.api.animetix.auth.*` dans `AUTHENTICATION_BACKENDS`, `MIDDLEWARE` et
DRF — les deux identités se chargent donc réellement en prod, et
[middleware.py:15-27](../../backend/api/animetix/middleware.py) contient déjà un hack
runtime qui synchronise les contextvars entre les deux copies. Les tests portent un
`MetaPathFinder` custom (`SrcPipelineMapper`, [tests/conftest.py:20-66]) pour un
troisième alias hérité (`src.pipeline.*`).

**Décision (validée)** : racine canonique = **la racine nue** (`animetix`,
`animetix_project`, `core`, `adapters`, `pipeline`) — identité d'`INSTALLED_APPS` et de
~95 % du code (109+103 fichiers `animetix` nu, 204 fichiers `core/adapters/pipeline`
nus, contre ~23 fichiers `backend.*`). Unification **complète** (pas seulement
`animetix`), hacks supprimés, tripwire durable.

Alternatives écartées : `backend.*` canonique (400+ fichiers, ré-enregistrement de
l'app) ; conserver l'alias synchronisé (institutionnalise le double chargement).

## Périmètre

### 1. Réécritures vers la racine nue

| Zone | Fichiers | Changement |
| --- | --- | --- |
| Settings | `backend/api/animetix_project/settings.py` (l.207, 232, 249, 250) | chaînes `backend.api.animetix.auth.X` → `animetix.auth.X` |
| Pipeline (import vivant) | `backend/pipeline/characters/combat_data.py:7` | `from backend.api.animetix.containers` → `from animetix.containers` |
| Pipeline (imports morts, layout `src/backend` disparu) | `backend/pipeline/anime/6_generate_sagas.py`, `backend/pipeline/anime/vectorize_anime.py`, `backend/pipeline/manga/vectorize_manga.py` | `from backend.animetix.containers` → `from animetix.containers` ; supprimer les `sys.path.append(.../src...)` vestigiaux et s'assurer que `backend/api` est sur le path de ces scripts standalone |
| `backend.core/adapters/pipeline` (20 fichiers) | `backend/api/animetix/api/developer.py`, `explore.py`, `backend/pipeline/mlops/dpo_dataset_compiler.py`, `ft_dataset/dialogue_generators.py`, `backend/scripts/sync_gold_ground_truth.py`, `scripts/detect_embedding_drift.py`, `scripts/verify/verify_brain_adapter.py`, et 13 tests : `tests/adapters/inference/test_cross_frame_attention.py`, `test_local_text_adapter.py`, `tests/adapters/test_video_analysis_coverage.py`, `test_video_rag.py`, `tests/backend/test_lore_ingestion_beam.py`, `tests/mlops/test_dpo_dataset_compiler.py`, `test_dpo_dataset_compiler_extra.py`, `test_finetuning_dataset.py`, `test_index_otaku_knowledge_coverage.py`, `test_japanese_market.py`, `test_run_provenance.py`, `test_semantic_drift_analyzer.py`, `test_sql_quality_pipeline.py` | imports nus |
| Alias `src.pipeline` (5 tests) | `tests/pipeline/test_advanced_scrapers.py`, `test_enrich_db_scraper.py`, `test_expert_scrapers.py`, `test_neo4j_security.py`, `test_specialized_scrapers.py` | `src.pipeline.*` → `pipeline.*` |

### 2. Hacks supprimés (devenus sans objet)

- Le sync contextvars inter-namespaces de `backend/api/animetix/middleware.py`
  (l.15-27 et le bloc associé).
- `SrcPipelineMapper` + `AliasLoader` + le module `src` fabriqué de
  `tests/conftest.py:20-66`.

### 3. Tripwire (3 couches)

Supprimer `backend/__init__.py` ne suffit pas : avec la racine du repo sur `sys.path`,
les **namespace packages implicites** maintiendraient l'alias silencieusement. Donc :

1. **Garde runtime** : `backend/__init__.py` lève
   `ImportError("Import via 'backend.*' est interdit : utilisez la racine nue "
   "(animetix, core, adapters, pipeline). Voir docs/plans/2026-07-05-unify-import-"
   "namespace-design.md")` — attrape aussi les chaînes dynamiques (`import_string`)
   et les imports tardifs.
2. **Lint** : règle ruff `TID251` (flake8-tidy-imports banned-api) interdisant les
   imports `backend` et `src` — feedback à l'édition et au lint CI.
3. **Test d'hygiène** : `tests/test_import_hygiene.py` scanne `backend/`, `tests/`,
   `scripts/` pour `from backend.` / `import backend` / `src.pipeline` résiduels, y
   compris dans les chaînes des modules settings.

### Ne PAS toucher

- Les racines `sys.path` elles-mêmes (pytest.ini, PYTHONPATH Docker, asgi.py) : les
  trois restent nécessaires (`.` pour `tests.*`, `backend` pour `core/adapters/
  pipeline`, `backend/api` pour `animetix*`). L'unification se fait par convention
  d'import + tripwire, pas par chirurgie du path.
- `backend/GEMINI.md`, coverage `--cov=backend` (mesure par chemin, pas par import).

## Risques et parades

- **`regression_benchmark.py`** (backend/pipeline/evaluation/) documente qu'il dépend
  de la résolution `backend.api.*` depuis la racine : après réécriture des chaînes
  settings, son header doit ajouter `backend/api` à `sys.path` (à vérifier/corriger au
  plan).
- **Chaînes pointées hors `.py`** : grep exhaustif fait — seul un commentaire de
  `pyproject.toml:35` mentionne `backend.core.x` (note mypy, à laisser).
- **Usage légitime de `import backend`** : aucun trouvé (grep) ; le garde ne s'exécute
  que sur import explicite — coverage, dbt, scripts par chemin ne le déclenchent pas.
  Si le plan en découvre un, le réécrire d'abord.
- **Double chargement historique** : après unification, une seule identité de
  `animetix.models`/signaux/DI — les tests middleware existants et `manage.py check`
  valident le boot.

## Vérification

1. Nouveau test d'hygiène vert + garde runtime en place (test : `import backend.core`
   doit lever `ImportError`).
2. `manage.py check` + collecte pytest complète sans erreur.
3. Suite CI-équivalente : `pytest -m "not integration" --cov=backend` ≥ 75 %.
4. ruff (avec la nouvelle règle TID251) + black.
5. Grep final : zéro `backend\.(api|core|adapters|pipeline|animetix)` et zéro
   `src\.pipeline` dans le code (hors docs/archives).
