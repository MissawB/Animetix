# DPO Subtle Tonal Corruption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subtilize the tonal corruption strategy in the DPO preference dataset compiler by replacing the simplistic punctuation/casing stripping with three probabilistic sub-strategies: excessive code-switching, excessive redundancy, and condescending/pedantic tone.

**Architecture:** Modify `corrupt_tonal_deviation` in `dpo_dataset_compiler.py` to randomly delegate to one of the three strategies per example, and update `test_dpo_dataset_compiler.py` to assert correct behavior.

**Tech Stack:** Python 3.12, unittest, regex

---

### Task 1: Update corrupt_tonal_deviation in dpo_dataset_compiler.py

**Files:**
- Modify: `backend/pipeline/mlops/dpo_dataset_compiler.py:327-362`

- [ ] **Step 1: Replace corrupt_tonal_deviation with the new subtle implementation**

Update `corrupt_tonal_deviation` to contain:
```python
def corrupt_tonal_deviation(text: str, language: str = "Français") -> str:
    """
    Dégrade le ton en choisissant aléatoirement l'un des trois types de corruption :
    1. Code-switching excessif (mélange fr/en ou en/jp non naturel)
    2. Redondance excessive (répétitions de propositions ou de phrases)
    3. Ton condescendant (ajouts de formules hautaines et pédantes)
    """
    strategy = random.choice(["code_switching", "redundancy", "condescending"])

    if strategy == "code_switching":
        if language == "Français":
            swaps = {
                r"\bpersonnages?\b": lambda m: "characters" if m.group(0).endswith("s") else "character",
                r"\bréalisateurs?\b": lambda m: "directors" if m.group(0).endswith("s") else "director",
                r"\bdirecteurs?\b": lambda m: "directors" if m.group(0).endswith("s") else "director",
                r"\bhistoire\b": "plotline",
                r"\bscénario\b": "storyline",
                r"\bchef-d'œuvre\b": "masterpiece",
                r"\bchefs-d'œuvre\b": "masterpieces",
                r"\bépisodes?\b": lambda m: "episodes" if m.group(0).endswith("s") else "episode",
                r"\bséries?\b": lambda m: "shows" if m.group(0).endswith("s") else "show",
                r"\banimation\b": "art style",
                r"\bdessins?\b": "art style",
                r"\bdiffusés?\b": "released",
                r"\bsortis?\b": "released",
                r"\béditeurs?\b": "publisher",
                r"\bédités?\b": "published",
            }
            for pattern, replacement in swaps.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
            prependers = ["Basically, ", "Honestly, ", "Anyway, "]
            appenders = [", which is totally fine.", ", literally.", ", fr fr.", ", actually."]
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)
        else:
            swaps_en = {
                r"\bcharacters?\b": "chara",
                r"\bmasterpiece\b": "kami-sama tier masterpiece",
                r"\bfriends?\b": "nakama",
                r"\bprotagonists?\b": "MC",
                r"\bheros?\b": "MC",
                r"\banimation\b": "sakuga",
            }
            for pattern, replacement in swaps_en.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
            prependers = ["So, basically, ", "Like, honestly, "]
            appenders = [", which is fine.", ", literally.", ", fr fr."]
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)

    elif strategy == "redundancy":
        prependers = ["Pour ce qui est de ce sujet, et afin de préciser les choses de manière très précise, "]
        appenders = [
            ", et comme je l'ai déjà expliqué et mentionné précédemment dans mon explication à ce sujet, c'est tout à fait cela.",
            ", ce qui signifie et veut dire exactement ce que cela signifie."
        ]
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            idx = random.randint(0, len(sentences) - 1)
            target = sentences[idx].rstrip(".!? ")
            if target:
                dup = f"Je répète donc que {target[0].lower() + target[1:]}."
                sentences.insert(idx + 1, dup)
            text = " ".join(sentences)
        else:
            text = random.choice(prependers) + text[0].lower() + text[1:]
            text = text.rstrip(".") + random.choice(appenders)

    elif strategy == "condescending":
        prependers = [
            "C'est pourtant évident, et tout otaku digne de ce nom devrait le savoir : ",
            "Franchement, il est élémentaire de comprendre que : ",
            "Pour peu que l'on s'y connaisse un minimum en japanimation, on sait bien que : ",
            "C'est une question triviale... Tout le monde sait que : "
        ]
        appenders = [
            " Mais bon, il faut avoir un minimum de culture pour s'en rendre compte.",
            " C'est pourtant la base.",
            " (Enfin, si tant est que tu puisses comprendre cela)."
        ]
        inlines = [
            ", comme n'importe quel amateur de base l'aurait compris,",
            ", ce qui va de soi pour n'importe qui de cultivé,",
            ", bien que les néophytes en doutent,"
        ]
        if "," in text:
            parts = text.split(",", 1)
            text = parts[0] + random.choice(inlines) + parts[1]
        else:
            words = text.split()
            if len(words) > 4:
                words.insert(4, random.choice(inlines).strip())
                text = " ".join(words)
        
        text = random.choice(prependers) + text[0].lower() + text[1:]
        text = text.rstrip(".") + random.choice(appenders)

    return text.strip()
```

- [ ] **Step 2: Commit changes**

```bash
git add backend/pipeline/mlops/dpo_dataset_compiler.py
git commit -m "feat: implement subtle tonal corruption strategies for DPO"
```

---

### Task 2: Update unit tests in test_dpo_dataset_compiler.py

**Files:**
- Modify: `tests/mlops/test_dpo_dataset_compiler.py:44-56`

- [ ] **Step 1: Replace test_corrupt_tonal_deviation with the new multi-strategy test**

Update `test_corrupt_tonal_deviation` in `test_dpo_dataset_compiler.py` to:
```python
    def test_corrupt_tonal_deviation(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_tonal_deviation
        
        text = "Cet anime est un chef-d'œuvre avec d'excellents personnages. C'est incroyable !"
        
        strategies_seen = {
            "code_switching": False,
            "redundancy": False,
            "condescending": False
        }
        
        for _ in range(50):
            corr = corrupt_tonal_deviation(text, "Français")
            # 1. Code-switching check
            if "masterpiece" in corr or "character" in corr or "basically" in corr.lower():
                strategies_seen["code_switching"] = True
            # 2. Redundancy check
            if "préciser" in corr or "explication" in corr or "répète" in corr.lower():
                strategies_seen["redundancy"] = True
            # 3. Condescending check
            if "évident" in corr or "otaku" in corr or "Franchement" in corr or "triviale" in corr:
                strategies_seen["condescending"] = True
                
        self.assertTrue(strategies_seen["code_switching"], "Code-switching strategy was not triggered")
        self.assertTrue(strategies_seen["redundancy"], "Redundancy strategy was not triggered")
        self.assertTrue(strategies_seen["condescending"], "Condescending strategy was not triggered")
```

- [ ] **Step 2: Run pytest to verify all tests pass**

Run: `.venv\Scripts\pytest tests/mlops`
Expected: 33 passed

- [ ] **Step 3: Commit changes**

```bash
git add tests/mlops/test_dpo_dataset_compiler.py
git commit -m "test: update tonal corruption assertions for subtle strategies"
```
