# Otaku Dataset Sanitation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Régénérer `MissawB/otaku-expert-dataset` en ancrant les réponses dans les vrais champs `description`/`biography` du source data, en purgeant les slots numériques non-conditionnés et en supprimant la mémorisation de forme byte-identique — de façon déterministe (zéro appel LLM), sans réentraîner.

**Architecture:** On réécrit les constructeurs de profils/bios (`profile_builders.py`) pour qu'ils consomment le texte source réel (EN : synopsis complet ; FR : faits structurés honnêtes), on ajoute un nettoyeur de prose source (`text_cleaning.py`), on modifie la boucle d'émission (`finetuning_dataset.py`) pour passer ce texte et n'émettre que des sorties distinctes, et on ajoute une suite de validation qui prouve l'absence des motifs corrupteurs.

**Tech Stack:** Python 3.10+, `pytest`/`unittest`, `datasets` (HF), `hf` CLI pour l'upload.

## Global Constraints

- **Zéro appel LLM** dans le chemin de génération du volume (augmentation Gemini reste inerte par défaut). Copié du spec : « Ancrage déterministe, gratuit ».
- **Seule l'année (`year`) est un nombre autorisé** en sortie. Aucun `rank`, `favs`, compteur de votes, ou nombre non dérivable de la question.
- **FR structuré / EN synopsis complet** : les réponses FR ne contiennent pas de synopsis (pas de traduction) ; les réponses EN intègrent le synopsis réel nettoyé.
- **Aucune sortie identique** ne doit être associée à deux instructions différentes.
- **Encodage** : tous les fichiers `.py`/`.jsonl` en UTF-8. Sous Windows, éditer les fichiers non-ASCII via l'outil Edit (pas `Get-Content -Raw` sans `-Encoding UTF8`).
- **Exécution des tests (worktree)** : lancer via le python du `.venv` de `main` (voir la commande exacte en tête de Task 1), le worktree n'a pas de venv propre.
- Périmètre : **dataset seulement**. Pas de `hf jobs`, pas de re-service.

---

## File Structure

- `backend/pipeline/mlops/ft_dataset/text_cleaning.py` — ajout de `clean_source_prose()`.
- `backend/pipeline/mlops/ft_dataset/profile_builders.py` — réécriture des 6 constructeurs `make_*`.
- `backend/pipeline/mlops/finetuning_dataset.py` — boucles anime/manga/personnages : passer le texte source, émettre des sorties distinctes.
- `tests/mlops/test_finetuning_dataset.py` — mise à jour des attentes obsolètes (numériques, comptes de variations).
- `tests/mlops/test_source_prose_cleaning.py` — **nouveau**, unitaire pour `clean_source_prose`.
- `tests/mlops/test_dataset_sanitation.py` — **nouveau**, suite de garde-fous anti-corruption sur un dataset généré.

**Commande de test de référence** (worktree → venv de main) :

```bash
MAIN=/c/Users/bahma/PycharmProjects/Projet\ solo/Double_scenario_Project
PY="$MAIN/.venv/Scripts/python.exe"
cd backend && "$PY" -m pytest ../tests/mlops/<file>.py -v
```

Si `$PY` n'existe pas, se rabattre sur `python` du PATH. Toutes les commandes `pytest` ci-dessous supposent le CWD `backend/` (c'est là que `pipeline.mlops...` est importable, cf. `sys.path.insert(0, BASE_DIR)` dans les tests existants).

---

### Task 1: Nettoyeur de prose source (`clean_source_prose`)

Transforme une `description`/`biography` AniList brute en texte factuel propre et borné, prêt à être inséré dans une réponse EN.

**Files:**
- Modify: `backend/pipeline/mlops/ft_dataset/text_cleaning.py`
- Test: `tests/mlops/test_source_prose_cleaning.py` (create)

**Interfaces:**
- Produces: `clean_source_prose(text: str, max_chars: int = 1200) -> str`
  - `""`/`None` → `""`.
  - Décode entités HTML, retire balises HTML, retire le markup spoiler AniList `~!…!~` en **gardant** le texte interne, retire le caractère de remplacement `�` (U+FFFD), normalise les espaces.
  - Tronque à `max_chars` sur la dernière frontière de phrase (`.`/`!`/`?`) ≤ `max_chars` ; sinon coupe dur à `max_chars`.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/mlops/test_source_prose_cleaning.py` :

```python
# -*- coding: utf-8 -*-
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from pipeline.mlops.ft_dataset.text_cleaning import clean_source_prose  # noqa: E402


class TestCleanSourceProse(unittest.TestCase):
    def test_empty_and_none(self):
        self.assertEqual(clean_source_prose(""), "")
        self.assertEqual(clean_source_prose(None), "")

    def test_strips_html_and_entities(self):
        raw = "Denji is a <i>Devil Hunter</i>.<br>He merges &amp; fights."
        out = clean_source_prose(raw)
        self.assertNotIn("<", out)
        self.assertIn("Denji is a Devil Hunter.", out)
        self.assertIn("merges & fights", out)

    def test_keeps_spoiler_inner_text_drops_markers(self):
        raw = "Tanjiro fights ~!the demon king Muzan!~ in the finale."
        out = clean_source_prose(raw)
        self.assertNotIn("~!", out)
        self.assertNotIn("!~", out)
        self.assertIn("the demon king Muzan", out)

    def test_removes_replacement_char(self):
        raw = "resolves to become a �demon slayer� so that he can"
        out = clean_source_prose(raw)
        self.assertNotIn("�", out)
        self.assertIn("demon slayer", out)

    def test_collapses_whitespace(self):
        self.assertEqual(clean_source_prose("a   b\n\nc"), "a b c")

    def test_truncates_on_sentence_boundary(self):
        text = ("Sentence one is here. " * 100).strip()  # ~2200 chars
        out = clean_source_prose(text, max_chars=100)
        self.assertLessEqual(len(out), 100)
        self.assertTrue(out.endswith("."))

    def test_hard_cut_when_no_boundary(self):
        text = "x" * 500
        out = clean_source_prose(text, max_chars=100)
        self.assertEqual(len(out), 100)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_source_prose_cleaning.py -v`
Expected: FAIL — `ImportError: cannot import name 'clean_source_prose'`.

- [ ] **Step 3: Implémenter**

Ajouter dans `text_cleaning.py` (après `clean_description`) :

```python
def clean_source_prose(text: str, max_chars: int = 1200) -> str:
    """Nettoie une description/biographie AniList brute pour ancrage factuel EN.

    - décode les entités HTML, retire les balises HTML ;
    - retire le markup spoiler AniList ``~!...!~`` en gardant le texte interne ;
    - retire le caractère de remplacement U+FFFD (données déjà perdues) ;
    - normalise les espaces ;
    - tronque sur une frontière de phrase <= ``max_chars`` (sinon coupe dure).
    """
    if not text:
        return ""
    text = html.unescape(text)
    # Markup spoiler AniList : on garde le contenu, on retire les marqueurs.
    text = text.replace("~!", " ").replace("!~", " ")
    # Balises HTML.
    text = re.sub(r"</?[a-zA-Z]+(?:\s+[^>]*)?>", " ", text)
    # Caractère de remplacement : contenu irrécupérable, on le retire.
    text = text.replace("�", " ")
    # Espaces.
    text = re.sub(r"\s+", " ", text).strip()
    # Les balises/spoilers retirés laissent parfois un espace avant la ponctuation
    # ("Hunter ." ) — on le referme.
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    boundary = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
    if boundary != -1:
        return window[: boundary + 1].strip()
    return window
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_source_prose_cleaning.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/ft_dataset/text_cleaning.py tests/mlops/test_source_prose_cleaning.py
git commit -m "feat(ft_dataset): add clean_source_prose for grounded EN answers"
```

---

### Task 2: Bio de personnage EN ancrée dans la biographie

`make_english_character_bio` intègre la vraie `biography` et **supprime** `favs`/`rank`/`height`.

**Files:**
- Modify: `backend/pipeline/mlops/ft_dataset/profile_builders.py`
- Test: `tests/mlops/test_finetuning_dataset.py` (update `test_bilingual_generators`)

**Interfaces:**
- Consumes: `clean_source_prose` (Task 1), `get_character_synonyms_string`, `get_synonyms_string` (existants).
- Produces: `make_english_character_bio(name, origin, orgs, biography) -> str`
  - Amorce variée nom+origine ; corps = `biography` nettoyée ; mention des `orgs` si présentes ; **aucun** nombre.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `tests/mlops/test_finetuning_dataset.py`, remplacer le bloc `# Test character bio` de `test_bilingual_generators` (lignes ~131-139) par :

```python
        # Test character bio — grounded in real biography, no numeric noise
        char_bio = make_english_character_bio(
            "Luffy",
            "One Piece",
            ["Straw Hats"],
            "Luffy is a rubber-bodied pirate who dreams of becoming Pirate King.",
        )
        self.assertIn("Luffy", char_bio)
        self.assertIn("One Piece", char_bio)
        self.assertIn("Straw Hats", char_bio)
        self.assertIn("Pirate King", char_bio)  # real fact from biography
        self.assertNotIn("rank", char_bio.lower())
        self.assertNotIn("votes", char_bio.lower())
        # No free-floating digit runs (years would be OK, but this bio has none)
        import re as _re
        self.assertIsNone(_re.search(r"\d{3,}", char_bio))
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_bilingual_generators -v`
Expected: FAIL — `TypeError` (signature à 6 args) ou assertion sur `Pirate King`.

- [ ] **Step 3: Implémenter**

Remplacer `make_english_character_bio` dans `profile_builders.py` par :

```python
_EN_CHAR_LEADINS = [
    "{name}{syns} is a character from '{origin}'{osyns}.",
    "{name}{syns} appears in '{origin}'{osyns}.",
    "In '{origin}'{osyns}, {name}{syns} is one of the cast.",
    "Meet {name}{syns}, from the series '{origin}'{osyns}.",
    "{name}{syns} belongs to the world of '{origin}'{osyns}.",
    "Here is {name}{syns}, a figure of '{origin}'{osyns}.",
]


def make_english_character_bio(name, origin, orgs, biography):
    syns = get_character_synonyms_string(name, "English")
    origin_syns = get_synonyms_string(origin, "English")
    lead = random.choice(_EN_CHAR_LEADINS).format(
        name=name, syns=syns, origin=origin, osyns=origin_syns
    )
    parts = [lead]
    if orgs:
        org_str = " and ".join(orgs)
        parts.append(f"They are affiliated with {org_str}.")
    bio = biography.strip() if biography else ""
    if bio:
        parts.append(bio)
    return " ".join(parts)
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_bilingual_generators -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/ft_dataset/profile_builders.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat(ft_dataset): ground EN character bio in real biography, drop rank/favs/height"
```

---

### Task 3: Bio de personnage FR structurée honnête

`make_french_character_bio` ne rend que des faits structurés (nom, origine, organisations), sans synopsis, sans nombre, sans superlatif universel.

**Files:**
- Modify: `backend/pipeline/mlops/ft_dataset/profile_builders.py`
- Modify: `backend/pipeline/mlops/ft_dataset/dialogue_generators.py` (2e site d'appel — voir Step 6)
- Test: `tests/mlops/test_finetuning_dataset.py` (ajouter `test_french_character_bio_structured`)

**Interfaces:**
- Produces: `make_french_character_bio(name, origin, orgs) -> str` (le mapping FR des organisations est conservé.)

> **Découvert en exécution (Task 2 review) :** `dialogue_generators.py` est un 2e consommateur des builders. Le changement de signature casse aussi la branche FR (ligne ~174), et ce fichier injecte le même bruit numérique (`#{rank}` / `{favs} votes d'admiration`, ligne ~186). Cette tâche doit donc AUSSI corriger la branche FR de `dialogue_generators.py` (Step 6). La branche EN a déjà été traitée en Task 2.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter dans `TestFinetuningDataset` :

```python
    def test_french_character_bio_structured(self):
        from pipeline.mlops.finetuning_dataset import make_french_character_bio

        bio = make_french_character_bio("Levi", "Shingeki no Kyojin", ["Survey Corps"])
        self.assertIn("Levi", bio)
        self.assertIn("Shingeki no Kyojin", bio)
        # organisation traduite via le mapping conservé
        self.assertIn("Bataillon d'exploration", bio)
        # motifs corrupteurs bannis
        for banned in [
            "jouit d'une immense popularité",
            "figure incontournable",
            "rang numéro",
            "votes d'admiration",
            "incarne les valeurs",
        ]:
            self.assertNotIn(banned, bio)
        import re as _re
        self.assertIsNone(_re.search(r"\d{3,}", bio))
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_french_character_bio_structured -v`
Expected: FAIL — `TypeError` (signature à 6 args) ou motif banni présent.

- [ ] **Step 3: Implémenter**

Remplacer `make_french_character_bio`. Conserver la table `org_mapping` existante ; nouvelle logique :

```python
_FR_CHAR_LEADINS = [
    "{name}{syns} est un personnage de l'œuvre '{origin}'{osyns}.",
    "{name}{syns} apparaît dans '{origin}'{osyns}.",
    "Dans '{origin}'{osyns}, on trouve le personnage de {name}{syns}.",
    "{name}{syns} fait partie de l'univers de '{origin}'{osyns}.",
    "Voici {name}{syns}, issu de '{origin}'{osyns}.",
]


def make_french_character_bio(name, origin, orgs):
    org_mapping = {
        "Survey Corps": "le Bataillon d'exploration",
        "Straw Hat Pirates": "l'Équipage du Chapeau de paille",
        "Gotei 13": "le Gotei 13",
        "Akatsuki": "l'organisation criminelle Akatsuki",
        "League of Villains": "la Ligue des Vilains",
        "U.A. High School": "le lycée Yuei (U.A. High School)",
        "Hunter Association": "l'Association des Hunters",
        "Jujutsu High": "l'école d'exorcisme de Tokyo (Jujutsu High)",
        "Demon Slayer Corps": "l'Armée des pourfendeurs de démons",
        "Special Operations Squad": "l'Escouade tactique de Levi",
        "Black Bulls": "la compagnie du Taureau Noir (Black Bulls)",
    }
    french_orgs = [org_mapping.get(o, o) for o in orgs]

    syns = get_character_synonyms_string(name)
    origin_syns = get_synonyms_string(origin)
    lead = random.choice(_FR_CHAR_LEADINS).format(
        name=name, syns=syns, origin=origin, osyns=origin_syns
    )
    parts = [lead]
    if french_orgs:
        org_str = " et ".join(french_orgs)
        parts.append(f"Il est notamment associé à {org_str}.")
    return " ".join(parts)
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_french_character_bio_structured -v`
Expected: PASS.

- [ ] **Step 6: Corriger la branche FR de `dialogue_generators.py`**

Le 2e site d'appel (branche `else` du scénario personnage, ~lignes 173-186) appelle encore `make_french_character_bio(name, origin, orgs, favs, rank, height)` et son 3e tour injecte du bruit numérique. Remplacer le bloc `else:` par (symétrique de la correction EN faite en Task 2) :

```python
            else:
                biography = clean_source_prose(char.get("biography", ""))
                p_text = make_french_character_bio(name, origin, orgs)
                t = fr_char_templates[0]
                turns = [
                    {"user": t["t1"].format(name=display_name), "assistant": p_text},
                    {
                        "user": t["t2"],
                        "assistant": f"Il est principalement connu pour son affiliation avec : {orgs_str}.",
                    },
                ]
```

Le 3e tour (`Sa taille officielle est {height}. Il est classé au rang #{rank}…`) est supprimé. `clean_source_prose` est déjà importé (Task 2 a ajouté l'import). Les vars `favs`/`rank`/`height` peuvent devenir inutilisées après cette tâche — les retirer si le linter les signale.

- [ ] **Step 7: Vérifier les tests de dialogue + commit**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_french_character_bio_structured ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_generate_multiturn_dialogues ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_generate_multiturn_dialogues_complex_scenarios -v`
Expected: PASS.

```bash
git add backend/pipeline/mlops/ft_dataset/profile_builders.py backend/pipeline/mlops/ft_dataset/dialogue_generators.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat(ft_dataset): structured honest FR character bio + FR dialogue fix, purge templated filler"
```

---

### Task 4: Profils anime/manga EN ancrés dans la description

`make_english_anime_profile` / `make_english_manga_profile` prennent la `description` réelle et suppriment les adjectifs-squelette.

**Files:**
- Modify: `backend/pipeline/mlops/ft_dataset/profile_builders.py`
- Test: `tests/mlops/test_finetuning_dataset.py` (update `test_bilingual_generators`)

**Interfaces:**
- Produces:
  - `make_english_anime_profile(title, genres, studios, tags, year, description) -> str`
  - `make_english_manga_profile(title, genres, tags, description) -> str`
  - Amorce variée (nom/type/année/genres réels) + corps = `description`. Repli structuré-seul si `description` vide.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `test_bilingual_generators`, remplacer les blocs anime/manga EN (lignes ~115-129) par :

```python
        # Test anime profile — grounded in real description
        anime_prof = make_english_anime_profile(
            "Naruto",
            ["Action"],
            ["Pierrot"],
            ["Ninja"],
            2002,
            "Naruto Uzumaki is a young ninja seeking recognition and the Hokage title.",
        )
        self.assertIn("Naruto", anime_prof)
        self.assertIn("2002", anime_prof)  # year is the only allowed number
        self.assertIn("Hokage", anime_prof)  # real fact from description
        self.assertNotIn("landmark work", anime_prof)
        self.assertNotIn("highly recommended", anime_prof)

        # Empty description -> structured fallback still names the work + facts
        anime_fallback = make_english_anime_profile(
            "Naruto", ["Action"], ["Pierrot"], ["Ninja"], 2002, ""
        )
        self.assertIn("Naruto", anime_fallback)
        self.assertIn("Pierrot", anime_fallback)

        # Test manga profile — grounded in real description
        manga_prof = make_english_manga_profile(
            "One Piece",
            ["Adventure"],
            ["Pirates"],
            "Monkey D. Luffy sails to find the One Piece treasure.",
        )
        self.assertIn("One Piece", manga_prof)
        self.assertIn("treasure", manga_prof)  # real fact
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_bilingual_generators -v`
Expected: FAIL — `TypeError` (arg `description` manquant).

- [ ] **Step 3: Implémenter**

Remplacer les deux fonctions EN :

```python
_EN_ANIME_LEADINS = [
    "'{title}'{syns} is a {year} anime in the {genres} genre(s).",
    "'{title}'{syns} ({year}) is an anime spanning {genres}.",
    "The anime '{title}'{syns}, released in {year}, falls under {genres}.",
    "Released in {year}, the anime '{title}'{syns} covers {genres}.",
]
_EN_MANGA_LEADINS = [
    "'{title}'{syns} is a manga in the {genres} genre(s).",
    "The manga '{title}'{syns} spans {genres}.",
    "'{title}'{syns} is a manga covering {genres}.",
]


def make_english_anime_profile(title, genres, studios, tags, year, description=""):
    cleaned_genres = clean_tags(genres, "English")
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "various genres"
    studios_str = ", ".join(studios) if studios else "an unspecified studio"
    syns = get_synonyms_string(title, "English")
    lead = random.choice(_EN_ANIME_LEADINS).format(
        title=title, syns=syns, year=year, genres=genres_str
    )
    parts = [lead, f"It was produced by {studios_str}."]
    body = (description or "").strip()
    if body:
        parts.append(body)
    return " ".join(parts)


def make_english_manga_profile(title, genres, tags, description=""):
    cleaned_genres = clean_tags(genres, "English")
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "various genres"
    syns = get_synonyms_string(title, "English")
    lead = random.choice(_EN_MANGA_LEADINS).format(
        title=title, syns=syns, genres=genres_str
    )
    parts = [lead]
    body = (description or "").strip()
    if body:
        parts.append(body)
    return " ".join(parts)
```

Ajouter `from .text_cleaning import clean_tags` → déjà importé (ligne 12). Aucun import supplémentaire requis (`clean_source_prose` est appelé par l'appelant, pas ici).

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_bilingual_generators -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/ft_dataset/profile_builders.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat(ft_dataset): ground EN anime/manga profiles in real description"
```

---

### Task 5: Profils anime/manga FR structurés honnêtes

`make_french_anime_profile` / `make_french_manga_profile` : faits structurés variés, sans superlatif universel, sans synopsis.

**Files:**
- Modify: `backend/pipeline/mlops/ft_dataset/profile_builders.py`
- Test: `tests/mlops/test_finetuning_dataset.py` (ajouter `test_french_profiles_structured`)

**Interfaces:**
- Produces (signatures **inchangées**) :
  - `make_french_anime_profile(title, genres, studios, tags, year) -> str`
  - `make_french_manga_profile(title, genres, tags) -> str`

- [ ] **Step 1: Écrire le test qui échoue**

```python
    def test_french_profiles_structured(self):
        from pipeline.mlops.finetuning_dataset import (
            make_french_anime_profile,
            make_french_manga_profile,
        )

        a = make_french_anime_profile("Naruto", ["Action"], ["Pierrot"], ["Ninja"], 2002)
        self.assertIn("Naruto", a)
        self.assertIn("2002", a)
        self.assertIn("Pierrot", a)
        for banned in ["œuvre marquante de la japanimation", "s'inscrit avec brio", "chef-d'œuvre"]:
            self.assertNotIn(banned, a)

        m = make_french_manga_profile("One Piece", ["Adventure"], ["Pirates"])
        self.assertIn("One Piece", m)
        self.assertNotIn("manga culte", m)
        self.assertNotIn("référence incontournable", m)
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_french_profiles_structured -v`
Expected: FAIL — motifs bannis présents (implémentation actuelle).

- [ ] **Step 3: Implémenter**

Remplacer les deux fonctions FR :

```python
_FR_ANIME_LEADINS = [
    "L'anime '{title}'{syns} est sorti en {year} et relève des genres {genres}.",
    "'{title}'{syns} ({year}) est un anime des genres {genres}.",
    "Sorti en {year}, l'anime '{title}'{syns} appartient aux genres {genres}.",
    "'{title}'{syns} est un anime de {year}, classé dans {genres}.",
]
_FR_MANGA_LEADINS = [
    "'{title}'{syns} est un manga des genres {genres}.",
    "Le manga '{title}'{syns} relève des genres {genres}.",
    "'{title}'{syns} est un manga classé dans {genres}.",
]


def make_french_anime_profile(title, genres, studios, tags, year):
    cleaned_genres = clean_tags(genres)
    cleaned_tags = clean_tags(tags)
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres variés"
    studios_str = ", ".join(studios) if studios else "un studio non précisé"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else ""
    syns = get_synonyms_string(title)
    lead = random.choice(_FR_ANIME_LEADINS).format(
        title=title, syns=syns, year=year, genres=genres_str
    )
    parts = [lead, f"Il a été produit par {studios_str}."]
    if tags_str:
        parts.append(f"Ses thématiques incluent : {tags_str}.")
    return " ".join(parts)


def make_french_manga_profile(title, genres, tags):
    cleaned_genres = clean_tags(genres)
    cleaned_tags = clean_tags(tags)
    genres_str = ", ".join(cleaned_genres) if cleaned_genres else "genres variés"
    tags_str = ", ".join(cleaned_tags[:5]) if cleaned_tags else ""
    syns = get_synonyms_string(title)
    lead = random.choice(_FR_MANGA_LEADINS).format(
        title=title, syns=syns, genres=genres_str
    )
    parts = [lead]
    if tags_str:
        parts.append(f"Ses thématiques incluent : {tags_str}.")
    return " ".join(parts)
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestFinetuningDataset::test_french_profiles_structured -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/mlops/ft_dataset/profile_builders.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat(ft_dataset): structured honest FR anime/manga profiles"
```

---

### Task 6: Boucle d'émission — texte source + sorties distinctes

La boucle `run_generate_instruction_dataset` passe désormais `description`/`biography` aux constructeurs EN et n'émet plus 5 sorties identiques : **1 sortie primaire ancrée par (entité, langue)**, plus des exemples auxiliaires **courts et factuellement distincts** pour les entités populaires.

**Files:**
- Modify: `backend/pipeline/mlops/finetuning_dataset.py` (sections ANIME, MANGA, CHARACTER ; boucles ~404-1235)
- Test: `tests/mlops/test_finetuning_dataset.py` (mettre à jour les intégrations qui comptent les variations)

**Interfaces:**
- Consumes: les 6 `make_*` (Tasks 2-5), `clean_source_prose` (Task 1).
- Produces: comportement d'émission observable — voir attentes de test ci-dessous. Nombre de variations par entité :
  - **Tier-1** : 1 primaire + 2 auxiliaires (courts, faits distincts) = 3.
  - **Tier-2** : 1 primaire + 1 auxiliaire = 2.
  - **Tier-3** : 1 primaire = 1.
  - Chaque sortie d'une même entité doit être **textuellement distincte**.

Les exemples auxiliaires sont **courts et factuels** (donc pas de squelette narratif mémorisable) :
- anime aux1 (studio/année) : Q `"Which studio produced '{t}' and when?"` / `"Quel studio a produit '{t}' et en quelle année ?"` → A `"'{t}' was produced by {studios} and released in {year}."` / `"'{t}' a été produit par {studios} et est sorti en {year}."`
- anime aux2 (genres) : Q `"What genres define '{t}'?"` / `"Quels sont les genres de '{t}' ?"` → A `"'{t}' spans: {genres}."` / `"'{t}' relève des genres : {genres}."`
- manga aux1 (genres) : idem sans studio.
- character aux1 (origine) : Q `"Which work does {name} come from?"` / `"De quelle œuvre vient {name} ?"` → A `"{name} is a character from '{origin}'."` / `"{name} est un personnage de '{origin}'."`

- [ ] **Step 1: Écrire/mettre à jour les tests d'intégration qui échouent**

Dans `TestRunGenerateInstructionDataset.test_integration_happy_path_assembles_all_sections`, remplacer les assertions de comptage (lignes ~899-902) par :

```python
        # Tier-variation counts after sanitation (augmentation off, noise off).
        alpha = [it for it in data if "TestAnimeAlpha" in instr(it)]
        beta = [it for it in data if "TestAnimeBeta" in instr(it)]
        self.assertEqual(len(alpha), 3, "Tier-1 anime -> 1 primary + 2 aux")
        self.assertEqual(len(beta), 1, "Tier-3 anime -> 1 primary only")
        # No two outputs for the same entity are identical.
        alpha_outputs = [it["output"] for it in alpha]
        self.assertEqual(len(alpha_outputs), len(set(alpha_outputs)))
```

Dans `test_augmentation_calls_paraphrase_for_tier1_title`, remplacer `self.assertEqual(paraphrase_mock.call_count, 5)` par :

```python
        # Tier-1 primary profile is the only paraphrase target now (aux are short facts).
        self.assertEqual(paraphrase_mock.call_count, 1)
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset -v`
Expected: FAIL sur les comptages (l'ancien code émet encore 5).

- [ ] **Step 3: Implémenter la section ANIME**

Dans `run_generate_instruction_dataset`, remplacer le corps de la boucle `for idx, item in enumerate(animes):` (la partie qui construit `profile` et appende selon les tiers). Extraire d'abord la description et construire les helpers auxiliaires. Nouvelle structure (remplace tout le bloc `if idx % 2 == 1: ... else: ...` de la section ANIME) :

```python
                description = clean_source_prose(item.get("description", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"
                studios_str = ", ".join(studios) if studios else (
                    "an unspecified studio" if is_en else "un studio non précisé"
                )
                genres_str = ", ".join(clean_tags(genres, lang)) if genres else (
                    "various genres" if is_en else "genres variés"
                )

                if is_en:
                    primary = make_english_anime_profile(
                        title, genres, studios, tags, year, description
                    )
                    q_primary = f"Present the anime '{display_t}' in detail."
                    aux1 = (
                        f"Which studio produced '{display_t}' and when?",
                        f"'{display_t}' was produced by {studios_str} and released in {year}.",
                    )
                    aux2 = (
                        f"What genres define '{display_t}'?",
                        f"'{display_t}' spans: {genres_str}.",
                    )
                else:
                    primary = make_french_anime_profile(title, genres, studios, tags, year)
                    q_primary = f"Présente l'anime '{display_t}' de manière détaillée."
                    aux1 = (
                        f"Quel studio a produit '{display_t}' et en quelle année ?",
                        f"'{display_t}' a été produit par {studios_str} et est sorti en {year}.",
                    )
                    aux2 = (
                        f"Quels sont les genres de '{display_t}' ?",
                        f"'{display_t}' relève des genres : {genres_str}.",
                    )

                if client and title in augmented_anime_titles:
                    primary = paraphrase_text_via_gemini(primary, client, "encyclopédique")

                specialized_data.append(
                    {"instruction": q_primary, "input": "", "output": primary, "language": lang}
                )
                if effective_pop > 150000:  # Tier-1: +2 aux
                    for q, a in (aux1, aux2):
                        specialized_data.append(
                            {"instruction": q, "input": "", "output": a, "language": lang}
                        )
                elif effective_pop > 50000:  # Tier-2: +1 aux
                    specialized_data.append(
                        {"instruction": aux1[0], "input": "", "output": aux1[1], "language": lang}
                    )
                # Tier-3: primary only
```

- [ ] **Step 4: Implémenter la section MANGA**

Remplacer de même le corps de `for idx, item in enumerate(mangas):`. Manga n'a pas de studio ; aux1 = genres :

```python
                description = clean_source_prose(item.get("description", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"
                genres_str = ", ".join(clean_tags(genres, lang)) if genres else (
                    "various genres" if is_en else "genres variés"
                )

                if is_en:
                    primary = make_english_manga_profile(title, genres, tags, description)
                    q_primary = f"What is the manga '{display_t}' about?"
                    aux1 = (
                        f"What genres define the manga '{display_t}'?",
                        f"'{display_t}' spans: {genres_str}.",
                    )
                else:
                    primary = make_french_manga_profile(title, genres, tags)
                    q_primary = f"De quoi parle le manga '{display_t}' ?"
                    aux1 = (
                        f"Quels sont les genres du manga '{display_t}' ?",
                        f"'{display_t}' relève des genres : {genres_str}.",
                    )

                if client and title in augmented_manga_titles:
                    primary = paraphrase_text_via_gemini(primary, client, "encyclopédique")

                specialized_data.append(
                    {"instruction": q_primary, "input": "", "output": primary, "language": lang}
                )
                if effective_pop > 50000:  # Tier-1 & Tier-2: +1 aux
                    specialized_data.append(
                        {"instruction": aux1[0], "input": "", "output": aux1[1], "language": lang}
                    )
```

- [ ] **Step 5: Implémenter la section CHARACTER**

Remplacer le corps de `for idx, c in enumerate(top_chars):`. Extraire la biographie ; supprimer l'usage de `favs`/`rank`/`height` dans le texte (mais `favs` reste lu pour le tiering) :

```python
                biography = clean_source_prose(c.get("biography", ""))
                is_en = idx % 2 == 1
                lang = "English" if is_en else "Français"

                if is_en:
                    primary = make_english_character_bio(
                        display_name, display_origin, orgs, biography
                    )
                    q_primary = f"Who is {display_name}?"
                    aux1 = (
                        f"Which work does {display_name} come from?",
                        f"{display_name} is a character from '{display_origin}'.",
                    )
                else:
                    primary = make_french_character_bio(display_name, display_origin, orgs)
                    q_primary = f"Qui est {display_name} ?"
                    aux1 = (
                        f"De quelle œuvre vient {display_name} ?",
                        f"{display_name} est un personnage de '{display_origin}'.",
                    )

                if client and (name, origin) in augmented_char_names:
                    primary = paraphrase_text_via_gemini(primary, client, "encyclopédique")

                specialized_data.append(
                    {"instruction": q_primary, "input": "", "output": primary, "language": lang}
                )
                if favs > 500:  # Tier-1 & Tier-2: +1 aux
                    specialized_data.append(
                        {"instruction": aux1[0], "input": "", "output": aux1[1], "language": lang}
                    )
```

Note : `make_french_character_bio` reçoit `display_origin` (avec synonyme random) ; le mapping FR des organisations reste dans la fonction. `orgs` provient de `ents.get("organizations", [])` déjà nettoyé plus haut dans la boucle existante.

- [ ] **Step 6: Vérifier que la suite d'intégration passe**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_finetuning_dataset.py -v`
Expected: PASS. Si `test_run_generate_instruction_dataset_all_tiers_and_languages_no_augmentation` échoue sur un comptage implicite, ajuster ses attentes aux nouveaux totaux (le test vérifie surtout la présence et le champ `language`, pas un comptage strict — le corriger si besoin sans affaiblir la couverture).

- [ ] **Step 7: Commit**

```bash
git add backend/pipeline/mlops/finetuning_dataset.py tests/mlops/test_finetuning_dataset.py
git commit -m "feat(ft_dataset): emit grounded distinct outputs, kill 5x identical-variation bug"
```

---

### Task 7: Suite de validation anti-corruption

Un test qui génère un petit dataset via l'orchestrateur (fixtures réalistes avec description/biographie) et **prouve** l'absence des motifs corrupteurs.

**Files:**
- Create: `tests/mlops/test_dataset_sanitation.py`

**Interfaces:**
- Consumes: `fd.run_generate_instruction_dataset` et le harnais `_orchestrator_env` — **réutiliser** le context manager de `test_finetuning_dataset.py` en l'important.

- [ ] **Step 1: Écrire le test (échouera si un motif corrupteur réapparaît)**

Créer `tests/mlops/test_dataset_sanitation.py` :

```python
# -*- coding: utf-8 -*-
"""Garde-fous : le dataset généré est ancré, sans slot numérique, sans squelette."""
import collections
import json
import os
import re
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)  # racine repo -> permet `import tests.mlops...`
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))  # -> permet `import pipeline...`

import pipeline.mlops.finetuning_dataset as fd  # noqa: E402
from tests.mlops.test_finetuning_dataset import _orchestrator_env  # noqa: E402

BANNED_PHRASES = [
    "jouit d'une immense popularité",
    "figure incontournable",
    "se plaçant au rang numéro",
    "incarne les valeurs et les conflits majeurs",
    "votes d'admiration",
    "avec pas moins de",
    "ranking at number",
    "votes of admiration",
    "no less than",
]
BANNED_NUMERIC = [
    re.compile(r"rang num[ée]ro\s+\d+", re.IGNORECASE),
    re.compile(r"\d+\s+votes", re.IGNORECASE),
    re.compile(r"number\s+\d+\s+of favorite", re.IGNORECASE),
]

ANIMES = [
    {"title": "AlphaWork", "genres": ["Action"], "studios": ["StudioX"], "tags": ["ninja"],
     "popularity": 200000, "year": 2002,
     "description": "AlphaHero trains hard to protect his village from the demon lord."},
    {"title": "BetaWork", "genres": ["Comedy"], "studios": ["StudioY"], "tags": ["school"],
     "popularity": 1000, "year": 2015,
     "description": "BetaHero navigates a chaotic high-school life full of clubs."},
]
CHARS = [
    {"name": "GammaHero", "origin": "AlphaWork", "entities": {"organizations": ["Survey Corps"]},
     "popularity": {"favourites": 3000, "rank": 7}, "metadata": {"height": "180 cm"},
     "biography": "GammaHero is a fearless swordsman who lost his family to demons."},
]


def _generate(tmp):
    with _orchestrator_env(
        tmp, animes=ANIMES, mangas=[], chars=CHARS,
        env={"ANIMETIX_AUGMENT_DATA": "False", "ANIMETIX_QUERY_NOISE_RATE": "0.0"},
    ) as out:
        fd.run_generate_instruction_dataset()
        with open(out, encoding="utf-8") as f:
            return [json.loads(line) for line in f]


def _specialized_outputs(data):
    """Sorties dont l'instruction cite une de nos entités-fixtures (donc générées ici)."""
    entities = ("AlphaWork", "BetaWork", "GammaHero")
    outs = []
    for it in data:
        if "turns" in it:
            continue
        text = it.get("instruction", "") + " " + it.get("output", "")
        if any(e in text for e in entities):
            outs.append(it["output"])
    return outs


class TestDatasetSanitation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = _generate(self._tmp.name)
        self.outs = _specialized_outputs(self.data)
        self.assertTrue(self.outs, "aucune sortie spécialisée générée")

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_banned_phrases(self):
        for o in self.outs:
            for phrase in BANNED_PHRASES:
                self.assertNotIn(phrase, o, f"phrase bannie: {phrase!r}")

    def test_no_unconditioned_numeric_noise(self):
        for o in self.outs:
            for rx in BANNED_NUMERIC:
                self.assertIsNone(rx.search(o), f"bruit numérique: {rx.pattern} dans {o!r}")

    def test_outputs_are_grounded(self):
        joined = " ".join(self.outs)
        # faits réels tirés des descriptions/biographie
        self.assertIn("demon lord", joined)
        self.assertIn("swordsman", joined)

    def test_no_duplicate_outputs_per_entity(self):
        alpha = [it["output"] for it in self.data
                 if "AlphaWork" in it.get("instruction", "")]
        self.assertEqual(len(alpha), len(set(alpha)), "sorties dupliquées pour AlphaWork")

    def test_form_diversity_no_dominant_8gram(self):
        grams = collections.Counter()
        for o in self.outs:
            toks = o.split()
            for i in range(len(toks) - 7):
                grams[" ".join(toks[i:i + 8])] += 1
        if grams:
            top = grams.most_common(1)[0][1]
            self.assertLessEqual(top / len(self.outs), 0.5,
                                 "un 8-gramme domine les sorties (squelette ?)")


if __name__ == "__main__":
    unittest.main()
```

Note : le seuil 8-gramme est à 0.5 ici (échantillon minuscule = peu de sorties, donc tolérant). Sur le dataset réel complet (Task 9), on resserre à < 0.05 via l'inspection manuelle, pas via ce test unitaire.

- [ ] **Step 2: Lancer, vérifier le succès (le code des Tasks 1-6 doit déjà satisfaire)**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/test_dataset_sanitation.py -v`
Expected: PASS (5 tests). Si un test échoue, c'est une régression réelle dans les Tasks 2-6 — corriger la source, pas le test.

- [ ] **Step 3: Commit**

```bash
git add tests/mlops/test_dataset_sanitation.py
git commit -m "test(ft_dataset): sanitation guardrails (banned phrases, numeric noise, grounding, diversity)"
```

---

### Task 8: Audit des générateurs annexes

Vérifier que les générateurs non-touchés ne portent pas la même maladie (slot numérique non-conditionné répété, ou sortie identique en masse). **Patcher seulement si malade.**

**Files:**
- Read: `backend/pipeline/mlops/ft_dataset/relation_generators.py`, `market_profile_generators.py`, `otaku_generators.py`, `dialogue_generators.py`, `synthetic_generators.py`
- Modify: seulement ceux jugés malades.
- Create: `docs/analysis/2026-07-17-annex-generators-audit.md` (verdict par générateur).

- [ ] **Step 1: Lire et juger chaque générateur**

Pour chacun, appliquer les 2 critères :
1. **Slot numérique non-conditionné** : une réponse contient-elle un nombre (hors année/volume/épisode réel demandé) non dérivable de la question ? (grep : `rank`, `favourites`, `favs`, `votes`, `{rank}`, `numéro`)
2. **Sortie identique en masse** : le même texte de sortie est-il mappé à N questions différentes ?

Commande d'aide :

```bash
cd backend && grep -nE "rank|favourites|favs|votes|numéro|number \{" pipeline/mlops/ft_dataset/relation_generators.py pipeline/mlops/ft_dataset/market_profile_generators.py pipeline/mlops/ft_dataset/otaku_generators.py pipeline/mlops/ft_dataset/dialogue_generators.py pipeline/mlops/ft_dataset/synthetic_generators.py
```

Attendu (hypothèse du spec) : les relationnels/marché/méta sont **factuels ou à contenu écrit à la main** → sains. `otaku_generators.py` a 15 templates/concept mais chaque `output` diffère (projection de champs distincts) et le contenu est réel → sain, mais **vérifier** qu'aucun n'émet `rank`/`favs`.

- [ ] **Step 2: Écrire le verdict**

Créer `docs/analysis/2026-07-17-annex-generators-audit.md` avec, pour chaque fichier : `SAIN` ou `PATCHÉ` + justification d'une ligne. Exemple de forme :

```markdown
# Audit générateurs annexes — 2026-07-17
- relation_generators.py — SAIN : Q&A factuelles depuis les bases de relations, aucun slot numérique non-conditionné.
- market_profile_generators.py — SAIN : profils depuis données réelles.
- otaku_generators.py — SAIN : 15 projections distinctes/concept, contenu réel, pas de rank/favs.
- dialogue_generators.py — SAIN : dialogues à contenu réel.
- synthetic_generators.py — SAIN : MCP/RAG/refus à structure voulue.
```

- [ ] **Step 3: Si un générateur est jugé malade**, appliquer le même remède (purge du nombre non-conditionné / suppression des sorties identiques) en TDD dans son propre test, puis commit séparé. Sinon, passer.

- [ ] **Step 4: Lancer toute la suite mlops (régression)**

Run: `cd backend && "$PY" -m pytest ../tests/mlops/ -v`
Expected: PASS (toute la suite verte).

- [ ] **Step 5: Commit**

```bash
git add docs/analysis/2026-07-17-annex-generators-audit.md
git commit -m "docs(analysis): annex ft_dataset generators audit verdict"
```

---

### Task 9: Régénération, validation manuelle & upload

Générer le vrai JSONL complet, faire tourner les garde-fous dessus, inspecter à l'œil, puis pousser sur le Hub.

**Files:**
- Generated: `data/mlops/datasets/animetix_expert_ft.jsonl`
- Use: `scripts/deploy/huggingface/hf_upload_dataset.py`

- [ ] **Step 1: Régénérer le dataset complet**

Run (CWD `backend/`, augmentation OFF) :

```bash
cd backend && ANIMETIX_AUGMENT_DATA=False "$PY" -m pipeline.mlops.finetuning_dataset
```

Expected: log `UNIFIED MASSIVE AND OPTIMIZED DATASET READY: N total instructions.` et écriture de `data/mlops/datasets/animetix_expert_ft.jsonl`.

- [ ] **Step 2: Garde-fous sur le fichier réel (script d'inspection jetable)**

Écrire `/tmp/inspect_dataset.py` (hors repo) qui charge le JSONL et vérifie sur **l'ensemble** :
- aucune `BANNED_PHRASES` (réutiliser la liste de Task 7) ;
- aucune `BANNED_NUMERIC` ;
- ratio 8-gramme le plus fréquent (sorties spécialisées) **< 0.05** ;
- ratio d'unicité des sorties **≥ 0.95**.

```python
import json, re, collections
from pathlib import Path

data = [json.loads(l) for l in Path(
    "data/mlops/datasets/animetix_expert_ft.jsonl").read_text(encoding="utf-8").splitlines()]
outs = [it["output"] for it in data if "turns" not in it]

banned = ["jouit d'une immense popularité", "figure incontournable",
          "se plaçant au rang numéro", "incarne les valeurs et les conflits majeurs",
          "votes d'admiration", "avec pas moins de", "ranking at number",
          "votes of admiration", "no less than"]
for b in banned:
    hits = sum(b in o for o in outs)
    print(f"BANNED {b!r}: {hits}")
    assert hits == 0

numeric = [re.compile(r"rang num[ée]ro\s+\d+", re.I), re.compile(r"\d+\s+votes", re.I)]
for rx in numeric:
    hits = sum(bool(rx.search(o)) for o in outs)
    print(f"NUMERIC {rx.pattern}: {hits}")
    assert hits == 0

uniq = len(set(outs)) / len(outs)
print(f"unicité sorties: {uniq:.4f}")
assert uniq >= 0.95

grams = collections.Counter()
for o in outs:
    t = o.split()
    for i in range(len(t) - 7):
        grams[" ".join(t[i:i+8])] += 1
top = grams.most_common(1)[0]
print(f"top 8-gram x{top[1]} ({top[1]/len(outs):.4f}): {top[0][:80]}")
assert top[1] / len(outs) < 0.05
print("TOTAL", len(data), "OK")
```

Run: `cd backend && "$PY" /tmp/inspect_dataset.py`
Expected: tous les `assert` passent ; imprime le total.

- [ ] **Step 3: Inspection manuelle (~20 exemples)**

Run: `cd backend && "$PY" -c "import json,random; d=[json.loads(l) for l in open('data/mlops/datasets/animetix_expert_ft.jsonl',encoding='utf-8')]; r=random.Random(1); [print('---',x.get('language'),'\n Q:',x.get('instruction'),'\n A:',x.get('output','')[:300]) for x in r.sample([i for i in d if 'turns' not in i], 20)]"`

Vérifier à l'œil : FR = faits structurés corrects, EN = synopsis réel présent, aucun chiffre suspect, aucun personnage inventé. **STOP et corriger** si un motif corrupteur apparaît.

- [ ] **Step 4: Upload sur le Hub**

Lire `scripts/deploy/huggingface/hf_upload_dataset.py` pour confirmer la cible (`MissawB/otaku-expert-dataset`) et l'invocation, puis :

Run: `cd backend && "$PY" ../scripts/deploy/huggingface/hf_upload_dataset.py` (adapter au CLI réel du script ; nécessite `HF_TOKEN`).

Expected: push réussi ; vérifier le nombre de lignes affiché == total de Step 2.

- [ ] **Step 5: Vérifier sur le Hub & commit du dataset local**

Vérifier le row count via l'API HF (ou l'UI). Puis committer le JSONL régénéré s'il est suivi par git (sinon, il est en `data/` possiblement ignoré — vérifier `git status`) :

```bash
git add -A
git commit -m "data(ft): regenerate sanitized otaku expert dataset (grounded, no numeric noise)"
```

---

## Self-Review

**Couverture spec :**
- Cause 1 (slots numériques) → Tasks 2,3,5,6 (suppression favs/rank/height) + garde-fou Task 7/9. ✓
- Cause 2 (forme identique) → Task 6 (sorties distinctes) + garde-fou diversité 8-gramme. ✓
- Cause 3 (contenu absent) → Tasks 1,2,4 (ancrage description/biography) + test grounding. ✓
- FR structuré / EN synopsis → Tasks 2-5. ✓
- Nettoyage (mojibake/HTML/spoiler/troncature/awards conservés) → Task 1. ✓
- Suite de validation (phrases bannies, regex, unicité, diversité, ancrage) → Task 7 + Step 2 Task 9. ✓
- Audit annexes → Task 8. ✓
- Régénération + upload → Task 9. ✓
- Hors périmètre (retrain) → non planifié, conforme. ✓

**Cohérence des types :** `make_english_character_bio(name, origin, orgs, biography)`, `make_french_character_bio(name, origin, orgs)`, `make_english_anime_profile(..., description="")`, `make_english_manga_profile(title, genres, tags, description="")`, `make_french_anime_profile(title, genres, studios, tags, year)`, `make_french_manga_profile(title, genres, tags)`, `clean_source_prose(text, max_chars=1200)` — signatures utilisées de façon identique en Tasks 2-6. ✓

**Placeholders :** aucune étape sans code ; les template-pools sont énumérés en entier. ✓
