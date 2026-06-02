# Dagster/Neo4j Automated Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the Neo4j knowledge graph synchronization during Dagster asset materialization so that whenever data is ingested or refined, the graph is automatically updated without requiring manual intervention.

**Architecture:** We are updating the `neo4j_sync.py` to handle "Games" explicitly (as there is an asset `sync_games_to_graph` but no mapping in `neo4j_sync.py`). Then we'll ensure `neo4j_client.py` has the missing methods like `sync_character_to_graph` to support the sync process smoothly. The Dagster dependencies are already well set up in `dagster_app.py`, they just need the underlying implementation to work cleanly.

**Tech Stack:** Python, Neo4j, Dagster.

---

### Task 1: Update Neo4j Sync Mapping

**Files:**
- Modify: `backend/pipeline/neo4j_sync.py`

- [ ] **Step 1: Add "Game" to the sync mappings**
  Update `file_map` to handle `Game` media types and link to the correct JSON path.

```python
    GAME_DB = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_games.json')
    # ... inside run_sync_type_to_graph
    file_map = {
        "Anime": ANIME_DB,
        "Manga": MANGA_DB,
        "Character": CHAR_DB,
        "Game": GAME_DB
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/pipeline/neo4j_sync.py
git commit -m "feat: add Game data mapping to neo4j_sync for automated Dagster materialization"
```

### Task 2: Ensure Neo4jManager Support

**Files:**
- Modify: `backend/pipeline/neo4j_client.py`

- [ ] **Step 1: Implement `sync_character_to_graph` in `Neo4jManager`**
  Currently, `neo4j_sync.py` tries to call `sync_character_to_graph` on `Neo4jManager` for characters, but it doesn't exist. Let's create it.

```python
    def sync_character_to_graph(self, character_item: dict):
        """Injects a Character node and links it to associated media."""
        if not self.driver: return
        with self.driver.session() as session:
            session.execute_write(self._sync_character_tx, character_item)

    @staticmethod
    def _sync_character_tx(tx, item):
        query = "MERGE (c:Character {id: $id}) SET c.name = $name RETURN c"
        tx.run(query, id=str(item['id']), name=item.get('name'))
        
        # Link to anime or manga if present in the data
        for anime_id in item.get('anime_appearances', []):
             tx.run("MATCH (c:Character {id: $cid}) MATCH (m:Media {id: $mid}) MERGE (c)-[:APPEARS_IN]->(m)", cid=str(item['id']), mid=str(anime_id))
```

- [ ] **Step 2: Allow connection args in Neo4jManager init**
  `neo4j_sync.py` tries to pass `uri`, `user`, `password` to `Neo4jManager` directly, but the init doesn't take kwargs:
  Change `def __init__(self):` to `def __init__(self, uri=None, user=None, password=None):` and set them up using `self._uri = uri or NEO4J_URI` etc.

- [ ] **Step 3: Commit**

```bash
git add backend/pipeline/neo4j_client.py
git commit -m "feat: implement character graph sync and support dynamic connection args in Neo4jManager"
```
