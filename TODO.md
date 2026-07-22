# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.
> Les entrées marquées _(audit dette 2026-07-19)_ sont issues d'une seconde passe multi-agents (mêmes 4 axes) — preuves fichier:ligne vérifiées à l'écriture. Vérifié sain au passage : pas d'injection SQL (tout paramétré), settings durcis, aucun test skippé/xfail, aucun artefact lourd versionné hors LFS, throttle akinetix classic OK (`CpuGameThrottle` présent).

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ (PR #87) ; reste le réentraînement (bloqué GPU)** _(2026-07-13→17 ; détail cf. HISTORY 2026-07-17)_
  - **Reste** : réentraîner sur le dataset propre (`MissawB/otaku-expert-dataset`) **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké, aucun rebuild).

- [/] **Index visuel : phase 2 — `character_ccip_space` partiel, BLOQUÉ par la facturation GCP coupée** _(phase 1 2026-07-14 ; run tenté 2026-07-17, cf. HISTORY)_
  - **🔴 BLOQUEUR** : la facturation GCP du projet `animetix` a été **désactivée en plein run** (~13:15 ; log Brain « billing is disabled for this project »), Brain L4 tombé → job échoué après **~3,5 h de vecteurs écrits (préservés, reprenable)**. Cause probable : plafond de budget franchi par le run GPU. Impact : Brain + Cloud Run Jobs + prod bloqués.
  - **Reste (après rétablissement facturation, action console)** : 1) rouvrir la facturation sur `animetix` (vérifier/relever le plafond) ; 2) Brain `/health` = 200 ; 3) re-exécuter **par chunks** (`--limit N`) jusqu'aux ~35 000 ; 4) recherche perso ne renvoie plus 503.

## 🟡 Moyens

- [ ] **Backend — `InferencePort` obèse (violation ISP)** _(audit dette 2026-07-19)_
  - Preuve : `fallback_adapter.py` (833 l.) contient ~30 méthodes de pure délégation `return self._fallback_call(...)` (l.~509-785) — chaque adapter doit couvrir toute la surface du port.
  - Fix : segmenter en ports fins (texte / vision / audio / 3D).

- [x] **Frontend — pages > 500 lignes (8/8 faits : ProfilePage 506→110 +test, TreeOfThoughtsPage 509→198 +test, PowerStationPage 523→175 +test, SeiyuuDiscoveryPage 531→240 +test, ClusterHealthPanel 616→154 +test, VsBattlePage 647→207 +test, ClassicGamePage 603→370, LoreWorldMapPage 604→385, cf. HISTORY 2026-07-21)** _(audit dette 2026-07-19)_
  - Reste (mesuré 2026-07-21) : **0 pages > 500 lignes**. Toutes les pages volumineuses ont été décomposées en sous-composants réutilisables avec tests de caractérisation.
  - Aussi : ratcheter les seuils vitest (`vite.config.ts:149-154`, 38 % stmts) au fil des tests ajoutés.


## 🟢 Faibles

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
