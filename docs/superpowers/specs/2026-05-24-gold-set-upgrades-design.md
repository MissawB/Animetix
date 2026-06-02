# Design Spec - Gold Set & Gold Dataset Upgrades (Industry & French Market)

Date: 2026-05-24  
Author: Antigravity  
Status: Approved  

---

## 1. Goal Description
The purpose of this specification is to expand our evaluation suites to verify the new SOTA SFT expert data concepts. By introducing highly targeted, complex questions regarding prepublication magazines, prestige awards, legendary anisong singers, iconic Japanese seiyū, French market localized publishers, French VF doubleurs, and precise episode/volume statistics, we ensure that our local fine-tuned adapter (`otaku-qwen-7b-adapter`) is audited on its actual specialization without failing basic regression checks.

We implement this via Approach 1 (Cross-Upgrade):
1. **Factual Regression Test Expansion:** Add 5 new queries (Query 8 to 12) to the fast local `GOLD_SET` inside `backend/pipeline/evaluation/regression_benchmark.py`.
2. **RAGAS Evaluation Gold Dataset Expansion:** Add 10 new semantic/graph queries (Query 21 to 30) to `data/mlops/gold_dataset.json`.

---

## 2. Proposed Changes

### Component 1: `regression_benchmark.py` Upgrades
We will modify the hardcoded `GOLD_SET` list in `backend/pipeline/evaluation/regression_benchmark.py` to append the 5 new queries:

```python
    {
        "query": "Quelle maison d'édition publie le manga Berserk en France ?",
        "expected_facts": [["Glénat", "Editions Glénat"]],
        "media_type": "Manga"
    },
    {
        "query": "Quel comédien de doublage français prête sa voix principale au personnage de Luffy dans l'anime One Piece ?",
        "expected_facts": [["Stéphane Excoffier", "Excoffier", "Brigitte Lecordier", "Lecordier"]],
        "media_type": "Character"
    },
    {
        "query": "Quel prix prestigieux a récompensé le manga L'Attaque des Titans en 2011 au Japon ?",
        "expected_facts": [["Prix du manga Kōdansha", "Kodansha Manga Award", "Kodansha", "Kōdansha"]],
        "media_type": "Manga"
    },
    {
        "query": "Combien de saisons et d'épisodes compte l'adaptation animée de Demon Slayer (Kimetsu no Yaiba) ?",
        "expected_facts": [["4 saisons", "quatre saisons"], ["60 épisodes", "soixante épisodes"]],
        "media_type": "Anime"
    },
    {
        "query": "Dans quel magazine de prépublication japonais a été sérialisé le manga Hunter x Hunter ?",
        "expected_facts": [["Weekly Shōnen Jump", "Shonen Jump", "Weekly Shonen Jump"]],
        "media_type": "Manga"
    }
```

### Component 2: `gold_dataset.json` Upgrades
We will edit the JSON array in `data/mlops/gold_dataset.json` to append 10 new structured blocks mapping Query 21 through Query 30 with their metadata, expected titles, query types, and expert ground truths in French.

---

## 3. Verification Plan

### Automated Tests
1. **Syntax Check:** Run `python backend/pipeline/evaluation/regression_benchmark.py` syntax/import test to verify that the python list elements parse cleanly.
2. **JSON Schema Audit:** Verify that `gold_dataset.json` is a valid JSON file and contains exactly 30 objects after the additions.
3. **Execution Check:** Run a quick dry-run of `regression_benchmark.py` with the default local RAG engine to verify that the 12 queries run, outputs are recorded, and a new regression report is generated in `data/mlops/`.

### Manual Verification
1. Verify that the generated regression JSON report correctly contains the 12 queries with their details and accuracy scores listed in detail.
