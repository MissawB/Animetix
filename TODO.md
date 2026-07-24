# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.
> Les entrées marquées _(audit dette 2026-07-19)_ sont issues d'une seconde passe multi-agents (mêmes 4 axes) — preuves fichier:ligne vérifiées à l'écriture. Vérifié sain au passage : pas d'injection SQL (tout paramétré), settings durcis, aucun test skippé/xfail, aucun artefact lourd versionné hors LFS, throttle akinetix classic OK (`CpuGameThrottle` présent).
> Les entrées marquées _(audit dette 2026-07-22)_ sont issues d'une troisième passe multi-agents (mêmes 4 axes) — preuves fichier:ligne vérifiées à l'écriture. Aucun constat critique. Vérifié sain au passage : aucun secret en dur, aucun `except:` nu, fuite `sys.modules` gardée (conftest autouse), fixtures factorisées, gate couverture 76 % verrouillé en lockstep, URLs API frontend centralisées (`apiClient`), toutes les `<img>` avec `alt`, aucun TODO/FIXME dans le code, 4 adaptateurs d'inférence tous câblés (pas de code mort DI), deps des 5 jeux requirements contraintes par construction (`-c`), logging structuré + Sentry + tripwire DEBUG OK.

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, run GPU différé (mode économie)** _(phase 1 2026-07-14 ; run tenté 2026-07-17 ; facturation rétablie 2026-07-22, cf. HISTORY)_
  - Facturation GCP **rétablie le 2026-07-22**, mais le run GPU est **différé volontairement** : période de réduction des frais pendant la validation AdSense (sensors en pause, Redis migré Upstash, connecteur VPC retiré — cf. HISTORY 2026-07-22). Les ~3,5 h de vecteurs déjà écrits sont préservés (job reprenable).
  - **Reste (quand le mode économie sera levé)** : 1) vérifier/relever le plafond de budget (50 € conseillé) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

- [x] **Backend — galerie VN publique non bornée + N+1 + sur-exposition (fait 2026-07-23)** _(audit dette 2026-07-22)_
  - Fixé en TDD (4 tests de caractérisation dans `test_forge_vn_api.py::TestTheaterGallery`) : cap `GALLERY_MAX_ITEMS=50` + `select_related("creator")` + `prefetch_related("likes")` (35 → 2 requêtes applicatives), whitelist de champs (`likes` — IDs bruts des likers — retiré du payload), `context={"request": request}` (→ `is_liked` fonctionne). Régression vérifiée : suites forge_vn/multiverse/social vertes.

- [x] **Infra — l'image Brain tourne en root (fait 2026-07-23, effectif au prochain rebuild brain)** _(audit dette 2026-07-22)_
  - Fixé : `useradd appuser` + `USER appuser` + `HOME=/home/appuser` dans le stage runtime de `Dockerfile.brain`. Volontairement **sans** `chown -R /opt/ollama` : les modèles bakés (~5 Go) ne sont que lus (world-readable suffit) et un chown récursif dupliquerait les blobs dans un layer. Seuls `/app/data/models` (caches HF/torch, écrits au 1er appel STT/XTTS) et le HOME (clé `ollama serve`, cache coqui-tts) passent à `appuser`. Vérifié : `/mnt/models` (FUSE) est en lecture seule dans les 3 consommateurs.
  - ⚠️ Dormant tant que l'image brain n'est pas rebuildée (la CI ne la redéploie jamais) — le rebuild S2S déjà en attente (cf. item Moshi/Kyutai) l'embarquera ; smoke à vérifier à ce moment-là : `/health` 200 + warm-up Ollama OK en non-root.

- [x] **CI — aucun garde-fou de dérive des migrations Django (fait 2026-07-23)** _(audit dette 2026-07-22)_
  - Fixé : `tests/deploy/test_migrations_check.py` exécute `makemigrations --check --dry-run` dans le job pytest (CI + pre-push + local, ~8 s). Marqueur `django_db` requis (`check_consistent_history` lit l'historique appliqué). Discrimination vérifiée en TDD : champ-sonde ajouté sans migration → FAIL, retiré → PASS. `test_settings` héritant d'`INSTALLED_APPS` prod, le graphe inspecté est celui de la prod.

- [x] **Frontend — régression du plafond « 0 pages > 500 lignes » — verrou eslint posé & décomposition achevée (fait 2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : règle `max-lines: 500` (lignes brutes, comme le `wc -l` des audits) dans `eslint.config.js`. Décomposition de `CovertestPage.tsx` (695 ➔ 377 l., FX extraits dans `covertestFx.ts` avec test unit) et `ClassicLobbyPage.tsx` (520 ➔ 250 l., sous-composants `ClassicUniverseSelector` & `ClassicHintConfigSection`). Exemptions ESLint retirées. Verrou 100 % actif sans exemption de page.

- [x] **Frontend — data-fetching manuel contournant react-query — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Migration des 5 pages concernées (`FinancialDashboardPage`, `AkinetixRLPage`, `OfflineSyncPage`, `MangaLabPage`, `PricingPage`) vers `useQuery` et `useMutation`. Élimination complète du data-fetching ad hoc (`useState` + `useEffect` + `catch` muets).

- [x] **Frontend — 7 pages > 350 lignes sans aucun test (prérequis au ratchet vitest) — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Création des 7 suites de tests unitaires `__tests__/<Page>.test.tsx` pour `ExpertNexusPage`, `ArchetypeNexusPage`, `ForgePage`, `ClubDashboard`, `StrategyLabPage`, `LatentSpacePage` et `AccountSettingsPage` (13 tests au total couvrant rendu initial, états loading, error et interactions). Plancher de couverture `vite.config.ts` rehaussé à **45 % statements / 35 % branches / 40 % functions / 47 % lines**.

## 🟡 Moyens

- [x] **Backend — `brain_service.py` : 28 handlers d'erreur identiques qui fuitent `str(e)` — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Remplacement des 28 requêtes dupliquées `except Exception as e` par un décorateur centralisé `@handle_brain_errors`. Les exceptions internes sont désormais capturées, loguées côté serveur avec stack trace (`logger.exception`), et retournent un statut 500 avec message générique non fuyard `{"detail": "Internal server error"}`.

- [x] **Backend — adaptateur Google GenAI : sentinelles neutres qui masquent les pannes — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Suppression des retours silencieux neutres (`0.0`, `[]`, `{label: 0.0}`) dans `google_genai_adapter.py` (`calculate_visual_similarity`, `get_text_embedding`, `get_image_embedding`, `get_video_temporal_embeddings`, `detect_objects`, `classify_image`) au profit de `raise InferenceError` explicites comme pour `generate`. Tests unitaires mis à jour (63/63 passés).

- [x] **Backend — N+1 résiduel `likes.count` + `fields="__all__"` sur serializers publics — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Suppression de `source="likes.count"` dans `VsBattleSerializer` au profit d'un `SerializerMethodField` compatible avec les annotations `likes_count` et la mémoire cache prefetched. Whitelists explicites de `fields` configurées sur `CreativeFusionSerializer`, `VsBattleSerializer` et `AISafetyEventSerializer` (suppression de `fields = "__all__"`). Annotations `Count("likes")` ajoutées dans les endpoints `list_vs_battles` et `TheaterListView`.

- [x] **Backend — god modules + typage du cœur lacunaire — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Éclatement de `models.py` (1006 l.), `serializers.py` (780 l.) et `urls/api.py` (837 l.) en packages modulaires axés par domaine (`models/` `catalog`, `manga`, `social`, `games`, `ai_ml`, `system` ; `serializers/` `catalog`, `manga`, `social`, `games`, `ai_ml` ; `urls/domains/`). Rétro-compatibilité totale assurée via réexportations `__init__.py`. Ajout d'annotations de type de retour sur les méthodes de services du domaine (`agentic_rag_service.py`). Verification complète avec `manage.py check` et suite de tests (`1635 passed`).

- [x] **Infra — CSP `'unsafe-inline'` dans `script-src` même en prod — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** : Retrait dynamique de `'unsafe-inline'` de `CSP_SCRIPT_SRC` en environnement de production (`IS_PRODUCTION=True`), injectable/désactivable uniquement via la variable d'environnement `DJANGO_CSP_ALLOW_UNSAFE_INLINE`. Configuration de `CSP_INCLUDE_NONCE_IN = ('script-src',)` via `django-csp` pour autoriser les nonces sécurisés par requête. Suite de tests unitaires dédiée ajoutée (`tests/api/test_csp_security.py`).

- [x] **Infra — Dockerfiles : toolchain dans le runtime Brain, web sans HEALTHCHECK, Dataflow sur `:latest` — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** :
    - `deploy/Dockerfile.brain` : Ajout d'un stage builder dédié `brain-builder` (compilation Wheels & venv) pour exclure `build-essential` et `gcc` du stage final de runtime.
    - `deploy/Dockerfile` : Ajout de la consigne `HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -fs http://127.0.0.1:7860/health || exit 1`.
    - `deploy/Dockerfile.dataflow` : Remplacement du tag flottant `:latest` sur `dataflow-templates-base/python3-template-launcher-base` par son digest SHA256 immuable `@sha256:d84f2b1d3d666d3a8a30689b2fb1e36780c108c49e1eefbfd6796c9c6ec543ab`.

- [x] **CI — durcissement (timeouts, permissions, SHA pinning, concurrency) — fait (2026-07-23)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-23)** :
    - `timeout-minutes` configuré sur les 11 jobs de CI (`ci.yml`, `deploy_to_hf.yml`, `load-test.yml`, `security_audit.yml`).
    - `permissions: { contents: read }` configuré au niveau racine de chaque workflow GitHub Actions.
    - Blocs `concurrency` ajoutés sur `deploy_to_hf.yml`, `load-test.yml` et `security_audit.yml`.
    - Épinglage par SHA immuables de toutes les GitHub Actions (checkout, setup-python, setup-node, cache, upload-artifact, codecov, gcloud, auth, hadolint, setup-k6).

- [x] **Frontend — 10 modales sans sémantique `dialog` ni focus-trap — fait (2026-07-24)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-24)** : Création d'un composant partagé accessible `<Modal>` (`frontend/src/components/ui/Modal.tsx`) respectant WCAG (`role="dialog"`, `aria-modal="true"`, piège à focus keyboard `Tab`/`Shift+Tab`, écouteur `Escape`, verrouillage du scroll `body` et animations backdrop framer-motion). Suite de tests unitaires dédiée `Modal.test.tsx` (5/5 passés). Refactorisation des modales overlays (`LabListOverlay`, `ToTNodeInspectionModal`, `UniverseDetailPanel`, `ClubDiscoveryPage`, `ClubDashboard`, `TrackerSyncPanel`).

- [ ] **Frontend — couche service incohérente + `types/index.ts` monolithique** _(audit dette 2026-07-22)_
  - Preuve : 70 pages appellent `apiClient('/api/v1/…')` avec l'URL inline vs 25 modules `*Service.ts` (un changement d'endpoint touche N pages) ; `types/index.ts` 703 l. / 88 déclarations (point de couplage/merge-conflict).
  - Fix : router les accès via des services par feature ; éclater les types par domaine (`types/media.ts`, `types/games.ts`…).

- [ ] **Deps — Tailwind un major de retard (v3 → v4)** _(audit dette 2026-07-22)_
  - Preuve : `frontend/package.json:92` `tailwindcss ^3.4.19` — migration de config/moteur non triviale à planifier.

- [x] **Backend — `InferencePort` obèse (violation ISP) — fait (2026-07-23)** _(audit dette 2026-07-19)_
  - **Fait (2026-07-23)** : Segmentation de l'interface monolithic `InferencePort` en 4 ports spécialisés par modalité (`TextInferencePort`, `VisionInferencePort`, `AudioInferencePort`, `Spatial3DInferencePort`). Héritage multiple composite maintenu sur `InferencePort` garantissant une rétro-compatibilité à 100 % pour les adaptateurs et conteneurs d'injection existants. Organisation des délégations par domaine dans `fallback_adapter.py`. Suite complète de tests validée (`1635 passed`).

- [x] **Frontend — pages > 500 lignes (8/8 faits : ProfilePage 506→110 +test, TreeOfThoughtsPage 509→198 +test, PowerStationPage 523→175 +test, SeiyuuDiscoveryPage 531→240 +test, ClusterHealthPanel 616→154 +test, VsBattlePage 647→207 +test, ClassicGamePage 603→370, LoreWorldMapPage 604→385, cf. HISTORY 2026-07-21)** _(audit dette 2026-07-19)_
  - Reste (mesuré 2026-07-21) : **0 pages > 500 lignes**. Toutes les pages volumineuses ont été décomposées en sous-composants réutilisables avec tests de caractérisation.
  - Aussi : ratcheter les seuils vitest (`vite.config.ts:149-154`, 38 % stmts) au fil des tests ajoutés.


## 🟢 Faibles

- [x] **Vrac audit 2026-07-22 (traitable en une passe) — fait (2026-07-24)** _(audit dette 2026-07-22)_
  - **Fait (2026-07-24)** : test placebo `assert True` remplacé par assertions réelles (`test_distillation_pipeline.py`) ; `tests/e2e/` vide supprimé ; `if: always()` ajouté au check OpenAPI (`ci.yml`) ; tests `date.today()` patchés via `FakeDate` subclass (`test_ranking_service.py`, `test_sync.py`) ; `LLM_API_BASE` ajouté à `.env.example` ; `scripts/README.md` corrigé (arbo `root/` → scripts au root + `data/`) ; `.gitignore` dédupliqué (6 doublons) ; triggers `deploy_to_hf.yml` étendus (`requirements-web.txt`/`requirements-brain.txt`) ; `plotly.js` déplacé de devDependencies vers dependencies ; `ollama` pinné à `0.5.13` dans `docker-compose.yml` ; wrapper typé `LazyForceGraph2D.tsx` éliminant 13 `any` + 5 `eslint-disable` dans 5 fichiers ; `role="presentation"` retiré des `<img>` content dans `TraditionalMode.tsx`/`WebtoonMode.tsx` ; composant `<Modal>` accessible réutilisable (WCAG 2.1 AA, `role="dialog"`, `aria-modal="true"`, focus trap, `Escape`, scroll lock) + tests + refactor des 6 modales applicatives ; routes API Multiverse enregistrées dans `ai_ml_urls.py` (15/15 tests Multiverse verts) et `test_media_characters.py` ajusté ; `knip` ajouté en CI pour dead code frontend.

- [x] **Vrac audit 2026-07-19 (traitable en une passe)** _(audit dette 2026-07-19)_
  - Backend : `except Exception: pass` muets dans `core/utils/json_utils.py:67` et `dpo_feedback_loop.py:22` loggés en debug ; `AdEventLoggingAPIView` protégé par `BurstAnonRateThrottle` ; `creators_db.py`/`french_market_db.py` externalisés sous `data/mlops/*.json`.
  - Frontend : `cream-50` (`#fffcf0`) et `navy-950` (`#0f0f1a`) intégrés aux tokens palette ; `getAgentColorCode` nettoyé avec dictionnaire de correspondance dans `ExpertNexusPage.tsx` ; `react-force-graph-2d` chargé en `lazy` + `Suspense` dans les 4 modules ; `aria-label` ajoutés aux boutons d'action ; `useEffect` réalignés avec leurs dépendances réelles (`AkinetixPage.tsx`) ; état dérivé `visualResults` directement calculé (`UniversalSearchHubPage.tsx`).
  - Deps/CI : `pytest-cov>=6.0.0` aligné avec pytest 9 ; `cache: 'pip'` ajouté à `security_audit.yml` ; mypy `--no-site-packages` aligné entre pre-commit et CI ; commentaire Beam réaligné sur 2.75.0 dans `requirements-dataflow.in` ; `bitsandbytes` supprimé du lock web ; `plotly.js`/`react-plotly.js` isoblocs.

- [x] **Brain — intégration Moshi (S2S local) : réécrite en cascade Kyutai STT + XTTS**
  - Remplacé le `from moshi.models import Moshi` fantôme par une cascade
    Kyutai STT (transformers, kyutai/stt-1b-en_fr-trfs) → LLM brain → XTTS-v2 (FR).
    Le paquet `moshi` a été écarté (il plafonne safetensors<0.8.0, incompatible avec
    diffusers==0.39.0) ; aucune nouvelle dépendance (transformers + coqui-tts déjà
    verrouillés). Contrat batch `speech_to_speech` inchangé ; Gemini Live intact.
    Implémentation dans [audio_mixin.py](backend/adapters/inference/audio_mixin.py)
    (`_load_stt`/`_transcribe`/`_synthesize`/`speech_to_speech`).
    Reste : rebuild/redeploy manuel de l'image brain (poids STT téléchargés au 1er
    appel), puis smoke test GPU (`S2S_GPU_SMOKE=1 pytest -m gpu`).
