# Gold Set & Gold Dataset Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand both the factual precision regression Gold Set (from 7 to 12 items) and the sémantic RAGAS Gold Dataset (from 20 to 30 items) to cover the new meta-vocabulary, awards, publishers, seiyū, and French market concepts.

**Architecture:** Extend static databases/arrays with validated, expert French pop-culture question-answer structures.

**Tech Stack:** Python 3.12, JSON

---

### Task 1: Extend Factual `GOLD_SET` in `regression_benchmark.py`

**Files:**
- Modify: `backend/pipeline/evaluation/regression_benchmark.py:13-50`

- [ ] **Step 1: Write the updated `GOLD_SET` list**

Modify the `GOLD_SET` array in [regression_benchmark.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/pipeline/evaluation/regression_benchmark.py) to append the 5 new query dictionaries. The updated array should look exactly like this:

```python
GOLD_SET = [
    {
        "query": "Explique l'intrigue de l'anime Death Note en une phrase.",
        "expected_facts": ["Light Yagami", ["Ryuk", "dieu de la mort", "shinigami"], ["carnet", "livre", "cahier", "système de notes", "Death Note"]],
        "media_type": "Anime"
    },
    {
        "query": "Qui est l'auteur du manga One Piece ?",
        "expected_facts": [["Eiichiro Oda", "Oda"]],
        "media_type": "Manga"
    },
    {
        "query": "Quelle est l'arme emblématique de Guts dans Berserk ?",
        "expected_facts": [["Dragon Slayer", "Dragonslayer", "épée", "lame géante"]],
        "media_type": "Character"
    },
    {
        "query": "Qui a créé la franchise de jeux vidéo Metal Gear ?",
        "expected_facts": [["Hideo Kojima", "Kojima"]],
        "media_type": "Game"
    },
    {
        "query": "Quel studio a produit l'anime Neon Genesis Evangelion ?",
        "expected_facts": [["Gainax", "Studio Gainax"]],
        "media_type": "Anime"
    },
    {
        "query": "Quel studio est derrière l'animation de Jujutsu Kaisen ?",
        "expected_facts": [["MAPPA", "Studio MAPPA"]],
        "media_type": "Anime"
    },
    {
        "query": "Qui interprète le rôle du Joker dans le film The Dark Knight de 2008 ?",
        "expected_facts": [["Heath Ledger", "Ledger"]],
        "media_type": "Movie"
    },
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
]
```

- [ ] **Step 2: Commit Task 1**

```bash
git add backend/pipeline/evaluation/regression_benchmark.py
git commit -m "test: extend GOLD_SET regression benchmark with 5 new queries"
```

---

### Task 2: Extend RAGAS `gold_dataset.json`

**Files:**
- Modify: `data/mlops/gold_dataset.json`

- [ ] **Step 1: Append 10 new structured objects to `gold_dataset.json`**

Edit [gold_dataset.json](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/data/mlops/gold_dataset.json) to append the following 10 new JSON objects right before the closing square bracket `]`. Ensure that a comma `,` is placed before the first new object:

```json
  {
    "query": "Quels comédiens de doublage français (VF) prêtent leur voix à la fois à des personnages de Naruto et de One Piece ?",
    "expected_id": "0",
    "expected_title": "Multiple",
    "is_architectural": true,
    "query_type": "graph",
    "ground_truth": "Le système doit lier les relations de voix françaises. Par exemple, Christophe Lemoine double à la fois Shikamaru (Naruto) et Baggy le Clown (One Piece), et Stéphane Excoffier intervient également sur ces franchises."
  },
  {
    "query": "Je cherche la maison d'édition française qui publie des chefs-d'œuvre de dark fantasy comme Berserk et des mangas d'action comme Tokyo Ghoul.",
    "expected_id": "2",
    "expected_title": "Glénat",
    "is_architectural": true,
    "query_type": "thematic",
    "ground_truth": "Il s'agit des éditions Glénat, qui publient Berserk de Kentaro Miura et Tokyo Ghoul de Sui Ishida en France."
  },
  {
    "query": "Dans quel magazine prépublie l'auteur original de Monster et de Pluto, et a-t-il reçu des prix majeurs pour ces mangas ?",
    "expected_id": "19",
    "expected_title": "Monster",
    "is_architectural": true,
    "query_type": "cross-media",
    "ground_truth": "L'auteur est Naoki Urasawa. Il prépublie principalement dans des magazines comme Big Comic Original (Monster) et Big Comic Spirits (20th Century Boys). Il a remporté de prestigieuses distinctions comme le Prix culturel Osamu Tezuka et le Shogakukan Manga Award."
  },
  {
    "query": "Trouve-moi le groupe d'anisong légendaire ou le chanteur qui interprète le générique d'ouverture emblématique Guren no Yumiya pour L'Attaque des Titans.",
    "expected_id": "16498",
    "expected_title": "Attack on Titan",
    "is_architectural": true,
    "query_type": "thematic",
    "ground_truth": "L'opening emblématique 'Guren no Yumiya' de L'Attaque des Titans est interprété par le groupe Linked Horizon dirigé par Revo."
  },
  {
    "query": "Quel acteur de doublage japonais (Seiyuu) prête sa voix au charismatique Levi Ackerman dans L'Attaque des Titans et dans Trafalgar Law dans One Piece ?",
    "expected_id": "0",
    "expected_title": "Hiroshi Kamiya",
    "is_architectural": true,
    "query_type": "graph",
    "ground_truth": "L'acteur emblématique est Hiroshi Kamiya, qui prête sa voix à la fois au Caporal Levi dans Shingeki no Kyojin et à Trafalgar Law dans One Piece."
  },
  {
    "query": "Combien de tomes compte le manga original Death Note par rapport à son nombre d'épisodes dans son adaptation animée ?",
    "expected_id": "1535",
    "expected_title": "Death Note",
    "is_architectural": true,
    "query_type": "cross-media",
    "ground_truth": "Le manga original Death Note compte exactement 12 tomes (plus un tome spécial 13) tandis que son adaptation animée par Studio Madhouse comporte exactement 37 épisodes regroupés en une seule saison."
  },
  {
    "query": "Est-ce que le célèbre doubleur français de Guts dans l'anime de 1997 double aussi Son Goku dans la version française de Dragon Ball Z ?",
    "expected_id": "0",
    "expected_title": "None",
    "is_architectural": true,
    "query_type": "negative",
    "ground_truth": "Non, Guts dans la VF de la série Berserk de 1997 est doublé principalement par Emmanuel Gradi, tandis que Son Goku dans Dragon Ball Z est doublé par le comédien historique Patrick Borg."
  },
  {
    "query": "Quels sites de distribution ou plateformes de streaming légal diffusent l'anime Demon Slayer (Kimetsu no Yaiba) en France ?",
    "expected_id": "38000",
    "expected_title": "Demon Slayer",
    "is_architectural": true,
    "query_type": "standard",
    "ground_truth": "En France, l'anime Demon Slayer est distribué légalement sur les plateformes de streaming Crunchyroll et Netflix."
  },
  {
    "query": "Je me souviens d'un anime de comédie romantique récent avec un opening extrêmement populaire sur YouTube chanté par YOASOBI, parlant de la face cachée d'une idol et de ses jumeaux.",
    "expected_id": "0",
    "expected_title": "Oshi no Ko",
    "is_architectural": true,
    "query_type": "thematic",
    "ground_truth": "Il s'agit de l'anime Oshi no Ko, et l'opening ultra-populaire chanté par YOASOBI est intitulé 'Idol'."
  },
  {
    "query": "Le manga Neon Genesis Evangelion a-t-il remporté le Prix culturel Osamu Tezuka dans la catégorie manga en 2020 ?",
    "expected_id": "0",
    "expected_title": "None",
    "is_architectural": true,
    "query_type": "negative",
    "ground_truth": "Non, le manga Neon Genesis Evangelion s'est terminé en 2013 et n'a pas reçu le prix en 2020. En 2020, c'est le manga Nyx no Lantern de Kan Takahama qui a reçu le Grand Prix."
  }
```

- [ ] **Step 2: Commit Task 2**

```bash
git add data/mlops/gold_dataset.json
git commit -m "test: extend RAGAS gold_dataset.json with 10 new queries"
```

---

### Task 3: Execution and Schema Size Verification

**Files:**
- Test: `backend/pipeline/evaluation/regression_benchmark.py`
- Test: `data/mlops/gold_dataset.json`

- [ ] **Step 1: Verify the JSON schema size**

Run a command to confirm that the `gold_dataset.json` file parses cleanly and contains exactly 30 items:
Run: `.venv\Scripts\python -c "import json; d = json.load(open('data/mlops/gold_dataset.json', encoding='utf-8')); print('Total elements:', len(d)); assert len(d) == 30"`
Expected output: `Total elements: 30`

- [ ] **Step 2: Run a regression benchmark dry-run**

Run the regression benchmark to ensure that all 12 queries execute cleanly and write a new regression report:
Run: `.venv\Scripts\python backend/pipeline/evaluation/regression_benchmark.py`
Expected output:
`🧪 Starting AI Regression Test...`
`...`
`✅ Regression Test Complete.`
`📊 Avg Accuracy: ...`

- [ ] **Step 3: Commit Task 3**

```bash
git commit --allow-empty -m "test: verify Gold Set and Gold Dataset upgrade execution and size"
```
