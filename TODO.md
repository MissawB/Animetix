# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.

## 🔴 Critiques

_Aucun item ouvert._

## 🟠 Élevés

- [ ] **Sécu — révoquer les clés mortes du `.env` local** _(reliquat de l'hygiène post-fuite `.env`, close le 2026-07-09 — secrets montés sur `animetix-web` + 33 images pré-exclusion purgées, archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ Révoquer `TRIPO_API_KEY` et `MAPBOX_TOKEN` depuis leurs dashboards respectifs (Tripo3D / Mapbox — action manuelle externe) : valeurs réelles dans le `.env` local, consommées nulle part dans le code. Risque résiduel faible depuis la purge des anciennes images.

## 🟡 Moyens

- [ ] **Backend — exceptions avalées à grande échelle** _(audit dette 2026-07-05)_
  - 168 `except Exception` log-et-continue + 77 `pass` silencieux, dont un consumer WebSocket ([undercover.py:148-149](backend/api/animetix/consumers/undercover.py#L148-L149)), plusieurs vues des sous-modules [api/labs/](backend/api/animetix/api/labs/), [reachability_health_mixin.py:59-60](backend/adapters/inference/reachability_health_mixin.py#L59-L60). Remplacer par du log/handling explicite, au moins sur les chemins runtime.
- [ ] **Backend — module mort `brain_api.py` (539 lignes)** _(audit dette 2026-07-05)_
  - [brain_api.py](backend/adapters/inference/brain_api.py) n'est importé nulle part (le container câble `brain_api_adapter`). À supprimer — son nom quasi identique au module actif est un piège.
- [ ] **Backend — signaux dispersés + write amplification** _(audit dette 2026-07-05)_
  - Signaux dans [models.py:549-557](backend/api/animetix/models.py#L549-L557) ET [signals.py](backend/api/animetix/signals.py) ; `save_user_profile` ré-écrit le profil à **chaque** save de User et lève `RelatedObjectDoesNotExist` si le profil manque (users bulk/legacy). Consolider et garder.
- [ ] **Backend — squash des migrations : purge des originales** _(audit dette 2026-07-05 ; squash livrée le 2026-07-08, archivée dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ La squash `0001_squashed_0049` existe (commit `68fec496`). Reste : une fois la squash enregistrée comme appliquée partout (prod Neon comprise), supprimer les 49 migrations d'origine et retirer l'attribut `replaces` (procédure Django standard).
- [ ] **Backend — noms de modèles hardcodés + mismatch de version** _(revue archi 2026-06-22 ; Phases 1/2a livrées, archivées dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ **Reste (Phase 2b)** : registre d'**IDs logiques locaux** (`llama3`, `Qwen2.5-1.5B` vs `Qwen3.5-4B`, `DRAFT_MODEL_ID`, `VibeThinker-3B`, `FLUX`) + fusion résiduelle [pipeline/models_registry.py](backend/pipeline/models_registry.py).

## 🟢 Faibles

- [ ] **Settings — défauts d'infra codés en dur** _(audit dette 2026-07-05)_
  - `DEBUG=True` par défaut hors-prod ([settings.py:104](backend/api/animetix_project/settings.py#L104)) : toute la sécurité repose sur `DJANGO_ENV=production` ; URLs hf.space et emails de service accounts en littéraux ([settings.py:331,391,395,581,595,620](backend/api/animetix_project/settings.py#L331)) ; `print()` au démarrage ([settings.py:375,510](backend/api/animetix_project/settings.py#L375)) au lieu du logger ; `ssl_cert_reqs: None` sur le cache `rediss://` ([settings.py:361](backend/api/animetix_project/settings.py#L361)) désactive la vérif de cert.
- [ ] **Backend — duplication entre adapters d'inférence** _(revue archi 2026-06-22 ; mixins de factorisation livrés, archivés dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ **Reste (résiduel, hors scope)** : `RerankMixin` et `LocalTextAdapter.get_text_embedding` (chargements inline aux sémantiques d'erreur différentes) ; `LocalGuardrailAdapter` (aucun modèle).
- [ ] **Backend — exposer le streaming async aux endpoints HTTP** _(suite du streaming async natif — les 5 vues SSE sont désormais async natives, détail archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ **Reste** : les **8 processors one-shot** (Plan/Research/Judge/Acquire/Speculate/VlmRerank/GraphExplore/SagaLookup) restent sur le pont-thread par défaut (appels bloquants ponctuels → bénéfice marginal d'un `aprocess` natif, YAGNI) ; suppression du sync (`process`/`run_workflow`/`plan_and_solve_stream`) différée tant que les 8 dépendent du pont + voie WSGI.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
