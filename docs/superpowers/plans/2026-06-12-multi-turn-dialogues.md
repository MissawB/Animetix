# Multi-Turn Dialogues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate multi-turn dialogue scenarios representing ~15-20% of the SFT dataset, allowing the expert model to follow conversation context over multiple turns in French and English.

**Architecture:** Extend the dataset schema to support a `turns` key. Update the compilation logic in `finetuning_dataset.py` to procedurally generate multi-turn conversations and update `train_expert_model.py` to format them into ChatML sequential turns.

**Tech Stack:** Python 3.12, Pytest 9.0.

---

### Task 1: Update Deduplication in SFT Compiler

**Files:**
- Modify: `backend/pipeline/mlops/finetuning_dataset.py`
- Test: `tests/mlops/test_finetuning_dataset.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/mlops/test_finetuning_dataset.py`:
```python
    def test_deduplicate_dataset_multiturn(self):
        from backend.pipeline.mlops.finetuning_dataset import deduplicate_dataset
        dataset = [
            {
                "turns": [{"user": "Hi", "assistant": "Hello"}],
                "language": "English"
            },
            {
                "turns": [{"user": "Hi", "assistant": "Hello"}],
                "language": "English"
            },
            {
                "instruction": "Hi",
                "input": "",
                "output": "Hello",
                "language": "English"
            }
        ]
        res = deduplicate_dataset(dataset)
        self.assertEqual(len(res), 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_deduplicate_dataset_multiturn -v`
Expected: FAIL (KeyError or list does not equal 2)

- [ ] **Step 3: Write minimal implementation**

In `backend/pipeline/mlops/finetuning_dataset.py`, modify `deduplicate_dataset`:
```python
def deduplicate_dataset(dataset):
    seen = set()
    deduped = []
    duplicates_count = 0
    for item in dataset:
        if "turns" in item:
            sig_list = []
            for t in item["turns"]:
                sig_list.append(t["user"].strip())
                sig_list.append(t["assistant"].strip())
            key = tuple(sig_list)
        else:
            key = (item["instruction"].strip(), item.get("input", "").strip())
            
        if key in seen:
            duplicates_count += 1
            continue
        seen.add(key)
        deduped.append(item)
    logger.info(f"[INFO] Deduplication removed {duplicates_count} duplicate SFT pairs.")
    return deduped
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_deduplicate_dataset_multiturn -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/finetuning_dataset.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat: add multi-turn support to SFT compiler deduplication"
```

---

### Task 2: Implement Dynamic Dialogues Generator

**Files:**
- Modify: `backend/pipeline/mlops/finetuning_dataset.py`
- Test: `tests/mlops/test_finetuning_dataset.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/mlops/test_finetuning_dataset.py`:
```python
    def test_generate_multiturn_dialogues(self):
        from backend.pipeline.mlops.finetuning_dataset import generate_multiturn_dialogues
        animes = [{"title": "Naruto", "genres": ["Action"], "studios": ["Pierrot"], "tags": ["Ninja"], "popularity": 1000000, "year": 2002}]
        mangas = [{"title": "One Piece", "genres": ["Adventure"], "tags": ["Pirates"], "popularity": 1500000}]
        chars = [{"name": "Luffy", "origin": "One Piece", "entities": {"organizations": ["Straw Hats"]}, "popularity": {"favourites": 150000, "rank": 1}, "metadata": {"height": "174cm"}}]
        vocab = {"Tsundere": {"definition": "Cold then hot", "examples": "Taiga", "impact": "Popular trope", "origin": "Japanese"}}
        
        dialogues = generate_multiturn_dialogues(animes, mangas, chars, vocab, count=6)
        self.assertEqual(len(dialogues), 6)
        for d in dialogues:
            self.assertIn("turns", d)
            self.assertGreaterEqual(len(d["turns"]), 2)
            self.assertIn(d["language"], ["Français", "English"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_generate_multiturn_dialogues -v`
Expected: FAIL (ImportError or AttributeError: NameError: name 'generate_multiturn_dialogues' is not defined)

- [ ] **Step 3: Write minimal implementation**

In `backend/pipeline/mlops/finetuning_dataset.py`, add `generate_multiturn_dialogues`:
```python
def generate_multiturn_dialogues(animes, mangas, characters, otaku_vocab, count=1000) -> List[dict]:
    """
    Génère procéduralement des dialogues multi-tours à partir des bases de données locales.
    """
    dialogues = []
    
    # Templates de questions/réponses en Français
    fr_anime_templates = [
        {
            "t1": "Salut ! Tu as un bon anime de {genre} à me conseiller ?",
            "t2": "Ah super. Et c'est quel studio qui l'a produit, et en quelle année ?",
            "t3": "Génial, merci. Et quelles sont les thématiques principales abordées ?"
        }
    ]
    # Templates de questions/réponses en Anglais
    en_anime_templates = [
        {
            "t1": "Hi! Can you recommend a good {genre} anime?",
            "t2": "Awesome. Which studio produced it, and in what year was it released?",
            "t3": "Thanks! What are the primary themes in this anime?"
        }
    ]
    
    fr_char_templates = [
        {
            "t1": "Qui est le personnage {name} ?",
            "t2": "D'accord, et à quel groupe ou faction appartient-il ?",
            "t3": "Quelle est sa taille officielle et est-il populaire ?"
        }
    ]
    en_char_templates = [
        {
            "t1": "Who is the character {name}?",
            "t2": "Understood, and which group or faction do they belong to?",
            "t3": "What is their official height and are they popular?"
        }
    ]
    
    fr_vocab_templates = [
        {
            "t1": "Peux-tu m'expliquer le concept otaku de '{term}' ?",
            "t2": "Quels sont des exemples connus qui illustrent ce trope ?",
            "t3": "D'où vient ce terme et quel est son impact sur l'écriture ?"
        }
    ]
    en_vocab_templates = [
        {
            "t1": "Can you explain the otaku concept of '{term}'?",
            "t2": "What are some well-known examples illustrating this trope?",
            "t3": "Where does this term come from and what is its writing impact?"
        }
    ]

    for idx in range(count):
        lang = "English" if idx % 2 == 1 else "Français"
        scenario = idx % 3
        
        if scenario == 0 and animes:
            # Anime / Manga exploration dialogue
            anime = random.choice(animes)
            title = anime.get("title", "Unknown")
            display_title = get_display_title(title)
            genres = anime.get("genres", ["Action"])
            genre = random.choice(genres) if genres else "Action"
            studios = anime.get("studios", ["Pierrot"])
            studio_str = ", ".join(studios)
            year = anime.get("year", 2002)
            tags = anime.get("tags", [])
            tags_str = ", ".join(clean_tags(tags, lang)[:4])
            
            if lang == "English":
                p_text = make_english_anime_profile(title, genres, studios, tags, year)
                t = en_anime_templates[0]
                turns = [
                    {"user": t["t1"].format(genre=genre), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"This anime was produced by the studio {studio_str} and released in {year}."},
                    {"user": t["t3"], "assistant": f"In '{display_title}', the primary themes explored are: {tags_str}."}
                ]
            else:
                p_text = make_french_anime_profile(title, genres, studios, tags, year)
                t = fr_anime_templates[0]
                turns = [
                    {"user": t["t1"].format(genre=genre), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"Cet anime a été produit par le studio {studio_str} et est sorti en {year}."},
                    {"user": t["t3"], "assistant": f"Dans '{display_title}', les thématiques principales abordées sont : {tags_str}."}
                ]
                
        elif scenario == 1 and characters:
            # Character dialogue
            char = random.choice(characters)
            name = char.get("name", "Unknown")
            display_name = get_display_character(name)
            origin = char.get("origin", "Unknown")
            display_origin = get_display_title(origin)
            ents = char.get("entities", {})
            orgs = ents.get("organizations", []) if isinstance(ents, dict) else []
            orgs_str = ", ".join(orgs) if orgs else "several groups"
            favs = char.get("popularity", {}).get("favourites", 0) if isinstance(char.get("popularity"), dict) else 0
            rank = char.get("popularity", {}).get("rank", 999) if isinstance(char.get("popularity"), dict) else 999
            height = char.get("metadata", {}).get("height", "Unknown") if isinstance(char.get("metadata"), dict) else "Unknown"
            
            if lang == "English":
                p_text = make_english_character_bio(name, origin, orgs, favs, rank, height)
                t = en_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"They are primarily known for their affiliation with: {orgs_str}."},
                    {"user": t["t3"], "assistant": f"Their official height is {height}. They are ranked #{rank} in popularity with {favs:,} favourites."}
                ]
            else:
                p_text = make_french_character_bio(name, origin, orgs, favs, rank, height)
                t = fr_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {"user": t["t2"], "assistant": f"Il est principalement connu pour son affiliation avec : {orgs_str}."},
                    {"user": t["t3"], "assistant": f"Sa taille officielle est {height}. Il est classé au rang #{rank} des favoris avec {favs} votes d'admiration."}
                ]
                
        else:
            # Otaku concept dialogue
            vocab_list = list(otaku_vocab.keys())
            term = random.choice(vocab_list) if vocab_list else "Tsundere"
            data = otaku_vocab.get(term, {"definition": "trope", "examples": "Taiga", "impact": "popular", "origin": "Japan"})
            
            if lang == "English":
                t = en_vocab_templates[0]
                turns = [
                    {"user": t["t1"].format(term=term), "assistant": f"In otaku culture, '{term}' refers to: {data['definition']}."},
                    {"user": t["t2"], "assistant": f"Iconic examples illustrating this concept include: {data['examples']}."},
                    {"user": t["t3"], "assistant": f"Origin: {data['origin']}. Narrative impact: {data['impact']}."}
                ]
            else:
                t = fr_vocab_templates[0]
                turns = [
                    {"user": t["t1"].format(term=term), "assistant": f"Dans la culture otaku, '{term}' désigne : {data['definition']}."},
                    {"user": t["t2"], "assistant": f"Parmi les exemples emblématiques illustrant ce concept, on peut citer : {data['examples']}."},
                    {"user": t["t3"], "assistant": f"Origine : {data['origin']}. Impact narratif : {data['impact']}."}
                ]
                
        dialogues.append({
            "turns": turns,
            "language": lang
        })
        
    return dialogues
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_generate_multiturn_dialogues -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/finetuning_dataset.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat: add generate_multiturn_dialogues to SFT compiler"
```

---

### Task 3: Integrate Multi-Turn Dialogues into SFT Compiler Loop

**Files:**
- Modify: `backend/pipeline/mlops/finetuning_dataset.py`
- Test: `tests/mlops/test_finetuning_dataset.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/mlops/test_finetuning_dataset.py`:
```python
    def test_run_generate_instruction_dataset_contains_multiturn(self):
        # We verify that compilation produces multi-turn examples
        from backend.pipeline.mlops.finetuning_dataset import OUTPUT_DATASET
        import json
        
        # Verify output exists (it is created by run_generate_instruction_dataset during suite execution)
        if os.path.exists(OUTPUT_DATASET):
            multiturn_found = False
            with open(OUTPUT_DATASET, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    if "turns" in item:
                        multiturn_found = True
                        break
            self.assertTrue(multiturn_found, "Compilation did not produce multi-turn examples")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_run_generate_instruction_dataset_contains_multiturn -v`
Expected: FAIL (no multi-turn examples found)

- [ ] **Step 3: Write minimal implementation**

In `backend/pipeline/mlops/finetuning_dataset.py`, modify `run_generate_instruction_dataset` to integrate ~15-20% multi-turn examples:
```python
    # After deduplication of specialized_data (around line 1593)
    specialized_data = deduplicate_dataset(specialized_data)
    for item in specialized_data:
        if "language" not in item:
            item["language"] = "Français"

    non_meta_count = len(specialized_data)
    
    # Generate Multi-Turn dialogues to represent 15% of the SFT dataset
    # target = (specialized + meta + general + multiturn)
    # specialized + meta + general = 85%
    # target * 0.15 = multiturn_required
    multiturn_required = int(non_meta_count * 0.18) # 18% of non_meta count is roughly 15% of total
    logger.info(f"[INFO] Generating {multiturn_required} multi-turn dialogue examples...")
    
    # Load raw databases for generator
    animes_list = []
    if os.path.exists(ANIME_DB):
        with open(ANIME_DB, 'r', encoding='utf-8') as f:
            animes_list = json.load(f)
            
    mangas_list = []
    if os.path.exists(MANGA_DB):
        with open(MANGA_DB, 'r', encoding='utf-8') as f:
            mangas_list = json.load(f)
            
    chars_list = []
    if os.path.exists(CHAR_DB):
        with open(CHAR_DB, 'r', encoding='utf-8') as f:
            chars_list = json.load(f)
            
    multiturn_dialogues = generate_multiturn_dialogues(animes_list, mangas_list, chars_list, OTAKU_VOCABULARY, count=multiturn_required)
    multiturn_dialogues = deduplicate_dataset(multiturn_dialogues)
```
And add them to the unified assemblage list (around line 1645):
```python
    # Assemblage unifié
    final_dataset = []
    final_dataset.extend(specialized_data)
    final_dataset.extend(selected_meta)
    final_dataset.extend(general_data)
    final_dataset.extend(multiturn_dialogues)
```
And log the ratio check (around line 1667):
```python
    logger.info(f"  - Specialized, Bridges & French Market (80% target): {len(specialized_data)} / {total_count} ({actual_spec_ratio:.2f}%)")
    logger.info(f"  - Otaku Meta-Vocabulary (5% target): {len(selected_meta)} / {total_count} ({actual_meta_ratio:.2f}%)")
    logger.info(f"  - General French SFT (15% target): {len(general_data)} / {total_count} ({actual_gen_ratio:.2f}%)")
    logger.info(f"  - Multi-Turn Dialogues (15-20% target): {len(multiturn_dialogues)} / {total_count} ({len(multiturn_dialogues)/total_count*100:.2f}%)")
```

- [ ] **Step 4: Run test to verify it passes**

First, run the generator script to compile the new dataset:
`.venv\Scripts\python backend/pipeline/mlops/finetuning_dataset.py`

Then, run: `.venv\Scripts\pytest tests/mlops/test_finetuning_dataset.py -k test_run_generate_instruction_dataset_contains_multiturn -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/finetuning_dataset.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat: integrate multi-turn dialogues into compiler output"
```

---

### Task 4: Support Multi-Turn Format in Trainer ChatML Formatting

**Files:**
- Modify: `backend/pipeline/mlops/train_expert_model.py`
- Test: `tests/mlops/test_train_expert_model.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/mlops/test_train_expert_model.py`:
```python
    def test_format_chatml_messages_multiturn(self):
        item = {
            "turns": [
                {"user": "Salut ! Tu as un bon anime de combats ?", "assistant": "Bonjour ! Oui, je te recommande 'Naruto'..."},
                {"user": "Et c'est quel studio ?", "assistant": "Il a été produit par Pierrot."}
            ],
            "language": "Français"
        }
        messages = format_chatml_messages(item)
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Salut ! Tu as un bon anime de combats ?")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["content"], "Bonjour ! Oui, je te recommande 'Naruto'...")
        self.assertEqual(messages[3]["role"], "user")
        self.assertEqual(messages[4]["role"], "assistant")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\pytest tests/mlops/test_train_expert_model.py -k test_format_chatml_messages_multiturn -v`
Expected: FAIL (KeyError: 'instruction')

- [ ] **Step 3: Write minimal implementation**

In `backend/pipeline/mlops/train_expert_model.py`, modify `format_chatml_messages`:
```python
def format_chatml_messages(item) -> list:
    """
    Formate les messages au format ChatML selon la langue du dataset.
    Supporte le mono-tour et le multi-tours.
    """
    language = item.get("language", "Français")
    if language == "English":
        system_prompt = "You are Animetix, an absolute expert in otaku culture, Japanese manga, and anime. You answer in a very comprehensive and precise manner in English."
    else:
        system_prompt = "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des animés japonais. Tu réponds de manière très complète et précise en français."
        
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    if "turns" in item:
        for turn in item["turns"]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
    else:
        user_content = item["instruction"]
        if item.get("input"):
            if language == "English":
                user_content = f"{item['instruction']}\n\nContext: {item['input']}"
            else:
                user_content = f"{item['instruction']}\n\nContexte : {item['input']}"
        messages.append({"role": "user", "content": user_content})
        messages.append({"role": "assistant", "content": item["output"]})
        
    return messages
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\pytest tests/mlops/test_train_expert_model.py -k test_format_chatml_messages_multiturn -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/train_expert_model.py tests/mlops/test_train_expert_model.py
git commit -m "feat: support multi-turn messages in ChatML trainer formatter"
```
