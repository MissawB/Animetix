# pgvector is empty — diagnosis

**Date:** 2026-07-12
**Status:** investigation, read-only. No code changed.
**Finding:** `VectorRecord.objects.count() == 0` in prod (Neon) against `MediaItem.objects.count() == 44 763`.

---

## TL;DR

The embedding store was never populated because **the only write path is a stub that logs a line and returns**. It is not "unfinished sync", it is a no-op that has been a no-op since the first commit.

The interesting half is what depends on it. The honest answer:

- **One live, user-visible gameplay bug** — the classic "hot/cold" guessing game (and 1v1 duels) score **exactly 0.00 for every wrong guess**. The core mechanic of the flagship game is dead in production.
- **Two features that were never wired at all** and cannot work regardless of a backfill (image search, video-RAG) — and both **charge Berrix before returning an empty list**.
- **Everything else has a real fallback** (RAG hybrid search degrades to SQL ILIKE, semantic cache degrades to exact match) or is dead code.

And the sting: **a backfill alone fixes nothing.** The read path queries the wrong collection names. See [§4](#4-a-backfill-alone-would-not-fix-the-games).

---

## 1. Why the store is empty

Three independent faults, each sufficient on its own. This is why it produced zero rows rather than partial rows.

### 1a. The write path is a no-op stub (root cause)

`MediaItem.post_save` → `enqueue_task("sync_media_item_task", …)` (`backend/api/animetix/signals.py:149-151`)
→ `sync_media_item_task` (`backend/api/animetix/tasks/__init__.py:95-98`)
→ `MediaSyncService.handle_media_update` (`backend/core/domain/services/media_sync_service.py:15-33`)
→ `PipelineSyncAdapter.sync_to_vector_db`:

```python
# backend/adapters/persistence/pipeline_sync_adapter.py:15-16
def sync_to_vector_db(self, media_type: str, item_id: str, data: Dict):
    logger.info(f"📡 Requesting re-vectorization for {media_type} {item_id}")
```

That is the entire method. No embedding is computed, no `VectorRecord` is written. Its sibling `sync_to_graph_db` (`:18-33`) is fully implemented — the Neo4j half works, the vector half was never written.

`git log --follow` on this file shows the stub present in the **initial commit** (`b61f2b49`) and never touched since except by formatting passes. This has never worked, not once.

> This also explains the "catalogue sync takes hours" symptom benignly: outside prod `enqueue_task` runs synchronously (`backend/api/animetix/tasks_client.py:25-53`), so all 44 763 saves ran the Neo4j sync inline. The hours were Neo4j + logging, not embeddings.

### 1b. In production, no task runs at all

`enqueue_task` in prod does `from google.cloud import tasks_v2` (`backend/api/animetix/tasks_client.py:62`).

**`google-cloud-tasks` is not in any lockfile** — absent from `requirements.txt`, `requirements-web.txt` and `requirements-brain.txt` (`grep -i tasks requirements-web.txt` returns nothing). So the import raises `ImportError`, which is caught by the broad `except Exception` at `tasks_client.py:102`, logged as a **warning**, and the task is marked `SKIPPED`:

```python
# tasks_client.py:102-111
except Exception as e:
    logger.warning(f"Cloud Tasks enqueue skipped for {task_name} …")
```

**This is bigger than pgvector.** Every `enqueue_task` call in production is silently discarded — including `ingest_drift_telemetry`, `ingest_duel_telemetry`, and `trigger_club_event`. Worth its own ticket.

### 1c. The offline pipelines are capped at 100 items

The real vectorizers exist (`backend/pipeline/anime/vectorize_anime.py`, `manga/vectorize_manga.py`, `characters/vectorize_characters.py`, `games/vectorize_games.py`, `movies/5_vectorize_movies.py`, `actors/vectorize_actors.py`) and they do the right thing — encode with a local SentenceTransformer, then `repo.upsert_items(...)`.

But:

```python
# backend/pipeline/anime/vectorize_anime.py:64
new_items = items[:100]  # On limite pour la démo
```

They also read from `data/processed/*.json`, **not** from `MediaItem`. Nobody appears to have run them against prod.

---

## 2. What actually consumes the vectors

Traced every reader of `VectorRecord` / the repository port. Ranked by how much it matters.

| # | Feature | Entry point | Behaviour on empty store | Class |
|---|---|---|---|---|
| 1 | **Classic hot/cold game** | `api/games/classic.py:277` | score **0.00** on every wrong guess | **SILENT EMPTY — live bug** |
| 2 | **1v1 Duel (WS)** | `consumers/duel.py:97-100` | broadcasts `score: 0.0` | **SILENT EMPTY — live bug** |
| 3 | Undercover | `undercover_service.py:296-319` | picks a **random** title instead of a near-neighbour | REAL FALLBACK (degraded) |
| 4 | Image search (CLIP) | `api/core/media.py:198` | `[]` — **Berrix charged first** | SILENT EMPTY + never wired |
| 5 | Video-RAG search | `api/labs/video.py:132` | `[]` — **Berrix charged first** | SILENT EMPTY + never wired |
| 6 | RAG hybrid search | `advanced_rag_service.py:237` | falls back to Django ILIKE — but no view routes to it | REAL FALLBACK, and **not user-reachable** |
| 7 | Semantic LLM cache | `agentic_rag_service.py:461` | cache miss → calls LLM | REAL FALLBACK ✅ |
| 8 | Text search / autocomplete | `api/core/media.py:145` | pure SQL, never touched vectors | NOT AFFECTED ✅ |
| 9 | Drift monitor | `api/core/config.py:191` | `{"status": "error", "message": "Collection is empty"}` | SILENT EMPTY (honest) |
| 10 | Transparency dashboard | `api/core/config.py:126` | renders `knowledge_nodes: 0` | cosmetic |
| 11 | `GameService.find_similar_items` / `.calculate_similarity` | — | nothing routes to them | DEAD CODE |

### 2.1 The live bug (#1, #2)

`SimilarityService.calculate_raw_similarity` blends vector and graph similarity:

```python
# backend/core/domain/services/similarity_service.py:79-80
# Pondération hybride : 70% Vecteur + 30% Graphe
return (0.7 * vec_sim) + (0.3 * graph_sim)
```

Both terms are zero in production:

- `vec_sim` → `PGVectorRepositoryAdapter.calculate_similarity` → `len(res.get("embeddings", [])) == 2` is False → **`return 0.0`** (`pgvector_repository_adapter.py:92-105`). No exception is raised; the `except` at `:101` is never even entered.
- `graph_sim` → `_calculate_graph_similarity` returns `0.0` immediately if `self.neo4j` is None (`similarity_service.py:27-28`) — and **the container never passes `neo4j_manager`**: `SimilarityService` is constructed with `repository=` only, at `containers/core_services.py:139-142` and again at `:170-173` and `:177-182`.

So `calculate_raw_similarity` returns **exactly 0.0** for every non-identical guess. In the game view:

```python
# backend/api/animetix/api/games/classic.py:285-290
score = 100.0 if is_correct else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
color = GamePresenter.get_score_color(score)
```

Every wrong guess renders **0.00** with the coldest colour (`secondary`, `scoring_service.py:52-58`). Guesses are then sorted on an all-zero key (`classic.py:307`). The game is reduced to blind exact-title guessing — no proximity signal at all. Same path, same result, in the duel consumer.

**This is a user-visible bug in the flagship game that nobody has reported.** It does not throw, does not log, and returns a plausible-looking number.

### 2.2 The paid-for-nothing bugs (#4, #5)

`CrossModalSearchService.deep_multimodal_search` queries collection `unified_clip_space` (`cross_modal_service.py:59-61`). **That collection name is never written by any code in the repository** — grep confirms exactly one occurrence, the read. Same for `video_temporal` (`rag/video_rag_service.py:22`).

These are not "empty because the backfill never ran". They are empty **by construction** — no pipeline was ever written to populate them. A full backfill of the catalogue would not put a single row in either.

Meanwhile both endpoints deduct Berrix **before** the search and outside the `try` (`api/core/media.py:172-176`; `api/labs/video.py:126-128`), then return `Response([])` and log the call as a successful CLIP inference (`media.py:203-205`). Users are being charged for an empty list.

### 2.3 The things that are genuinely fine

- **RAG hybrid search** has a real fallback: `UnifiedRepositoryAdapter.search_media_items` returns pgvector results *if any*, else Django ILIKE (`unified_repository_adapter.py:63-66`). Keyword-only recall, still answers. **But it is also not user-reachable**: `AdvancedRAGService.hybrid_search` (`advanced_rag_service.py:226-247`) is only called from `ReasoningAgentService` (`reasoning_agent_service.py:82`), which no API view resolves, and from a management command. The user-facing Expert Nexus stream (`api/streams.py:114`) uses Neo4j + web + the *user-memory* collection — a different collection, not the 44 763 media items. So this row is fallback-safe **and** dormant.
- **Text search / autocomplete** (`/api/v1/search/` GET) is the one that carries real traffic, and it never touched vectors: `catalog_service.search_items` → `sql_repository` → Django ORM (`catalog_service.py:198-206`, `core_services.py:133`). Pure Postgres. This is why search "works" and nobody suspected anything.
- **Catalogue / game setup** is unaffected: `CatalogService` reads SQL first and only falls back to `load_catalog` if SQL is empty (`catalog_service.py:63-73`). Secret-title selection, titles, images all work.
- **Semantic cache** degrades to exact-match on the `SemanticCache` table (`django_semantic_cache_adapter.py:17-18`). Costs money in extra LLM calls; correctness unaffected.

---

## 3. Frontend exposure — the bug is on screen right now

The classic game is a **normal, linked route**, not an orphan page:

- `frontend/src/features/games/routes/GameRoutes.tsx:37-38` → `/game/classic/` (lobby) and `/game/classic/play/` (game).

And the page renders the dead score directly:

```tsx
// frontend/src/pages/games/ClassicGamePage.tsx:254, :280, :288
const score = Math.round(g.score ?? 0);
…
<span className="text-lg font-black tabular-nums w-12 text-right">{score}%</span>
…
<div style={{ width: `${Math.max(4, score)}%` }} />   // proximity bar
```

plus `heatOf` (`ClassicGamePage.tsx:46`) which maps `g.color` → a heat colour, and `g.color` is always `secondary` (the coldest bucket).

So a real user playing the flagship game today sees **every single guess listed as `0%`, with the coldest heat colour and a proximity bar stuck at its 4% minimum width** — until they happen to type the exact right title, which jumps to 100%. There is no empty state and no error; it renders as a confident, precise, completely uninformative `0%`.

That is not a latent bug. It is the product's main game, visibly broken, and nobody has reported it — which is itself the most alarming fact in this document.

It is also **linked from the homepage** (`frontend/src/features/home/data/useGameModes.ts:28`, rendered by `SoloChallenges`) — not buried.

The other reachable, vector-dependent pages:

| Page | Route | Linked from | State today |
|---|---|---|---|
| Classic game | `/game/classic/play/` (`GameRoutes.tsx:38`) | homepage | every guess = `0%` |
| Undercover | `/undercover/` (`GameRoutes.tsx:59`) | homepage + games hub | random word pair instead of near-neighbour |
| Visual Nexus / video search | `/lab/visual-nexus/` (`LabRoutes.tsx:50`), `/search/` visual tab | Lab hub, Forge hub | **charges Bx**, renders "ready to scan" empty state |
| Image search (camera) | `SearchBar.tsx:134-141` in Forge | Forge hub | **charges Bx**, renders "no results" |

Not affected, despite the names: Akinetix, Emoji, Paradox, VS Battle, Covertest, Blindtest, Quiz-Who (all read precomputed JSON or Neo4j), and the Latent Space 3D map (`/lab/latent-space/`) which reads `data/artifacts/latent_space_*.json` off disk (`api/labs/dashboards.py:41-51`), not pgvector.

---

## 4. A backfill alone would NOT fix the games

This is the single most important thing in this document.

`SimilarityService` passes **`media_type` directly as the collection name**:

```python
# similarity_service.py:72-74
vec_sim = self.repository.calculate_similarity(
    media_type, str(secret_full["id"]), str(guess_full["id"])
)
```

`media_type` is `"Anime"` / `"Manga"` / `"Character"`. But the pipelines write collections named `anime_thematic`, `manga_thematic`, `character_vibe` … The `coll_names` mapping that translates one to the other (`pgvector_repository_adapter.py:46-53`) is applied **only** in `search_media_items` and `load_catalog` — **not** in `calculate_similarity` (`:81`) or `get_nearest_neighbors` (`:67`).

So after a perfect backfill, the game would still run `VectorRecord.objects.filter(collection_name="Anime")` → 0 rows → `return 0.0`. Identical bug, now with 44 763 embeddings sitting unused in the table.

The docstring at `similarity_service.py:89-90` explicitly codifies this ("`media_type` sert directement de nom de collection"), so it is a deliberate-looking mistake, not a typo — which is exactly why it would survive a backfill.

**Corollary: the cheapest test of the whole theory costs nothing.** Vectorise ~200 anime into `anime_thematic`, fix the two-line collection-name mapping, and play the game. If the hot/cold score comes alive, the diagnosis is confirmed before spending anything on a full backfill.

---

## 5. Sizing the backfill (only if you want #1–#3 back)

**Only the games need vectors.** RAG is fine on SQL fallback. Image/video search need a pipeline that does not exist. So the backfill scope is far smaller than "44 763 × every collection".

Minimum viable set for the games:

| Collection | Source | Rough count |
|---|---|---|
| `anime_thematic` | `MediaItem(media_type="Anime")` | ~20k (unverified split) |
| `manga_thematic` | `MediaItem(media_type="Manga")` | ~15k |
| `character_vibe` | `MediaItem(media_type="Character")` | ~10k |

Total order of magnitude: **~45k text embeddings, one per item, text-only** (the visual collections are only used by features that are dead anyway).

**Model:** the code path is a local `SentenceTransformer`. The pipelines use `models_registry.text_model` (`pipeline/models_registry.py:48-51`); the query path hardcodes `jinaai/jina-embeddings-v3` (`pgvector_repository_adapter.py:59-61`). **These must match or cosine distance is meaningless** — worth checking `MODEL_VERSION_TEXT` before running anything.

**Cost/time:** a local CPU SentenceTransformer over ~45k short descriptions is on the order of **1–3 hours on one CPU box, ~zero marginal cost** (no API). On a GPU, minutes. There is no Vertex/Jina API call in this path — `is_alloydb_ai_supported()` is False on Neon (no `google_ml_integration` extension) and `VERTEX_AI_VECTOR_SEARCH_ACTIVE` defaults to False (`settings.py:651-652`), so the SQL-side `embedding()` path is inert and everything is computed locally.

**Where it should run:** a management command against prod DB, reading `MediaItem` (not the stale `data/processed/*.json` the current pipelines read). No such command exists — `reconcile_db` only *reports*.

### What I cannot determine from the code

- The actual `MediaItem` split per `media_type` (needs a DB query).
- Whether Neo4j prod is actually populated — so I cannot say whether wiring `neo4j_manager` into `SimilarityService` would restore a *useful* 0.3 graph term or just a slower 0.0.
- Whether `MODEL_VERSION_TEXT` in prod resolves to the same model the query path hardcodes.
- Whether the `vector` column (unbounded dimension, `models.py:804-807`) has an ANN index. It cannot — pgvector requires a fixed dimension for HNSW/IVFFlat. At 45k rows sequential scan is survivable but this will not scale.

---

## 6. Recommendation — cheapest correct next step

Do **not** start with the backfill.

1. **Fix the read path first (2 lines, free).** Map `media_type → coll_names[media_type]` in `PGVectorRepositoryAdapter.calculate_similarity` and `get_nearest_neighbors`. Without this, nothing else matters.
2. **Vectorise one collection (`anime_thematic`) and play the game.** Confirms the diagnosis end-to-end for a couple of CPU-hours. If the hot/cold score comes alive, backfill the rest.
3. **Stop charging for the dead features.** `api/core/media.py:172` and `api/labs/video.py:126` deduct Berrix for searches that return `[]` by construction. Either gate them off or refund the path. This is the only finding here with a money/trust cost attached.
4. **Delete or implement `PipelineSyncAdapter.sync_to_vector_db`.** A stub that logs "Requesting re-vectorization" is worse than no method — it is why this went unnoticed for the life of the project.
5. **Separately: `google-cloud-tasks` is missing from the prod lockfile.** Every background task in production is being silently dropped. That is a bigger blast radius than pgvector and deserves its own ticket.

### What is genuinely dead — leave it alone

`CrossModalSearchService` / `unified_clip_space`, `VlmIndexingService`, `VideoRAGService` / `video_temporal`, `GameService.find_similar_items`, `GameService.calculate_similarity`, `DriftService.COLLECTIONS` (which names `anime`/`manga`/`character` — collections that do not exist either, `drift_service.py:11`). None of this has ever had data. Don't backfill it; decide whether to delete it.
