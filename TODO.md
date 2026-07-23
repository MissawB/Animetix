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

- [ ] **CI — aucun garde-fou de dérive des migrations Django (quick win)** _(audit dette 2026-07-22)_
  - Preuve : zéro `makemigrations --check` dans CI/pre-commit/tests ; le seul `migrate` est au démarrage du conteneur (`deploy/supervisord.conf:9`) — un modèle modifié sans migration n'est détecté qu'au cold-start en prod.
  - Fix : étape CI (ou test dédié type `test_coverage_gate.py`) exécutant `makemigrations --check --dry-run`.

- [ ] **Frontend — régression du plafond « 0 pages > 500 lignes » + garde-fou manquant (quick win pour le lint)** _(audit dette 2026-07-22)_
  - Preuve : `pages/games/CovertestPage.tsx` **694 l.** (plus gros fichier du repo ; FX inline extractibles l.35-70) et `pages/games/ClassicLobbyPage.tsx` **519 l.** — l'acquis des PR 93-96 n'est pas protégé.
  - Fix : re-décomposer les 2 pages + règle eslint `max-lines` pour empêcher la re-croissance.

- [ ] **Frontend — data-fetching manuel contournant react-query** _(audit dette 2026-07-22)_
  - Preuve : 35 pages sur `useQuery`, mais triptyque `useState(loading/error/data)`+`useEffect` refait à la main dans `FinancialDashboardPage.tsx:37-61`, `AkinetixRLPage.tsx:21-59` (`catch {}` qui avale l'erreur), `OfflineSyncPage.tsx:36-110` ; POST manuels dans `MangaLabPage.tsx:43-86` et `PricingPage.tsx:45-83` au lieu de `useMutation`.
  - Fix : migrer ces 5 pages vers `useQuery`/`useMutation` comme le reste.

- [ ] **Frontend — 7 pages > 350 lignes sans aucun test (prérequis au ratchet vitest)** _(audit dette 2026-07-22)_
  - Preuve : `ExpertNexusPage` (467), `ArchetypeNexusPage` (447), `ForgePage` (435), `ClubDashboard` (421), `StrategyLabPage` (402), `LatentSpacePage` (378), `AccountSettingsPage` (355) — aucun `__tests__/<Page>.test.tsx`.
  - Fix : au minimum un test de rendu + états loading/error par page, puis ratcheter `vite.config.ts:149-154`.

## 🟡 Moyens

- [ ] **Backend — `brain_service.py` : 28 handlers d'erreur identiques qui fuitent `str(e)`** _(audit dette 2026-07-22)_
  - Preuve : 28 occurrences de `except Exception as e: raise HTTPException(status_code=500, detail=str(e))` (l.295-579) — duplication copier-coller + message d'exception interne renvoyé au client (atténué : service interne derrière `verify_api_key`).
  - Fix : un `@app.exception_handler(Exception)` unique (message générique + log serveur).

- [ ] **Backend — adaptateur Google GenAI : sentinelles neutres qui masquent les pannes** _(audit dette 2026-07-22)_
  - Preuve : `google_genai_adapter.py:156-158` (`return 0.0`), `:172-174` (`return []` — un embedding vide peut être persisté), `:501-503`, `:569-571`, `:586-588` — l'erreur est loggée mais l'aval est corrompu silencieusement (distance 0.0 fausse un ranking).
  - Fix : `raise InferenceError` comme le fait déjà `generate`, au lieu de retourner un défaut neutre.

- [ ] **Backend — N+1 résiduel `likes.count` + `fields="__all__"` sur serializers publics** _(audit dette 2026-07-22)_
  - Preuve : `serializers.py:384` `source="likes.count"` émet 1 COUNT/ligne et **ignore** le `prefetch_related("likes")` de `vs_battle.py:25-31` (seul `len(obj.likes.all())` utilise le cache) ; `fields = "__all__"` sur CreativeFusion/VsBattle/AISafetyEvent (`serializers.py:354/389/416`) → tout futur champ auto-exposé.
  - Fix : annoter `Count("likes")` dans les querysets + whitelist explicite des champs.

- [ ] **Backend — god modules + typage du cœur lacunaire** _(audit dette 2026-07-22)_
  - Preuve : `models.py` 1005 l., `urls/api.py` 831 l., `serializers.py` 714 l. (imports répétés en milieu de fichier l.321/379/403) ; ~30 % des fonctions de `core/domain/services/**` sans annotation de retour, 183 usages de `Any`.
  - Fix : éclater par domaine (`models/social.py`, `serializers/manga.py`…) ; compléter les annotations en priorité sur ports/services.

- [ ] **Infra — CSP `'unsafe-inline'` dans `script-src` même en prod** _(audit dette 2026-07-22)_
  - Preuve : `settings.py:569-577` — seul `'unsafe-eval'` est retiré en prod ; les scripts inline restent autorisés, neutralisant largement la protection XSS de la CSP.
  - Fix : nonces/hashes et retrait de `'unsafe-inline'` de `script-src` quand `IS_PRODUCTION`.

- [ ] **Infra — Dockerfiles : toolchain dans le runtime Brain, web sans HEALTHCHECK, Dataflow sur `:latest`** _(audit dette 2026-07-22)_
  - Preuve : `Dockerfile.brain:101-111` installe `build-essential`/`gcc` dans le stage **final** (pas de builder séparé, contrairement au web `Dockerfile:28-55`) ; `deploy/Dockerfile` sans `HEALTHCHECK` (le brain en a un l.181-182) ; `Dockerfile.dataflow:7` sur tag flottant `:latest` (le commentaire l.1-6 reconnaît le problème).
  - Fix : stage builder pour le brain ; `HEALTHCHECK CMD curl -fs http://127.0.0.1:7860/health` sur le web ; pin `@sha256:` pour dataflow.

- [ ] **CI — durcissement (timeouts, permissions, SHA pinning, concurrency)** _(audit dette 2026-07-22)_
  - Preuve : 11 jobs sans `timeout-minutes` (défaut GitHub 6 h) ; aucun bloc `permissions:` au niveau workflow (`GITHUB_TOKEN` hérite d'un scope potentiellement read-write) ; actions en tag mutable (`codecov@v5` ci.yml:152/381, `google-github-actions/auth@v2` ci.yml:454/566…) alors que le job deploy a `id-token: write` + accès GCP WIF ; `deploy_to_hf.yml` sans `concurrency` (deux pushes rapprochés = deux déploiements HF concurrents).
  - Fix : `timeout-minutes` partout, `permissions: {contents: read}` en tête de workflow, pin par SHA (dependabot github-actions suit), bloc `concurrency` sur deploy_to_hf/security_audit.

- [ ] **Frontend — 10 modales sans sémantique `dialog` ni focus-trap** _(audit dette 2026-07-22)_
  - Preuve : 10 overlays `fixed inset-0`, 0 avec `role="dialog"`/`aria-modal`, aucun piège/restauration de focus ni Escape (ex. `SponsorStreamModal.tsx`, `ToTNodeInspectionModal.tsx`, `LabListOverlay.tsx`) — seuls les boutons de fermeture ont des `aria-label`.
  - Fix : composant `<Modal>` partagé (dialog + aria-modal + focus-trap + Escape) adopté partout.

- [ ] **Frontend — couche service incohérente + `types/index.ts` monolithique** _(audit dette 2026-07-22)_
  - Preuve : 70 pages appellent `apiClient('/api/v1/…')` avec l'URL inline vs 25 modules `*Service.ts` (un changement d'endpoint touche N pages) ; `types/index.ts` 703 l. / 88 déclarations (point de couplage/merge-conflict).
  - Fix : router les accès via des services par feature ; éclater les types par domaine (`types/media.ts`, `types/games.ts`…).

- [ ] **Deps — Tailwind un major de retard (v3 → v4)** _(audit dette 2026-07-22)_
  - Preuve : `frontend/package.json:92` `tailwindcss ^3.4.19` — migration de config/moteur non triviale à planifier.

- [ ] **Backend — `InferencePort` obèse (violation ISP)** _(audit dette 2026-07-19)_
  - Preuve : `fallback_adapter.py` (833 l.) contient ~30 méthodes de pure délégation `return self._fallback_call(...)` (l.~509-785) — chaque adapter doit couvrir toute la surface du port.
  - Fix : segmenter en ports fins (texte / vision / audio / 3D).

- [x] **Frontend — pages > 500 lignes (8/8 faits : ProfilePage 506→110 +test, TreeOfThoughtsPage 509→198 +test, PowerStationPage 523→175 +test, SeiyuuDiscoveryPage 531→240 +test, ClusterHealthPanel 616→154 +test, VsBattlePage 647→207 +test, ClassicGamePage 603→370, LoreWorldMapPage 604→385, cf. HISTORY 2026-07-21)** _(audit dette 2026-07-19)_
  - Reste (mesuré 2026-07-21) : **0 pages > 500 lignes**. Toutes les pages volumineuses ont été décomposées en sous-composants réutilisables avec tests de caractérisation.
  - Aussi : ratcheter les seuils vitest (`vite.config.ts:149-154`, 38 % stmts) au fil des tests ajoutés.


## 🟢 Faibles

- [ ] **Vrac audit 2026-07-22 (traitable en une passe)** _(audit dette 2026-07-22)_
  - Tests/CI : test placebo `assert True` (`test_distillation_pipeline.py:56-57`) ; `tests/e2e/` vide (que du `__pycache__`) ; check OpenAPI sauté quand pytest échoue (pas de `if: always()`, `ci.yml:157`) ; tests couplés à `date.today()` (`test_ranking_service.py:20/40/51`, `test_sync.py:80/110` — flake potentiel à minuit, freezegun/clock injecté).
  - Config/docs : `LLM_API_BASE` lue par le code mais absente de `.env.example` ; `scripts/README.md:8-24` décrit une arbo `scripts/root/` inexistante ; `.gitignore` avec 6 entrées dupliquées ; `deploy_to_hf.yml:9-15` ne se déclenche pas sur `requirements-web.txt`/`requirements-brain.txt` ; `plotly.js` en devDependencies alors que `react-plotly.js` (runtime) le requiert ; `ollama/ollama:latest` en compose (`docker-compose.yml:60`) vs 0.5.13 pinné côté brain.
  - Frontend : 13 `any` résiduels (quasi tous le cast `ForceGraph2D` non typé — un wrapper typé unique réglerait tout) ; `alt` + `role="presentation"` contradictoires dans le manga reader (`TraditionalMode.tsx`, `WebtoonMode.tsx`) ; un barrel `export *` (`features/manga-reader/index.ts:1`).
  - Outillage : aucun détecteur de dead code frontend — ajouter `knip` ou `ts-prune` en CI plutôt qu'une chasse manuelle sur 121 pages.

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
