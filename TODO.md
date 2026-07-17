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

- [/] **Index visuel : phase 2 — peuplement `character_ccip_space` partiel, BLOQUÉ par la facturation GCP coupée** _(phase 1 livrée 2026-07-14 ; run tenté 2026-07-17)_
  - **Fait** : job Cloud Run `animetix-build-character-index` **créé** (config scopée) ; smoke test OK (48/50, Brain CCIP ~0,3 s/portrait) ; run complet lancé (`…-lznfm`) → **~3,5 h de vecteurs écrits (09:40→13:15) préservés** (reprenable). Décision « tour texte CLIP non exposée » tranchée (cf. HISTORY) — ne pas rebrancher `encode_text`.
  - **🔴 BLOQUEUR (2026-07-17 ~13:15)** : **la facturation GCP du projet `animetix` a été désactivée en plein run** (log Brain : « billing is disabled for this project ») → Brain L4 tombé (`/health` = 500), job échoué à 14:46. **Cause probable** : plafond de budget franchi par le run GPU de 3,5 h. **Impact** : Brain + Cloud Run Jobs + déploiement prod tous bloqués.
  - **Reste (après rétablissement facturation)** : 1) **rouvrir la facturation** sur `animetix` (Console GCP → Billing ; vérifier/relever le plafond) — action opérateur, pas CLI ; 2) confirmer Brain `/health` = 200 ; 3) **re-exécuter par chunks** (`--limit N` plutôt qu'un run de 6 h) jusqu'aux ~35 000 ; 4) vérifier que la recherche perso ne renvoie plus 503.

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
- [x] **CI — Windows testé (job `Run Unit Tests (Windows)`, PR #88 mergée)** _(audit dette 2026-07-11 ; résolu 2026-07-17)_
  - **Fait 2026-07-17 (PR #88 mergée)** : job séparé `Run Unit Tests (Windows)` sur `windows-latest`, **suite complète verte** (~33 min), bloquant (`continue-on-error` retiré). Sans services Linux (SQLite + LocMemCache, `test_settings`), sans gate couverture (reste sur la leg Linux) ; le check `Run Unit Tests` reste inchangé. L'angle mort win32 du conftest est désormais couvert à chaque PR/push.
  - **N/A** : « ajouter aux required checks » sans objet — `main` n'a **pas de branch protection** (le job montre un rouge honnête en cas d'échec ; créer une branch protection = choix infra séparé). _(à archiver dans HISTORY.md)_
- [ ] **Frontend — composants > 500 lignes (reliquat)** _(audit dette 2026-07-11 ; BlindtestPage découpé le 2026-07-16, cf. HISTORY)_
  - `BlindtestPage` traité (753→324, hook + sous-composants). Restent, à découper au fil de l'eau (sous-composants + hooks métier) : `TransparencyPage` (614), `AudioLabPage` (573), `LabHubPage` (569), `SpeechToSpeechLabPage` (544).
- [ ] **Deps — registre de prix désynchronisé (reliquat)** _(audit dette 2026-07-11 ; lock-doublons + COST_AUDIT réglés 2026-07-17)_
  - **Fait 2026-07-17** : lock backend vérifié — aiohttp/httpx/requests/ujson sont **tous transitifs** (via fsspec / datasets+diffusers / apache-beam+colpali / autobahn ; aucun dans [requirements.in](requirements.in)), donc **rien à dédupliquer** ; seul `orjson` est direct (légitime). [docs/COST_AUDIT.md](docs/COST_AUDIT.md) rafraîchi sur la vraie chaîne (Gemini 3.5 Flash + Qwen3.5 + brain-api ; chemin `deploy_brain.py` corrigé).
  - **Reste** : [`PricingService`](backend/core/domain/services/pricing_service.py) est désynchronisé — il tarifie `gpt-4o`/`gpt-3.5-turbo`/`claude-3-sonnet` (jamais appelés par la chaîne prod `[brain_api, google_genai]`) et n'a **aucune entrée `gemini-*`**, donc chaque appel Gemini live retombe sur le fallback `0.0` (facturé gratuit → attribution Bx fausse). Ajouter `gemini-3.5-flash` / `gemini-live-2.5-flash-native-audio` au registre + retirer les lignes OpenAI/Anthropic mortes.
