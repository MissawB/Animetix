# HISTORY — Journal des travaux Animetix

> Récapitulatif daté de ce qui a été réalisé. Le détail fin est dans l'historique git ;
> les chantiers ouverts restent dans [TODO.md](TODO.md).

---

## 2026-06-20 → 2026-06-21

### 🔴 Critiques

- **Architecture core hexagonale** — le `core` n'importe plus Django (`settings`/`cache`),
  ni la `pipeline`, ni le conteneur DI (`get_container()`). 4 tranches : ports
  `Cache` / `Config` / `VectorStore` + adapters Django/Chroma ; `guardrail_service`
  déplacé dans le conteneur `agentic` (dépendance circulaire `core`↔`agentic` résolue,
  alias rétro-compat conservé). Tests verts.
- **Imports `backend.core.*` → `core.*`** — double-namespace éliminé (15 fichiers source
  + 19 de test) ; plus aucun `isinstance`/mock cassé par les modules dupliqués.
- **SSRF `sample_url` (Animetix Voice)** — `requests.get` sur une URL contrôlée par
  l'utilisateur sécurisé via `safe_http_request` (validation IP privées/loopback/
  link-local à chaque hop de redirection), à l'ingestion comme au fetch.
- **Garde-fou CI frontend** — nouveau job `frontend-checks` (`check-types` + `lint`)
  branché sur `deploy-to-prod` ; `vite build` ne type-checkant pas, c'était la seule
  barrière avant prod. `src/types/api.d.ts` (généré) ignoré par ESLint.
- **Frontend `tsc` 131 → 0** — bugs runtime `ReferenceError` (variables `catch`
  cassées par un autofix, imports manquants : `Globe`/`motion`/`Button`/`useCallback`…),
  namespace Plotly, types app, cluster XAI dédupliqué, variantes `Button`, refs
  force-graph. `useAniminator.ts` (code mort + cassé) supprimé.
- **Frontend ESLint 132 → 0** — `no-explicit-any`, `no-unused-vars`,
  `react-hooks/*` (set-state-in-effect, static-components, immutability, exhaustive-deps),
  `jsx-a11y`.
- **Désync schéma backend ↔ front** — `wallet_balance` exposé (serializer + mapping) ;
  serializers DRF + `@extend_schema` pour `vs_battle` et l'évènement SSE `xai_report`
  (XAI), `api.d.ts` resync.

### 🟠 Élevés

- **Découpe des monolithes**
  - `pipeline/mlops/finetuning_dataset.py` : **4650 → 1316 l. (−72 %)** via façade
    (ré-export, zéro changement appelants), 9 modules sous `ft_dataset/`.
  - Conteneur DI : `LazyClass` dédupliqué dans `containers/lazy.py` partagé ;
    `core_services.py` 524 → 440 l.
  - Frontend : `MultiverseCatalogPage` 740→161, `TachideskExplorerPage` 724→157,
    `Layout` 475→118 — sous-composants `React.memo` + custom hooks, refactor
    strictement préservateur (DOM/classNames/ids/hook-order identiques).
- **Services RAG / dead-code** — audit complet (script `scripts/audit_dead_services.py`).
  Prémisse « ~125 services, code mort » corrigée : les 3 services RAG ne se recouvrent
  pas, ils se **composent** (fusion abandonnée à raison). Code mort supprimé : 2 modules
  orphelins, 3 modules test-only, 2 modules + providers « registered-only » (jamais
  résolus), 2 providers dupliqués morts, 1 wire mort (`video_rag_service` dans
  `ResearchProcessor`). `test_container_wiring` 3/3.
- **Campagne de couverture de tests** — gate `--cov-fail-under=75` + upload Codecov posés.
  Backlog de tests (P1→P4) **entièrement traité** : **17 modules backend de 0 % à 92-100 %**
  + 14 unités frontend, **≈ 443 nouveaux tests**, tout I/O externe mocké, vrais tests de
  comportement (pas de faux-vert ; plafonds honnêtes assumés sur la glue d'entraînement).
  - **P1 MLOps & Ingestion** (8 modules) : `jikan_enrichment`, `expert_enrichment`,
    `manga/{fetch_covers,ingest_manga,vectorize_manga}`, `mlops/{merge_lora_weights,
    train_preference,rlhf_pipeline}`. *(commit `658e9b4`)*
  - **P2 Consumers async** (3 modules) : `consumers/{duel,codemanga,speech_to_speech_live}`
    + fiabilisation d'un e2e Channels flaky (timeouts 1 s → 5 s). *(commit `f4aed65`)*
  - **P3 Adaptateurs** (6 modules) : `inference/{moondream,qwen3_vl,brain_api}`,
    `persistence/{django_safety,django_semantic_cache,colbert}`. *(commit `5629108`)*
  - **P4 Frontend** (vitest 69 → 191) : stores Zustand, `ErrorBoundary`, offline
    `idb-keyval`/persister. *(commit `a5e6ac9`)*
- **Pré-commit** — config alignée CI : ruff+black en `pre-commit`, mypy + pytest
  (`-m "not integration"`) en `pre-push`. *(commit `a258021`)*

### 🐛 Bugs de production découverts via les tests

- **`DjangoSafetyAdapter` entièrement cassé** : utilisait le champ `action_taken`
  (`create()`, `filter(action_taken__in=)`, `e.action_taken`) alors que le modèle
  `AISafetyEvent` a `action` → `TypeError`/`FieldError` **à chaque journalisation
  d'évènement de sécurité (guardrails)**. Corrigé (3 références) + test `@django_db`
  round-trip ajouté comme verrou de régression. *(commit `5629108`)*

### Notes

- Plusieurs sessions ont travaillé en parallèle sur `main` ; certains lots
  (cleanup RAG, refactors front, gate CI) restent non commités au moment de ce journal,
  entremêlés dans des fichiers partagés — à committer une fois les sessions stabilisées.
- Dépôt GitHub `MissawB/Animetix` : description, homepage (Cloud Run) et topics mis à jour ;
  remote `origin` repointé sur le nom courant.
