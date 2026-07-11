# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.

## 🔴 Critiques

_Aucun item ouvert._

## 🟠 Élevés


## 🟡 Moyens


## 🟢 Faibles

- [ ] **Backend — exposer le streaming async aux endpoints HTTP** _(suite du streaming async natif — les 5 vues SSE sont désormais async natives, détail archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - ⏳ **Reste** : les **8 processors one-shot** (Plan/Research/Judge/Acquire/Speculate/VlmRerank/GraphExplore/SagaLookup) restent sur le pont-thread par défaut (appels bloquants ponctuels → bénéfice marginal d'un `aprocess` natif, YAGNI) ; suppression du sync (`process`/`run_workflow`/`plan_and_solve_stream`) différée tant que les 8 dépendent du pont + voie WSGI.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
