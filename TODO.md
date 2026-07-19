# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.
> Les entrées marquées _(audit dette 2026-07-19)_ sont issues d'une seconde passe multi-agents (mêmes 4 axes) — preuves fichier:ligne vérifiées à l'écriture. Vérifié sain au passage : pas d'injection SQL (tout paramétré), settings durcis, aucun test skippé/xfail, aucun artefact lourd versionné hors LFS, throttle akinetix classic OK (`CpuGameThrottle` présent).

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [ ] **Secrets — clés Stripe mortes dans `.env` à révoquer** _(audit dette 2026-07-19)_
  - Preuve : `STRIPE_PUBLISHABLE_KEY`/`STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` encore présentes alors que le stack Stripe a été supprimé le 2026-07-07 (ROADMAP). Même famille que TRIPO/MAPBOX (révocation externe).
  - Fix : révoquer côté dashboard Stripe, puis retirer les 3 clés du `.env`.

- [ ] **Config — `.env.example` désynchronisé (~18 clés réelles absentes)** _(audit dette 2026-07-19)_
  - Preuve : `GEMINI_API_KEY`, `OPENAI_API_KEY`, `COHERE_API_KEY`, `TAVILY_API_KEY`, `TMDB_API_KEY`, `IGDB_CLIENT_ID/SECRET`, `HF_TOKEN`, `WANDB_API_KEY`, `NEO4J_USERNAME/DATABASE`… manquantes de l'exemple → onboarding/repro cassés.
  - Fix : régénérer `.env.example` à partir des noms de clés réellement lus par settings/adapters (noms uniquement, pas de valeurs).

- [ ] **Train — `deploy/Dockerfile.train` non reproductible (bloquant avant le réentraînement otaku)** _(audit dette 2026-07-19)_
  - Preuve : base `pytorch/pytorch:2.5.1-...` sans digest (`Dockerfile.train:11`) + deps flottantes `trl>=0.12.0`, `transformers>=4.57.0`, `peft>=0.7.0` (`:17-25`) alors que le service pinne `trl==0.12.1`, `transformers==4.57.6`, `peft==0.17.1` → LoRA entraîné sur des versions jamais testées en prod.
  - Fix : installer via un lock dédié (ou `-c requirements.txt`) + épingler la base par digest.

- [ ] **CI — action tierce `jlumbroso/free-disk-space@main` non épinglée (supply-chain)** _(audit dette 2026-07-19)_
  - Preuve : `@main` mutable dans 6 jobs (`ci.yml:36,68,94,208,287` + `security_audit.yml:22`) → un push amont modifie silencieusement la CI.
  - Fix : épingler sur tag ou SHA de commit.

- [ ] **CI — gate de couverture désaligné pre-push (75) vs CI (76)** _(audit dette 2026-07-19)_
  - Preuve : `.pre-commit-config.yaml:52` `--cov-fail-under=75` vs `ci.yml:143` + `pyproject.toml:77` à 76 → pre-push vert, CI rouge.
  - Fix : aligner le hook sur 76 (« kept in lockstep » du pyproject).

- [ ] **Frontend — contenu de démo Google câblé dans le flux sponsor (facturation)** _(audit dette 2026-07-19)_
  - Preuve : `frontend/src/features/billing/components/SponsorStreamModal.tsx:13-23` — vidéos `gtv-videos-bucket/sample/` + `AD_TAG_URL` d'exemple DoubleClick (`single_ad_samples`) servis tels quels.
  - Fix : externaliser en config/env avec de vrais créatifs, ou masquer le composant tant qu'aucun sponsor réel.

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, BLOQUÉ par la facturation GCP coupée** _(phase 1 2026-07-14 ; run tenté 2026-07-17, cf. HISTORY)_
  - **🔴 BLOQUEUR** : la facturation GCP du projet `animetix` a été **désactivée en plein run** (~13:15 ; log Brain « billing is disabled for this project »), Brain L4 tombé → job échoué après **~3,5 h de vecteurs écrits (préservés, reprenable)**. Cause probable : plafond de budget franchi par le run GPU. Impact : Brain + Cloud Run Jobs + prod bloqués.
  - **Reste (après rétablissement facturation, action console)** : 1) rouvrir la facturation sur `animetix` (vérifier/relever le plafond) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

## 🟡 Moyens

- [ ] **Backend — god-files du pipeline MLOps, sans aucun test dédié** _(audit dette 2026-07-19)_
  - Preuve : `dpo_dataset_compiler.py` (1086 l.), `ft_dataset/synthetic_generators.py` (917), `dialogue_generators.py` (716), `finetuning_dataset.py` (871), `creators_db.py` (600) — 0 fichier de test correspondant ; angle mort masqué par le 76 % global. Idem cœur Django : `models.py` (1005), `presenters.py` (857), `serializers.py` (707).
  - Fix : découper par responsabilité (génération vs compilation vs I/O) + tests ciblés ; scinder `models.py` en package par domaine.

- [ ] **Backend — `InferencePort` obèse (violation ISP)** _(audit dette 2026-07-19)_
  - Preuve : `fallback_adapter.py` (833 l.) contient ~30 méthodes de pure délégation `return self._fallback_call(...)` (l.~509-785) — chaque adapter doit couvrir toute la surface du port.
  - Fix : segmenter en ports fins (texte / vision / audio / 3D).

- [ ] **Duplication backend + frontend** _(audit dette 2026-07-19)_
  - Backend : `permission_classes = [AllowAny]` + `throttle_classes = [CpuGameThrottle]` répété ~30× dans `api/games/*.py` → classe de base `CpuGameAPIView`. Mapping `MangaCover → dict` copié 3× dans `pgvector_repository_adapter.py:316-400` → `_cover_to_dict()`.
  - Frontend : `norm()` (strip diacritiques) copiée dans 4 fichiers (`VsBattlePage.tsx:27`, `ClassicGamePage.tsx:33`, `CovertestPage.tsx:10`, `useBlindtestGame.ts:13`) → `utils/normalizeText.ts` ; sélecteur de difficulté dupliqué dans 4 lobbies → `<DifficultySelector>` partagé.

- [ ] **Frontend — fetch impératif hors react-query, erreurs avalées** _(audit dette 2026-07-19)_
  - Preuve : `ClusterHealthPanel.tsx:345-382` refait state/loading/`setInterval` à la main alors que `useHealth` + `refetchInterval` existent ; `MangaLibraryPage.tsx:34-38` avale l'échec sans retour utilisateur (`:28`).
  - Fix : migrer vers `useQuery`/`useMutation` + surfacer les erreurs.

- [ ] **Frontend — 8 pages encore > 500 lignes ; `VsBattlePage` (651 l.) sans test** _(audit dette 2026-07-19)_
  - Preuve : `VsBattlePage` (651), `ClassicGamePage` (608), `LoreWorldMapPage` (604), `SeiyuuDiscoveryPage` (531), `PowerStationPage` (523), `TreeOfThoughtsPage` (509), `ProfilePage` (506), `ClusterHealthPanel` (500). Seuils vitest bas (38 % stmts, `vite.config.ts:149-154`), ~114 pages sans test.
  - Fix : poursuivre le découpage (pattern PR #93-96) + test de rendu pour `VsBattlePage`, ratcheter les seuils.

- [ ] **API — `schema.yaml` figé au 2026-07-07, types front potentiellement désynchronisés** _(audit dette 2026-07-19)_
  - Preuve : dernier commit du schéma 2026-07-07 alors que l'API a été décomposée/étendue depuis (HISTORY 2026-07-10, pricing 2026-07-19) ; consommé par `generate:api` (openapi-typescript).
  - Fix : régénérer + ajouter un check CI (drift `spectacular` vs fichier commité).

- [ ] **CI — coût/couverture : job Windows non-bloquant, perf-test facturé, bandit hors PR** _(audit dette 2026-07-19)_
  - Preuve : `test-windows` (~33 min, `ci.yml:154-196`) rejoue toute la suite sans gater les merges ; `perf-test` (`ci.yml:273-321`) appelle Gemini/OpenAI à CHAQUE `workflow_dispatch` (même un simple deploy brain) ; bandit/hadolint ne tournent sur PR que si requirements/lock changent (`security_audit.yml:7-12`).
  - Fix : required-check ou filtrage OS-sensible pour Windows ; input dédié `run_perf` ; déclencher bandit sur les PR touchant `backend/`/`deploy/`.

- [ ] **Deploy — tags `:latest` mutables + `.dockerignore` incomplet** _(audit dette 2026-07-19)_
  - Preuve : `cloudbuild.yaml:4` (`_TAG: latest`) → rollback impossible par tag ; `.dockerignore` n'exclut pas `tests/`, `docs/`, `dev/`, `coverage.xml` (1,2 Mo) alors que `deploy/Dockerfile:80` fait `COPY . .`.
  - Fix : builder/déployer par `:${SHORT_SHA}` ; compléter `.dockerignore` (aligné `.gcloudignore`).

## 🟢 Faibles

- [ ] **Vrac audit 2026-07-19 (traitable en une passe)** _(audit dette 2026-07-19)_
  - Backend : `except Exception: pass` muets dans `core/utils/json_utils.py:67` et `dpo_feedback_loop.py:22` (logger en debug) ; `AdEventLoggingAPIView` (`admin_api.py:116-135`) AllowAny en écriture DB sans throttle dédié ; données métier en dur dans `creators_db.py`/`french_market_db.py` → externaliser en JSON sous `data/`.
  - Frontend : hex en dur contournant les tokens (`bg-[#0f0f1a]` dans 22 fichiers alors que `navy-950` existe ; `#fffcf0` absent de la palette) ; hex Tailwind recopiés à la main (`ExpertNexusPage.tsx:82-96`) ; `react-force-graph-2d` importé statiquement dans 4 modules (lazy local) ; boutons icône sans `aria-label` (`ClusterHealthPanel.tsx:410,455`) ; `useEffect` mount-only avec deps réelles ignorées (`AkinetixPage.tsx:22-31`) ; état dérivé stocké (`UniversalSearchHubPage.tsx:40`).
  - Deps/CI : `pytest-cov==5.0.0` face à pytest 9 ; `setup-python@v4` résiduel (`security_audit.yml:33`) ; `codecov-action@v4` → v5 ; pas de cache pip sur `security_audit.yml:37-40` ; flag mypy divergent hook vs CI (`--no-site-packages`) ; commentaire Beam 2.74 vs pin 2.75 (`requirements-dataflow.in:12`) ; `bitsandbytes` dans le lock web sans import direct (à confirmer puis cantonner à brain) ; retirer `plotly.js`/`react-plotly.js` une fois la migration recharts finie.
  - Cruft : dossier racine `Double_scenario_Project/` (1 seul fichier égaré, le spec vit déjà sous `docs/`) et `node_modules/` racine orphelin → supprimer.

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
