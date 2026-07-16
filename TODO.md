# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [ ] **Fine-tune otaku — l'adaptateur est corrompu, le dataset est à refaire** _(expérience contrôlée 2026-07-13)_
  - `MissawB/otaku-qwen-7b-adapter` mergé dans sa vraie base et servi produit du **texte corrompu** : chiffres injectés au milieu des mots, personnages inventés (« Izanagi Eikichi1 » comme héros de Chainsaw Man). Même image, même quantification, même template : le modèle **stock** répond « Denji » proprement. La chaîne de service est donc saine — **c'est l'adaptateur**.
  - **Cause** : il a mémorisé le **gabarit** de `MissawB/otaku-expert-dataset`, qui est synthétique et templaté (« jouit d'une immense popularité », « figure incontournable », « se plaçant au rang numéro… »), et il **remplit les emplacements numériques au hasard**. Il a appris la forme d'une réponse, pas son contenu.
  - **Écartés** : désalignement du tokenizer (adaptateur et base partagent les mêmes 22 tokens ajoutés) et pollution du dataset (1 ligne sur 100 porte le motif, et c'est une formule mathématique).
  - **À faire** : assainir le dataset (varier les formulations, ancrer les faits, purger les emplacements numériques) **avant** tout réentraînement. Le re-servir est un `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké dans l'image, aucun rebuild).

- [ ] **Index visuel : phase 2 (35 292 portraits de personnages)** _(phase 1 livrée 2026-07-14)_
  - `unified_clip_space` contient désormais **9 165 jaquettes** (anime/manga/film/jeu) et la recherche par jaquette fonctionne en prod. `character_ccip_space` est **vide** : une recherche de personnage répond honnêtement 503 sans facturer.
  - CCIP est vérifié contre les **vrais poids** (768 dims, déterministe, personnages différents à 0,36-0,45 sur de vrais portraits du catalogue). La construction est un `python manage.py build_visual_index --target character` (reprenable, une image morte est sautée) — dominée par le téléchargement, ~35 000 images.
  - **La tour texte de CLIP reste volontairement non exposée** (décidé 2026-07-16) : `VisualIndexService.encode_text` n'a aucun appelant, et c'est le bon choix. La saga `hybrid_search` (archivée HISTORY 2026-07-14→15) a mesuré la recherche texte CLIP sur `unified_clip_space` **sur les vrais vecteurs prod** et l'a trouvée hors sujet — CLIP capte le **style de jaquette, pas le thème** — puis a reverté `hybrid_search` en lexical seul (`revert(rag): … CLIP mesure hors sujet`). L'exposer comme recherche d'œuvres répèterait cette erreur mesurée. `encode_text` = infrastructure dormante, à ne rebrancher que pour une éventuelle recherche « par description de jaquette » (style visuel), jamais thématique.

- [ ] **URI Neo4j locale morte — reste un geste de config** _(constaté 2026-07-12 ; skip silencieux corrigé 2026-07-16)_
  - `Failed to DNS resolve a654e145.databases.neo4j.io` — l'instance configurée en local n'existe plus (la prod tourne sur l'instance `1254b9b8`). **Le skip n'est plus silencieux** : `reconcile_db` nomme désormais les stores vérifiés et signale `UNVERIFIED` quand Neo4j (ou pgvector) est sauté, au lieu d'annoncer un faux « synchronized across … Neo4j » (cf. HISTORY). Reste **purement de la config** : pointer `NEO4J_URI` local vers une instance vivante (prod = `1254b9b8`, ou un Neo4j local) — nécessite les creds, action opérateur, pas du code.

## 🟡 Moyens

- [ ] **Tests — hygiène : fixtures dupliquées, snapshot `sys.modules`, env forcé à l'import** _(audit dette 2026-07-11)_
  - **`api_client` (39×) et `mock_engine` (16×) centralisés** dans [tests/conftest.py](tests/conftest.py) le 2026-07-16 (cf. HISTORY ; CI verte). **Reste** : `mock_prompt_manager` (~21×) — non factorisé car il **varie** (valeurs de retour différentes par test), à traiter au cas par cas si un jour on veut une base commune paramétrable. Fixture autouse [tests/conftest.py:107-139](tests/conftest.py#L107-L139) snapshot/restore `sys.modules` entier à chaque test pour compenser les mocks fuyants (`test_diffusers_adapter.py:25`), et `BRAIN_API_URL` forcé au niveau import ([tests/conftest.py:12](tests/conftest.py#L12)) qui masque les tests d'absence de config : **gardes porteuses, à ne toucher qu'avec prudence** (fixer le mock fuyant AVANT de retirer le snapshot ; rendre la construction DI paresseuse AVANT de retirer le default BRAIN_API_URL).

## 🟢 Faibles

- [ ] **Brain — intégration Moshi (S2S local) chimérique : réécrire ou supprimer**
  - [audio_mixin.py:105](backend/adapters/inference/audio_mixin.py#L105) importe `from moshi.models import Moshi` — cette classe **n'existe pas** dans le package réel (API : `loaders.get_mimi`/`get_moshi_lm` + boucle streaming `LMGen`). Le chemin S2S local n'a jamais fonctionné (le package n'a de plus jamais été dans un lockfile) et lève proprement `InferenceError` — le S2S passe par le brain/Gemini Live. **Décision à prendre** : réécrire l'intégration sur la vraie API (chantier GPU, ~24 Go VRAM pour moshiko-bf16, invérifiable localement) ou supprimer le chemin mort. Le package `moshi` n'est volontairement PAS ajouté aux locks (constat 2026-07-11, en réparant ColPali qui, lui, correspondait à la vraie API).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
- [ ] **Frontend — plotly.js (~4,6 Mo) importé statiquement dans 8 pages** _(audit dette 2026-07-11)_
  - [AIUsagePage.tsx:18](frontend/src/pages/auth/AIUsagePage.tsx#L18), `LatentSpacePage`, `LiquidNeuralNetworkLabPage`, `StrategyLabPage`, `SeichijunreiMapPage`, `ArchetypeNexusPage`, `TransparencyPage`… Le chunk est isolé (`plotly-vendor`, [vite.config.ts:98](frontend/vite.config.ts#L98)) mais chaque visite télécharge 4,6 Mo — `AIUsagePage` n'affiche qu'un historique simple. + three.js dans 5 fichiers. **Reco** : lazy-import interne ou lib légère pour les graphes simples ; auditer via `stats.html` déjà généré.
- [ ] **CI — mono-cible : Windows jamais testé** _(audit dette 2026-07-11)_
  - Un seul `ubuntu-latest` / Python 3.12, aucune matrix — alors que toute la logique anti-pollution async du conftest cible Windows ([tests/conftest.py:14-18](tests/conftest.py#L14-L18)). Angle mort jamais couvert → ajouter `windows-latest` à la matrice de tests dans le workflow GitHub Actions (`.github/workflows/ci.yml`).
- [ ] **Frontend — composants > 500 lignes (reliquat)** _(audit dette 2026-07-11 ; BlindtestPage découpé le 2026-07-16, cf. HISTORY)_
  - `BlindtestPage` traité (753→324, hook + sous-composants). Restent, à découper au fil de l'eau (sous-composants + hooks métier) : `TransparencyPage` (614), `AudioLabPage` (573), `LabHubPage` (569), `SpeechToSpeechLabPage` (544).
- [ ] **Deps — doublons et divers** _(audit dette 2026-07-11)_
  - Lock backend : 3 clients HTTP (aiohttp/httpx/requests), 2 sérialiseurs JSON (orjson/ujson) — souvent transitifs, à vérifier. `@tanstack/react-query-devtools` en `dependencies` ([package.json:31](frontend/package.json#L31)) — corriger dans [Layout.tsx](frontend/src/components/Layout.tsx) pour l'importer de manière conditionnelle en dev uniquement (`import.meta.env.DEV` + dynamic import). `docs/COST_AUDIT.md` cite encore GPT-4o/Claude 3 Sonnet (daté). Full-scan Python évitable : [admin_api.py:165-169](backend/api/animetix/api/admin_api.py#L165-L169) charge toute la table Profile pour filtrer en Python → utiliser à la place `Profile.objects.filter(unlocked_badges__contains="Sponsor Or").count()`.
- [ ] **Backend — DI contourné et double voie Neo4j** _(audit dette 2026-07-11)_
  - [dependencies.py:14-19](backend/api/animetix/api/dependencies.py#L14-L19) résout via l'instance globale du container (work-around coverage documenté) au lieu de `@inject/Provide`. Les scripts pipeline instancient `Neo4jClient` directement ([neo4j_client.py:55](backend/pipeline/neo4j_client.py#L55), [neo4j_sync.py:29](backend/pipeline/neo4j_sync.py#L29)) hors container → deux voies d'accès Neo4j.
