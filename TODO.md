# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [/] **Fine-tune otaku — dataset assaini ✅ ; reste le réentraînement (bloqué GPU)** _(expérience contrôlée 2026-07-13 ; dataset refait 2026-07-17)_
  - **Contexte** : l'adaptateur servi produisait du texte corrompu (chiffres injectés, persos inventés) car il avait mémorisé le **gabarit** synthétique/templaté de `MissawB/otaku-expert-dataset` et **remplissait les emplacements numériques au hasard** — la forme d'une réponse, pas son contenu.
  - **✅ Fait 2026-07-17 (PR #87 mergée)** : dataset assaini de façon déterministe — générateurs réécrits pour **ancrer** les réponses dans les vrais `description`/`biography` (EN synopsis, FR structuré), **slots numériques purgés**, bug des sorties byte-identiques supprimé, suite de garde-fous `tests/mlops/test_dataset_sanitation.py`. Régénéré (39 392 lignes), validé propre, **re-uploadé sur `MissawB/otaku-expert-dataset`**. Spec/plan : `docs/specs|plans/2026-07-17-otaku-dataset-sanitation-*`.
  - **Reste** : réentraîner sur ce dataset propre **dès qu'un GPU est dispo** (cf. dette GPU), puis re-servir via `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké dans l'image, aucun rebuild).

- [ ] **Index visuel : phase 2 — peupler `character_ccip_space` (~35 000 portraits)** _(phase 1 livrée 2026-07-14 ; chaîne CCIP dé-risquée 2026-07-16, cf. HISTORY)_
  - `character_ccip_space` est **vide** (recherche perso → 503 honnête, sans facturer) ; la chaîne est dé-risquée (test d'intégration réel) et **le build est câblé en Cloud Run Job on-demand** `animetix-build-character-index` (cf. HISTORY). **Reste = geste opérateur** : `deploy_jobs.py` (crée/maj le job) puis `gcloud run jobs execute animetix-build-character-index --region=europe-west9`, Brain up ; reprenable, re-exécuter jusqu'à couvrir les ~35 000. Décision « tour texte CLIP non exposée » déjà tranchée (cf. HISTORY) — ne pas rebrancher `encode_text`.

- [x] **URI Neo4j locale morte — geste de config** _(constaté 2026-07-12 ; résolu 2026-07-17)_
  - **Fait 2026-07-17** : conteneur Docker `animetix-neo4j` (neo4j:5, `--restart unless-stopped`, ports 7687/7474) + root `.env` re-pointé sur `bolt://localhost:7687` (bloc Aura mort `a654e145` conservé en commentaire). Connexion vérifiée au niveau app (`neo4j_manager.driver` actif, requête test OK → le skip de `reconcile_db` ne se déclenche plus). Graphe vide : peupler via `python manage.py sync_catalog` au besoin. _(à archiver dans HISTORY.md)_

## 🟡 Moyens

- [ ] **Tests — hygiène : reliquat (2 gardes porteuses)** _(audit dette 2026-07-11 ; api_client/mock_engine/mock_prompt_manager centralisés 2026-07-16, cf. HISTORY)_
  - Fixtures dupliquées : **fait**. Mock fuyant : **fait** (`tests/core/test_diffusers_adapter.py` passe en `monkeypatch.setitem`, cf. HISTORY). Restent **deux retraits de gardes, dangereux et non-autonomes** : (1) le snapshot `sys.modules` autouse ([conftest:107-139](tests/conftest.py#L107-L139)) — le retirer expose des pollutions **dépendantes de l'ordre des tests** (flaky : une passe CE verte ne prouve PAS que c'est sûr) ; auditer TOUS les remplacements de modules d'abord. (2) le `BRAIN_API_URL` forcé à l'import ([conftest:12](tests/conftest.py#L12)) — exige de rendre la construction DI paresseuse (`containers/inference.py` `validate_inference_config` sur `django.setup()`), refactor large touchant toute la chaîne d'inférence. À faire dans une passe dédiée avec runs CI en ordre randomisé, pas en slice.

## 🟢 Faibles

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
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
- [ ] **Frontend — plotly.js (~4,6 Mo) importé statiquement dans 8 pages** _(audit dette 2026-07-11)_
  - [AIUsagePage.tsx:18](frontend/src/pages/auth/AIUsagePage.tsx#L18), `LatentSpacePage`, `LiquidNeuralNetworkLabPage`, `StrategyLabPage`, `SeichijunreiMapPage`, `ArchetypeNexusPage`, `TransparencyPage`… Le chunk est isolé (`plotly-vendor`, [vite.config.ts:98](frontend/vite.config.ts#L98)) mais chaque visite télécharge 4,6 Mo — `AIUsagePage` n'affiche qu'un historique simple. + three.js dans 5 fichiers. **Reco** : lazy-import interne ou lib légère pour les graphes simples ; auditer via `stats.html` déjà généré.
- [ ] **CI — mono-cible : Windows jamais testé** _(audit dette 2026-07-11)_
  - Un seul `ubuntu-latest` / Python 3.12, aucune matrix — alors que toute la logique anti-pollution async du conftest cible Windows ([tests/conftest.py:14-18](tests/conftest.py#L14-L18)). Angle mort jamais couvert → ajouter `windows-latest` à la matrice de tests dans le workflow GitHub Actions (`.github/workflows/ci.yml`).
- [ ] **Frontend — composants > 500 lignes (reliquat)** _(audit dette 2026-07-11 ; BlindtestPage découpé le 2026-07-16, cf. HISTORY)_
  - `BlindtestPage` traité (753→324, hook + sous-composants). Restent, à découper au fil de l'eau (sous-composants + hooks métier) : `TransparencyPage` (614), `AudioLabPage` (573), `LabHubPage` (569), `SpeechToSpeechLabPage` (544).
- [x] **Deps — doublons + registre de prix : réglés** _(audit dette 2026-07-11 ; réglé 2026-07-17)_ _(à archiver dans HISTORY.md)_
  - Lock backend vérifié : aiohttp/httpx/requests/ujson sont **tous transitifs** (via fsspec / datasets+diffusers / apache-beam+colpali / autobahn ; aucun dans [requirements.in](requirements.in)) → **rien à dédupliquer** ; seul `orjson` est direct (légitime). [docs/COST_AUDIT.md](docs/COST_AUDIT.md) rafraîchi sur la vraie chaîne (Gemini 3.5 Flash + Qwen3.5 + brain-api ; chemin `deploy_brain.py` corrigé).
  - [`PricingService`](backend/core/domain/services/pricing_service.py) résynchronisé : entrées `gemini-3.5-flash` / `gemini-live-2.5-flash-native-audio` / `gemini-embedding-2` ajoutées, lignes mortes `gpt-4o`/`gpt-3.5-turbo`/`claude-3-sonnet` retirées, et `_resolve_pricing` tolère les engines namespacés (`google_genai:<model>[:vision]`) → les appels Gemini ne retombent plus sur le fallback `0.0`. NB : `cost_estimate` est de l'**analytics USD**, pas la facturation Bx (`berrix_economy.py`).
- [ ] **Backend — DI contourné et double voie Neo4j** _(audit dette 2026-07-11)_
  - [dependencies.py:14-19](backend/api/animetix/api/dependencies.py#L14-L19) résout via l'instance globale du container (work-around coverage documenté) au lieu de `@inject/Provide`. Les scripts pipeline instancient `Neo4jClient` directement ([neo4j_client.py:55](backend/pipeline/neo4j_client.py#L55), [neo4j_sync.py:29](backend/pipeline/neo4j_sync.py#L29)) hors container → deux voies d'accès Neo4j.
