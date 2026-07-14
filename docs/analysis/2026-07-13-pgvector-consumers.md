# pgvector: who still depends on it? — consumer map against current `main`

**Date:** 2026-07-13
**Status:** investigation, read-only. No code changed.
**Supersedes:** `docs/analysis/2026-07-12-pgvector-empty.md` (two of its central conclusions are now stale — see §0).
**Facts:** `VectorRecord.objects.count() == 0` in prod. `MediaItem` = 44 761 rows.

---

## TL;DR — almost nothing depends on these vectors any more

Say it plainly, because it changes the whole decision:

**After the ProximityService redesign, exactly ONE live user-facing feature reads the catalogue vectors — and it has a working fallback.** That is Undercover's word-pair picker, which silently degrades to a random pair. Nobody would notice. Nobody has.

The classic game and the duel — the two features the 2026-07-12 doc called "the flagship game, visibly broken" — **no longer touch vectors at all.** That finding is dead. It was true when written; the redesign removed it.

What is left that actually hurts a user is not a gameplay bug. It is a **billing** bug:

> **Two endpoints charge 6 Bx each and return an empty list by construction.** Their collections (`unified_clip_space`, `video_temporal`) have no writer any ordinary user can reach. The UI renders the *pre-search idle state* afterwards — so the user pays, sees "enter a description", and has no way to know the search even ran.

**A backfill of 44 761 embeddings would fix nothing that a user can feel.** It would improve one Undercover heuristic. It would not put a single row in either collection that the paid endpoints read.

---

## 0. What the prior analysis got wrong (now)

Two of its load-bearing claims are **no longer true on `main`**:

| Prior claim | Status today |
|---|---|
| §2.1 "Classic game + duel score exactly 0.00 on every wrong guess — the flagship game is dead" | **STALE.** Both were rebuilt on `ProximityService`. Neither touches a vector. See §1.1. |
| §4 "A backfill alone would NOT fix the games — `calculate_similarity`/`get_nearest_neighbors` never map `media_type` → collection name" | **FIXED.** `_resolve_collection` now exists (`backend/adapters/persistence/pgvector_repository_adapter.py:76-85`) and is applied on entry to **both** `get_nearest_neighbors` (`:90`) and `calculate_similarity` (`:105`). |
| §5 "the query path hardcodes `jinaai/jina-embeddings-v3` — writer and reader may not match" | **FIXED.** Both sides now resolve through `core/utils/model_registry.py`: reader at `pgvector_repository_adapter.py:68-70` (`resolve_text_embedding_model_id()`), writer via `pipeline.models_registry`. Single source of truth. |

Still true, and confirmed against `main`:

- `PipelineSyncAdapter.sync_to_vector_db` is **still a one-line logging stub** — `backend/adapters/persistence/pipeline_sync_adapter.py:15-16`. The entire body is `logger.info(...)`. Its sibling `sync_to_graph_db` (`:18-33`) is real. **This remains the root cause of the empty store.**
- `unified_clip_space` and `video_temporal` have **no writer** reachable by a normal user, and both endpoints deduct Bx first. Verified precisely in §2.

---

## 1. The consumer map, redrawn against `main`

Ranked by what actually hurts a user today.

| # | Consumer | Entry point | Reachable? | Behaviour on empty store | Class |
|---|---|---|---|---|---|
| 1 | **Image search (CLIP)** | `api/core/media.py:198` | YES | `[]`, HTTP 200 — **6 Bx charged first** | **PAID + SILENT EMPTY** |
| 2 | **Video-RAG search** | `api/labs/video.py:132` | YES | `[]`, HTTP 200 `"status":"success"` — **6 Bx charged first** | **PAID + SILENT EMPTY** |
| 3 | Undercover word pair | `undercover_service.py:298` | YES (WS) | random title instead of near-neighbour | **REAL FALLBACK** (degraded, invisible) |
| 4 | RAG hybrid search | `advanced_rag_service.py:226-247` | YES (Expert Nexus stream) | BM25 lexical leg still returns results | **REAL FALLBACK** |
| 5 | Semantic LLM cache | `django_semantic_cache_adapter.py:20-63` | YES | cache miss → calls the LLM | **REAL FALLBACK** (self-populating) |
| 6 | Text search / autocomplete | `api/core/media.py:145` | YES | never touched vectors — pure SQL | NOT AFFECTED |
| 7 | Drift monitor | `drift_service.py:11` | YES | `"unknown"` forever — **wrong collection names** | DEAD (independently broken) |
| 8 | Transparency dashboard | `api/core/config.py:126` | YES | renders `knowledge_nodes: 0` | COSMETIC |
| 9 | Classic game | `api/games/classic.py` | YES | **no vector call** | **REMOVED by redesign** |
| 10 | Duel (WS) | `consumers/duel.py` | YES | **no vector call** | **REMOVED by redesign** |
| 11 | `SimilarityService.calculate_raw_similarity` | `similarity_service.py:23` | — | no live caller | **DEAD CODE** |
| 12 | `GameService.find_similar_items` / `.calculate_similarity` | `game_service.py:165,173` | — | no caller outside tests | **DEAD CODE** |

### 1.1 What the proximity redesign removed from the list

`ProximityService` (`backend/core/domain/services/proximity/service.py`) scores from the **AniList recommendation graph + IDF-weighted tag/genre vocabulary**, read out of the catalogue. It takes `catalog_service` and nothing else — `containers/core_services.py:144-147` wires it with `catalog_service=` only, **no repository**. It never touches `VectorRecord`.

- **Classic game** — `api/games/classic.py:346-362`. Scores via `proximity_service.rank()` / `.report()`; `score = 100.0 if is_correct else report["percent"]`. No `calculate_raw_similarity` anywhere in the file. On failure it raises `GameLogicError` → `_proximity_unavailable()` (`classic.py:28-37`), an **honest HTTP error**, not a silent 0.
- **Duel** — `consumers/duel.py:134-174`, same engine, same honest error path.
- The only `SimilarityService` call left in the games is `check_title_match` (`similarity_service.py:58-100`) — pure string normalisation, no vectors.

`similarity_service.py:26-32` documents the demotion itself: the description-embedding cosine had *"un plancher de bruit à 0,583 entre deux œuvres SANS RAPPORT"* and ranked Kimetsu closer to Death Note than Monster. **The vectors were removed from the games because they were worse than the graph, not because they were empty.** That is the single most important context for any backfill decision.

### 1.2 The one real remaining consumer: Undercover

`backend/core/domain/services/undercover_service.py:295-319`:

```python
similar = self.similarity_service.find_similar_items(media_type, str(civil_id), count=10)
neighbors = (similar or {}).get("metadatas") or [[]]
options = [ ... for m in neighbors[0] if str(m["id"]) != str(civil_id)]
if options:
    undercover_title = random.choice(options[:5])
except Exception as e:
    logger.warning(f"Semantic word selection failed for Undercover: {e}")

if not undercover_title:
    undercover_title = random.choice([...])   # :312 — random fallback
```

- Reached only for mono-category games in `VECTOR_CATS = {"Anime","Manga","Character"}` (`undercover_service.py:33`, gate at `:227-231`).
- Live: WS consumer `consumers/undercover.py:449` → `game_service.py:152`.
- **Genuine, working fallback.** `get_nearest_neighbors` returns `None` on no embeddings (`pgvector_repository_adapter.py:95-96`) → `options == []` → random title. The game starts. The undercover word is just semantically random instead of "close". A user cannot tell.

This is the *entire* live dependency on 44 761 catalogue embeddings.

### 1.3 The fallbacks that are genuinely fine

- **RAG hybrid search** (`advanced_rag_service.py:226-247`): BM25 lexical index runs first (`_get_or_create_index`, `:249-256`), the semantic leg is inside try/except (`:236-241`) and RRF-fused (`:243`). Empty vectors → lexical-only results, still non-empty. Reachable via `AgenticRAGStreamView` (`api/streams.py:114-158`). Correct degradation.
- **`UnifiedRepositoryAdapter.search_media_items`** (`unified_repository_adapter.py:63-66`): pgvector `[]` → falls through to Django ILIKE (`django_repository_adapter.py:78-94`). Correct.
- **Semantic cache** (`django_semantic_cache_adapter.py`): `get_semantic` wraps everything in try/except → `None` on empty (`:60-63`); exact-match on the `SemanticCache` table still works (`:17-18`); `set` (`:65-85`) self-populates. Empty store = cache miss = extra LLM calls. Costs money, not correctness.
  - *Corroborating signal:* `set` writes a `VectorRecord` under collection `semantic_cache` (`:78-83`). `VectorRecord.count() == 0` in prod therefore means the Expert Nexus stream has **either never run in prod, or its embedding leg is silently failing**. Worth one probe; not load-bearing.

---

## 2. The Berrix question — both halves of the prior claim CONFIRMED, and worse than stated

This is the finding that matters. Verified line by line.

### 2.1 The collections have no writer. Confirmed.

Repo-wide grep for each string:

- **`unified_clip_space`** — exactly **one** occurrence in all of `backend/`: the read, at `backend/core/domain/services/cross_modal_service.py:60`. No pipeline, no adapter, no management command, no task ever writes it. The six `vectorize_*.py` scripts write `anime_thematic`, `manga_thematic`, `manga_plot`, `manga_visual_vibe`, `character_vibe`, `character_visual_vibe`, `movie_thematic|plot|vibe`, `game_thematic|plot|vibe`, `actor_vibe` — **never `unified_clip_space`**.
- **`video_temporal`** — one read (`rag/video_rag_service.py:22`) and one writer, `index_video` (`:24-58`) — but that writer is behind `VideoRAGIndexView`, which is `permission_classes = [permissions.IsAdminUser]` (`api/labs/video.py:71`) **and** hidden in the UI behind `{isAdmin && <VideoIndexing />}` (`frontend/src/pages/labs/VideoRagPage.tsx:52, :154`).

So: image search is dead **by construction**. Video-RAG is dead **for every non-staff user** — they can pay to search an index they have no way to populate. A full catalogue backfill puts **zero** rows in either.

### 2.2 Bx is deducted before the search, outside the try. Confirmed.

**Image search** — `backend/api/animetix/api/core/media.py`:
```python
:172   deduct_berrix(
:173       request.user,
:174       FEATURE_BX_COSTS["vision_clip"],        # = 6 Bx  (berrix_economy.py:126)
:175       "Recherche par image (CLIP)",
:176   )
:178   try:
:198       results = self.cross_modal_search_service.deep_multimodal_search(...)
:203       self.usage_port.log_usage(engine="clip-vit-large-patch14", units=1, ...)
:207       return Response(self._format_results(results))     # -> []  HTTP 200
```
The deduction is at `:172`, **before** the `try` at `:178` and before the search at `:198`. The call is then **logged as a successful CLIP inference** (`:203`).

**Video-RAG search** — `backend/api/animetix/api/labs/video.py`:
```python
:127   deduct_berrix(
:128       request.user, FEATURE_BX_COSTS["video_rag"], "VideoRAG — recherche vidéo"   # = 6 Bx (berrix_economy.py:102)
:129   )
:131   try:
:132       results = self.video_rag_service.search_video_segment(query, limit=10)
:136       return Response({"status": "success", "results": results})   # -> results=[]  HTTP 200 "success"
```

**Quantified: 6 Bx per call, both endpoints. No refund path. No exception. HTTP 200. Logged as success.**

### 2.3 What the user sees — worse than "no results"

Both UIs render the **pre-search idle state** on an empty result, not an empty-results state:

| Endpoint | Frontend caller | What renders after paying |
|---|---|---|
| Image search | `frontend/src/api.ts:30-38` ← `SearchBar.tsx:77`, camera button `SearchBar.tsx:134-141` | `SearchBar.tsx:158-159` — italic *"Aucun résultat trouvé"*. Indistinguishable from a text-search miss. **No cost shown anywhere before the click** — the button tooltip says only "Recherche par image". |
| Video-RAG | `VideoRagPage.tsx:59`; `UniversalSearchHubPage.tsx:51`; `VisualNexusPage.tsx:41`; `VideoLabPage.tsx:68` | `Timeline.tsx:8-18` — a **pulsing** *"Aucun segment chargé — Saisissez des mots-clés…"*, i.e. the never-searched placeholder. And `UniversalSearchHubPage.tsx:277-283` — *"Moteur Optique Prêt / Entrez une description pour scanner la base de clips"* at `opacity-10`. `error` stays `null` (`VideoRagPage.tsx:60`). |

So the user is charged, and the app then tells them **to type a query they just typed**. There is no error, no empty-results message, no signal that anything happened. This is the "swallowed" class in its purest form: it looks fine and is not.

Image search is reachable from the **Graph pages** (`GraphPage.tsx:33`, `GraphNeighborhoodPage.tsx:41`) and the **Forge item selector** (`ForgeItemSelector.tsx:38, :94`). Video-RAG is reachable from **four** routed, hub-linked pages (`LabRoutes.tsx:44,50,72`; `/search/` visual tab, linked from `Footer.tsx:39` and `SidebarDrawer.tsx:119`). Neither is buried.

> **Aggravating detail.** `cross_modal_service.py:36-40`: if the text embedding fails, the service substitutes `np.random.rand(512)` — a **random vector** — instead of failing. If `unified_clip_space` ever *were* populated, a failed embedding would return confident, random results. Fix the billing bug and this one lands next.

---

## 3. The write path

### 3.1 What writes a `VectorRecord` today

`backend/pipeline/vector_client.py` is the only module that touches the model:
- `PGVectorCollectionWrapper.upsert` — `:228-313`; `VectorRecord.objects.update_or_create(collection_name=..., item_id=str(item_id), ...)` at `:305-313` (AlloyDB raw-SQL branch at `:266-298`).
- `VertexAICollectionWrapper.upsert` — `:129-155`; note the Vertex branch at `:138-144` **only logs** — it never ships anything to Vertex.

`item_id` is `str(id)` — whatever the caller passes. **No id normalisation in the client.** Correctness lives entirely in the six vectorisers.

### 3.2 The offline pipelines

**The `[:100]` demo cap is gone everywhere.** `vectorize_anime.py:54,84` replaced it with an opt-in `--limit` (default `None` = full catalogue). No `[:100]` survives in `backend/pipeline/**`.

| Script | Source | Collections | ID written | Verdict |
|---|---|---|---|---|
| `anime/vectorize_anime.py` | `data/processed/clean_root_animes.json` (`:31`) | `anime_thematic`, `character_visual_vibe` | `idMal or mal_id or id` (`:118`) | **WORKS, ids MATCH** |
| `manga/vectorize_manga.py` | `clean_root_mangas.json` (`:44`) | `manga_thematic`, `manga_plot`, `manga_visual_vibe` | `item["id"]` (`:92`) = **AniList id** | **BROKEN ×2 — see below** |
| `characters/vectorize_characters.py` | `filtered_characters.json` (`:45`) | `character_vibe`, `character_visual_vibe` | `item["id"]` (`:89`) | ids match |
| `games/vectorize_games.py` | `clean_root_games.json` (`:20`) | `game_thematic`, `game_plot`, `game_vibe` | `item["id"]` (`:109`) | ids match |
| `movies/5_vectorize_movies.py` | `clean_root_movies.json` (`:17`) | `movie_thematic`, `movie_plot`, `movie_vibe` | `item["id"]` (`:60`) | ids match |
| `actors/vectorize_actors.py` | `clean_root_actors.json` (`:15`) | `actor_vibe` (`:86`) | `item["id"]` (`:65`) | ids match |

**Every script reads `data/processed/*.json`. None reads `MediaItem`.** There is no `MediaItem → vector` path anywhere in the codebase — no management command (`backend/api/animetix/management/commands/` has no vectoriser), only the Celery `run_daily_ingestion_workflow` (`tasks/pipeline_tasks.py:34-158`) which invokes the same JSON-driven scripts.

### 3.3 The id contract — anime repaired, **manga still broken**

`sync_catalog.py:46-65` defines `MediaItem.external_id`: Anime → `idMal|mal_id|id` (MAL), **Manga → `idMal|mal_id|id` (MAL)**, Character/Movie/Game/Actor → `id`.

The readers look up `MediaItem.external_id`: `DjangoRepositoryAdapter._to_dict` sets `"id": item.external_id` (`django_repository_adapter.py:189-191`) → `catalog_service.py:83,86` builds `id_to_full_data` from it → `similarity_service.py:37-44` passes `secret_full["id"]` into `repository.calculate_similarity`.

- **Anime: MATCH.** `vectorize_anime.py:118` emits the MAL id, the reader asks for the MAL id. The earlier bug is fixed here.
- **Manga: MISMATCH — the original bug, unrepaired.** `vectorize_manga.py:92` writes `str(item["id"])` — the raw **AniList** id — while the catalogue serves manga under the **MAL** id. Every manga vector would be written under an id no reader ever asks for. `calculate_similarity`'s `len(...) == 2` guard (`pgvector_repository_adapter.py:114`) fails → silent `0.0`.
- **Manga is doubly broken.** `vectorize_manga.py:31-34` does `get_container().repository` — but `Container` (`backend/api/animetix/containers/__init__.py:10-26`) exposes only `infrastructure/persistence/inference/agentic/core`. **There is no `.repository`.** This raises `AttributeError` on the first line of `run_vectorization()` (`:49`), swallowed by the blanket `except Exception` at `:163` and written to `manga_vectorize_error.log`. The manga vectoriser **cannot have run since the container was nested.** `vectorize_anime.py:35-41` and `vectorize_characters.py:32-35` use the correct `get_container().persistence.repository()` — manga was left behind.

### 3.4 `PipelineSyncAdapter.sync_to_vector_db` — stub confirmed

`backend/adapters/persistence/pipeline_sync_adapter.py:15-16`. Body is one `logger.info(f"📡 Requesting re-vectorization for …")`. Nothing else. This is why `MediaItem.post_save` never produced a vector, and why the store is empty rather than partial.

### 3.5 Bonus: the drift monitor is broken independently of all this

`backend/core/domain/services/drift_service.py:11` — `COLLECTIONS = ("anime", "manga", "character")`. **No writer anywhere uses those names** (the real ones are `anime_thematic` / `manga_thematic` / `character_vibe`). `management/commands/generate_drift_baselines.py:6` hardcodes the **same three wrong names**, so the baseline can never be generated either. Drift reporting can only ever return `{"status": "unknown", "message": "No baseline found for comparison"}` — even after a perfect backfill.

---

## 4. Sizing the honest options

### Option A — do nothing about the vectors. Fix the billing. (recommended)

The vectors buy you: one Undercover heuristic. That is it. Everything else either has a real fallback, is dead, or was deliberately moved off vectors because they were **measurably worse** (`similarity_service.py:26-32`).

**Cost: near zero. Impact: the only user-visible harm goes away.**

### Option B — if you still want the catalogue vectorised

| Collection | Source | Rough count | Blocker |
|---|---|---|---|
| `anime_thematic` | `data/processed/clean_root_animes.json` | unknown split | none — script works, ids match |
| `character_vibe` | `filtered_characters.json` | unknown split | none |
| `manga_thematic` | `clean_root_mangas.json` | unknown split | **two bugs: `.repository` AttributeError (`:34`) + AniList-vs-MAL id (`:92`)** |

- **Model:** `EMBEDDING_VERSIONS["text"]["v3"] = "jinaai/jina-embeddings-v3"` (`core/utils/model_registry.py:122-131`), default from `MODEL_VERSION_TEXT` (`:147`) — 1024-d, ~1 GB, CPU-loadable. `v4` = `Qwen/Qwen3-Embedding-8B` (4096-d, GPU-only). Writer and reader now resolve through the same function, so they cannot drift.
- **Where it runs:** a local box running `backend/pipeline/*/vectorize_*.py` against `data/processed/*.json`. **Not from prod `MediaItem`** — no such path exists.
- **Time:** ~45k short descriptions through a local CPU SentenceTransformer ≈ **1–3 hours on one CPU box, ~zero marginal cost** (no API call; `is_alloydb_ai_supported()` is False on Cloud SQL and `VERTEX_AI_VECTOR_SEARCH_ACTIVE` defaults False, so everything is computed locally).

### Option C — make image / video search actually work

**This is a new feature, not a backfill.** `unified_clip_space` needs a CLIP/SigLIP image-embedding pipeline over 44 761 posters that **does not exist and was never written**. `video_temporal` needs a content source that only staff can supply. Neither is a "populate the table" job. Scope accordingly, or delete the features.

### What I cannot determine from the code

- The `MediaItem` split per `media_type` (needs a DB query) — so all counts above are shape, not size.
- Whether any staff account has ever indexed a video into `video_temporal`. If none has, **every** video-RAG call ever made was charged for an empty index. A `VectorRecord.objects.filter(collection_name="video_temporal").count()` settles it — and given the global count is 0, the answer is almost certainly **none**.
- **How many Bx have actually been burned** on these two endpoints. Check the usage/transaction log for `engine="clip-vit-large-patch14"` and `engine="video-rag"`, and the Bx ledger for `"Recherche par image (CLIP)"` / `"VideoRAG — recherche vidéo"`. That number is the true size of this finding.
- Whether the `vector` column (unbounded dimension, `models.py:804-807`) can carry an ANN index — it cannot as declared; pgvector requires a fixed dimension for HNSW/IVFFlat.

---

## 5. Recommendation — ranked by what hurts a user today

1. **Stop charging for the two dead endpoints.** `api/core/media.py:172` and `api/labs/video.py:127`. Either gate them off (feature flag / 503) or move the deduction *after* a non-empty result. This is the only finding with a money-and-trust cost. **Nothing else on this list touches a user's wallet.**
2. **Fix the empty-state lie.** Both UIs render the *idle* placeholder after a charged search (`Timeline.tsx:8-18`, `UniversalSearchHubPage.tsx:277-283`, `SearchBar.tsx:158-159`). Even after (1), a search that returns nothing must *say* it returned nothing.
3. **Decide about the vectors — and the honest answer is probably "delete".** One Undercover heuristic, whose fallback already works, does not justify a pipeline. If you keep them: fix `vectorize_manga.py:34` and `:92` first, then run anime + characters.
4. **Delete or implement `sync_to_vector_db`** (`pipeline_sync_adapter.py:15-16`). A stub that logs "Requesting re-vectorization" is worse than no method — it is exactly why this went unnoticed for the life of the project.
5. **Delete the dead surface:** `SimilarityService.calculate_raw_similarity` / `find_similar_items` (only Undercover uses the latter), `GameService.calculate_similarity` / `.find_similar_items` (`game_service.py:165,173` — no caller outside tests), `containers/core_services.py:139-142` (a Singleton provider never injected anywhere), `CrossModalSearchService`, `VlmIndexingService`, `DriftService` (`drift_service.py:11` — wrong collection names, can never work).
6. **Separately: `cross_modal_service.py:36-40` substitutes `np.random.rand(512)` on embedding failure.** Latent, but it is a landmine under any future fix.
