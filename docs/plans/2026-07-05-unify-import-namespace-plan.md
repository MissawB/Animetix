# Unification de l'espace de noms d'import — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Une seule identité d'import pour tout le backend — la racine nue (`animetix`, `core`, `adapters`, `pipeline`, `scripts`) — avec tripwire durable contre toute réintroduction de `backend.*` / `src.*`.

**Architecture:** Réécriture mécanique scriptée (règles ordonnées, littéraux de chaîne inclus — cibles `@patch` et clés `sys.modules` comprises), puis suppression des deux hacks de compatibilité (sync contextvars de middleware.py, `SrcPipelineMapper` du conftest), nettoyage des en-têtes `sys.path` des scripts standalone, et enfin le tripwire 3 couches (garde levante dans `backend/__init__.py`, ruff TID251, test d'hygiène).

**Tech Stack:** Python 3.12, Django, pytest, ruff (TID251/flake8-tidy-imports), black.

**Spec:** `docs/plans/2026-07-05-unify-import-namespace-design.md` (validée).

## Global Constraints

- Windows : python du venv uniquement — `.venv/Scripts/python.exe` (Git Bash) depuis la racine du repo.
- NE PAS lancer la suite `tests/api` complète en local (mass-fail sans backend d'inférence) — fichiers ciblés uniquement ; la validation large se fait avec `-m "not integration"`.
- Chaque tâche laisse la suite verte (baseline actuelle : 0 échec hors `integration`).
- Le script de réécriture (Task 1) EXCLUT `tests/conftest.py` et `backend/api/animetix/middleware.py` (traités chirurgicalement en Task 2) et ne touche que `*.py` sous `backend/`, `tests/`, `scripts/`.
- NE PAS toucher : les racines `sys.path` (pytest.ini, PYTHONPATH du Dockerfile, hack asgi.py), `pyproject.toml:31-43` (bloc mypy), `--cov=backend` (mesure par chemin), `backend/GEMINI.md`.
- Pre-commit hooks actifs (ruff/black au commit) ; jamais `--no-verify`. mypy local connu cassé (`SKIP=mypy` attendu, la CI l'applique).
- Branche de travail : `chore/unify-import-namespace` (créée en Task 1, Step 1). `git add` par chemins explicites, jamais `-A`.
- Fichiers temporaires (script de réécriture) : sous `C:\Users\bahma\AppData\Local\Temp\claude\`, PAS dans le repo ; supprimer après usage.

---

### Task 1: Réécriture mécanique vers la racine nue (31 fichiers, ~100 lignes + 29 littéraux)

**Files:**
- Modify: ~31 fichiers `*.py` sous `backend/`, `tests/`, `scripts/` (liste produite par le script ; périmètre vérifié par grep en Step 5)
- Create (scratchpad, hors repo): `rewrite_namespace.py`

**Interfaces:**
- Consumes: rien.
- Produces: plus AUCUNE occurrence de `backend.api.animetix|backend.animetix|backend.pipeline|backend.adapters|backend.core|backend.scripts|src.pipeline` dans le code, hors `tests/conftest.py` et `backend/api/animetix/middleware.py` (Task 2). Les Tasks 2-4 en dépendent.

- [ ] **Step 1: Créer la branche**

```bash
git checkout -b chore/unify-import-namespace
```

- [ ] **Step 2: Écrire le script de réécriture dans le scratchpad**

Chemin : `C:\Users\bahma\AppData\Local\Temp\claude\rewrite_namespace.py` (répertoire temporaire, hors repo — le supprimer après la tâche). Contenu exact :

```python
"""Réécriture one-off: unifie les imports/chaînes sur la racine nue."""

import pathlib
import sys

ROOT = pathlib.Path(r"c:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project")

# Ordre IMPORTANT: les préfixes les plus longs d'abord (backend.api.animetix
# avant backend.animetix; jamais de règle nue 'backend.' qui casserait
# p.ex. 'backend.api.manage').
RULES = [
    ("backend.api.animetix", "animetix"),
    ("backend.animetix", "animetix"),
    ("backend.pipeline", "pipeline"),
    ("backend.adapters", "adapters"),
    ("backend.core", "core"),
    ("backend.scripts", "scripts"),
    ("src.pipeline", "pipeline"),
]

EXCLUDE = {
    ROOT / "tests" / "conftest.py",              # SrcPipelineMapper -> Task 2
    ROOT / "backend" / "api" / "animetix" / "middleware.py",  # hack -> Task 2
}

changed = []
for top in ("backend", "tests", "scripts"):
    for path in (ROOT / top).rglob("*.py"):
        if path in EXCLUDE or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        new = text
        for old, repl in RULES:
            new = new.replace(old, repl)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="")
            changed.append(str(path.relative_to(ROOT)))

print(f"{len(changed)} fichiers modifiés:")
print("\n".join(sorted(changed)))
sys.exit(0)
```

- [ ] **Step 3: Exécuter la réécriture**

```bash
.venv/Scripts/python.exe "C:\Users\bahma\AppData\Local\Temp\claude\rewrite_namespace.py"
```

Attendu : ~31 fichiers listés, incluant `backend/api/animetix_project/settings.py` (4 chaînes auth), `backend/api/animetix/api/developer.py`, `explore.py`, `backend/pipeline/characters/combat_data.py`, `backend/pipeline/anime/6_generate_sagas.py`, `vectorize_anime.py`, `backend/pipeline/manga/vectorize_manga.py`, `backend/pipeline/mlops/dpo_dataset_compiler.py`, `ft_dataset/dialogue_generators.py`, `backend/scripts/sync_gold_ground_truth.py`, `backend/pipeline/evaluation/regression_benchmark.py` (commentaire l.17), 19 fichiers `tests/`, `scripts/detect_embedding_drift.py`, `scripts/verify/rag_smoke_test.py`, `scripts/verify/verify_brain_adapter.py`.

- [ ] **Step 4: Lint + format sur les fichiers modifiés**

```bash
.venv/Scripts/python.exe -m ruff check --fix backend/ tests/ scripts/
.venv/Scripts/python.exe -m black backend/ tests/ scripts/ -q
```

(ruff isort réordonne les imports devenus first-party nus ; black reformate. Les deux doivent finir sans erreur.)

- [ ] **Step 5: Vérifier le périmètre par grep**

```bash
grep -rnE "backend\.(api\.animetix|animetix|pipeline|adapters|core|scripts)|src\.pipeline" backend/ tests/ scripts/ --include="*.py" | grep -v __pycache__ | grep -vE "tests/conftest.py|backend/api/animetix/middleware.py"
```

Attendu : **aucun résultat** (exit 1). Les seules occurrences restantes vivent dans les deux fichiers exclus.

- [ ] **Step 6: Tests ciblés + boot Django + collecte**

```bash
.venv/Scripts/python.exe backend/api/manage.py check
.venv/Scripts/python.exe -m pytest tests/mlops/ tests/pipeline/ tests/adapters/ tests/backend/ tests/api/test_companion.py tests/api/test_forms.py tests/api/test_schemas.py -q -m "not integration" 2>&1 | tail -3
.venv/Scripts/python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : `manage.py check` sans erreur ; suites vertes (0 failed) ; collecte saine. NB : les tests mlops jouent avec `sys.modules` — si un test échoue sur une clé `sys.modules` non trouvée, chercher un littéral `backend.pipeline` résiduel oublié par une exclusion, pas contourner.

- [ ] **Step 7: Commit**

```bash
git add backend/ tests/ scripts/
git commit -m "refactor(imports): unify on the bare namespace root (animetix/core/adapters/pipeline)"
```

(Ici `git add` par répertoires est acceptable : le working tree ne contient que les modifications de cette tâche sur ces arbres — vérifier avec `git status --short` qu'aucun fichier étranger n'apparaît.)

---

### Task 2: Supprimer les deux hacks de compatibilité

**Files:**
- Modify: `backend/api/animetix/middleware.py:15-32`
- Modify: `tests/conftest.py:20-66`

**Interfaces:**
- Consumes: Task 1 (plus aucun consommateur des alias).
- Produces: un seul module `animetix.middleware` possible ; plus d'alias `src.*` dans les tests.

- [ ] **Step 1: middleware.py — remplacer le bloc de sync contextvars**

Remplacer ce bloc (l.15-32) :

```python
# Synchronize contextvars across double-import namespaces (e.g. animetix.middleware vs backend.api.animetix.middleware)
# Declared once so the branch assignments below don't trip mypy's no-redef.
user_id_var: contextvars.ContextVar[Optional[Any]]
user_tier_var: contextvars.ContextVar[str]
if "animetix.middleware" in sys.modules and __name__ != "animetix.middleware":
    _other = sys.modules["animetix.middleware"]
    user_id_var = getattr(_other, "user_id_var")
    user_tier_var = getattr(_other, "user_tier_var")
elif (
    "backend.api.animetix.middleware" in sys.modules
    and __name__ != "backend.api.animetix.middleware"
):
    _other = sys.modules["backend.api.animetix.middleware"]
    user_id_var = getattr(_other, "user_id_var")
    user_tier_var = getattr(_other, "user_tier_var")
else:
    user_id_var = contextvars.ContextVar("user_id", default=None)
    user_tier_var = contextvars.ContextVar("user_tier", default="free")
```

par :

```python
# Namespace unique garanti par le garde backend/__init__.py + ruff TID251
# (voir docs/plans/2026-07-05-unify-import-namespace-design.md) : plus besoin
# de synchroniser les contextvars entre doubles identités du module.
user_id_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "user_id", default=None
)
user_tier_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "user_tier", default="free"
)
```

puis supprimer `import sys` en tête de fichier s'il n'a plus d'autre usage (vérifier avec `grep -n "sys\." backend/api/animetix/middleware.py` ; ruff F401 le confirmera).

- [ ] **Step 2: conftest.py — supprimer le mapper src.***

Supprimer intégralement ce bloc (l.20-66) :

```python
import importlib  # noqa: E402
from importlib.abc import Loader, MetaPathFinder  # noqa: E402
from importlib.machinery import ModuleSpec  # noqa: E402


class AliasLoader(Loader):
    def __init__(self, real_module):
        self.real_module = real_module

    def create_module(self, spec):
        return self.real_module

    def exec_module(self, module):
        pass


class SrcPipelineMapper(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("src.pipeline"):
            real_name = fullname.replace("src.pipeline", "pipeline", 1)
            try:
                mod = importlib.import_module(real_name)
                spec = ModuleSpec(fullname, AliasLoader(mod))
                return spec
            except Exception:
                pass
        return None


sys.meta_path.insert(0, SrcPipelineMapper())

# Map the parent packages
try:
    import src  # noqa: E402
except ImportError:
    import types  # noqa: E402

    src = types.ModuleType("src")
    sys.modules["src"] = src

try:
    import pipeline  # noqa: E402

    src.pipeline = pipeline
    sys.modules["src.pipeline"] = pipeline
except Exception:
    pass
```

(ne rien mettre à la place — le `import tracemalloc` qui suit devient le code suivant).

- [ ] **Step 3: Lint + tests des zones touchées**

```bash
.venv/Scripts/python.exe -m ruff check --fix backend/api/animetix/middleware.py tests/conftest.py
.venv/Scripts/python.exe -m black backend/api/animetix/middleware.py tests/conftest.py -q
.venv/Scripts/python.exe -m pytest tests/pipeline/ tests/backend/ -q -m "not integration" 2>&1 | tail -2
.venv/Scripts/python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : 0 failed ; collecte saine (le mapper ne manque à personne puisque Task 1 a réécrit les 5 fichiers `src.pipeline`).

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/middleware.py tests/conftest.py
git commit -m "refactor(imports): drop the dual-namespace compat hacks (middleware contextvars sync, src.* test mapper)"
```

---

### Task 3: Nettoyer les en-têtes sys.path des scripts standalone

**Files:**
- Modify: `backend/pipeline/anime/6_generate_sagas.py:10-22`
- Modify: `backend/pipeline/anime/vectorize_anime.py:16-19`
- Modify: `backend/pipeline/manga/vectorize_manga.py:23-25`
- Modify: `backend/pipeline/evaluation/regression_benchmark.py:10-18`

**Interfaces:**
- Consumes: Task 1 (les `get_repo()` importent déjà `from animetix.containers`).
- Produces: des scripts standalone dont le `sys.path` référence des répertoires qui existent (`backend`, `backend/api`), plus aucun chemin `src/` fantôme.

- [ ] **Step 1: 6_generate_sagas.py — corriger le bloc path**

Remplacer (l.10-22, le bloc `# Setup environment` jusqu'aux deux appends) :

```python
# Setup environment
# abspath(__file__) is backend/pipeline/anime/6_generate_sagas.py
# 1. backend/pipeline/anime
# 2. backend/pipeline
# 3. src
# 4. root
base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
```

par :

```python
# Setup environment — standalone script: expose the two import roots
# (backend -> core/adapters/pipeline, backend/api -> animetix*).
# abspath(__file__) is backend/pipeline/anime/6_generate_sagas.py, so four
# dirname() calls reach the repo root.
base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(os.path.join(base_dir, "backend"))
sys.path.append(os.path.join(base_dir, "backend", "api"))
```

- [ ] **Step 2: vectorize_anime.py — corriger l'append cassé**

Remplacer (l.16-18) :

```python
# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "backend"))
```

par :

```python
# BASE_DIR est backend/ (3 dirname depuis backend/pipeline/anime/) ; on expose
# les deux racines d'import (backend -> core/pipeline, backend/api -> animetix*).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "api"))
```

(Note observée, HORS scope : `INPUT_FILE` de ce script pointe `backend/data/...` au lieu de `data/...` à la racine — bit rot préexistant, ne pas corriger ici, le signaler dans le rapport.)

- [ ] **Step 3: vectorize_manga.py — même traitement**

Remplacer (l.23-25) :

```python
# Détection robuste de la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, "pipeline"))
```

par :

```python
# BASE_DIR est backend/ (3 dirname depuis backend/pipeline/manga/) ; on expose
# les deux racines d'import (backend -> core/pipeline, backend/api -> animetix*).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "api"))
```

- [ ] **Step 4: regression_benchmark.py — retirer les inserts src/ fantômes**

Remplacer (l.10-18) :

```python
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "api"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
# Repo root, so the `backend.api.animetix.*` paths referenced in settings resolve.
sys.path.insert(0, BASE_DIR)
```

par :

```python
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(BASE_DIR, "backend", "api"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
# Repo root: tests.helpers & data paths resolve from here.
sys.path.insert(0, BASE_DIR)
```

- [ ] **Step 5: Vérifier que les 4 fichiers compilent + lint**

```bash
.venv/Scripts/python.exe -m py_compile backend/pipeline/anime/6_generate_sagas.py backend/pipeline/anime/vectorize_anime.py backend/pipeline/manga/vectorize_manga.py backend/pipeline/evaluation/regression_benchmark.py && echo COMPILE_OK
.venv/Scripts/python.exe -m ruff check backend/pipeline/anime/ backend/pipeline/manga/ backend/pipeline/evaluation/regression_benchmark.py
```

Attendu : `COMPILE_OK` ; ruff propre. (Ces scripts sont des one-shots manuels — pas de test runtime automatisé ; la compilation + le lint + la revue suffisent.)

- [ ] **Step 6: Commit**

```bash
git add backend/pipeline/anime/6_generate_sagas.py backend/pipeline/anime/vectorize_anime.py backend/pipeline/manga/vectorize_manga.py backend/pipeline/evaluation/regression_benchmark.py
git commit -m "fix(pipeline): standalone script headers point at real import roots (drop dead src/ paths)"
```

---

### Task 4: Tripwire — garde levante + ruff TID251 + test d'hygiène (TDD)

**Files:**
- Create: `tests/test_import_hygiene.py`
- Modify: `backend/__init__.py` (actuellement vide)
- Modify: `pyproject.toml:19-21` (bloc `[tool.ruff.lint]`)

**Interfaces:**
- Consumes: Tasks 1-3 (zéro import `backend.*`/`src.*` restant).
- Produces: tout `import backend.…` lève `ImportError` ; ruff refuse les imports `backend`/`src` ; le test d'hygiène échoue sur toute régression textuelle.

- [ ] **Step 1: Écrire les tests (RED sur le garde)**

`tests/test_import_hygiene.py` :

```python
"""Tripwire du namespace unique (racine nue).

Historique: le même package était importable sous 2-3 identités
(animetix vs backend.api.animetix, core vs backend.core, plus l'alias legacy
src.pipeline), au point que middleware.py synchronisait ses contextvars entre
les copies. Ces tests verrouillent la racine nue.
Voir docs/plans/2026-07-05-unify-import-namespace-design.md.
"""

import importlib
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ("backend", "tests", "scripts")
FORBIDDEN = re.compile(
    r"(?:from\s+backend\.|import\s+backend\.|src\.pipeline"
    r"|[\"']backend\.(?:api|core|adapters|pipeline|animetix|scripts))"
)


def _offending_lines():
    hits = []
    for top in SCAN_DIRS:
        for path in (REPO / top).rglob("*.py"):
            if "__pycache__" in path.parts or path == pathlib.Path(__file__):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if FORBIDDEN.search(line):
                    hits.append(f"{path.relative_to(REPO)}:{lineno}: {line.strip()}")
    return hits


def test_no_backend_or_src_namespace_references():
    hits = _offending_lines()
    assert not hits, (
        "Références au namespace interdit (backend.*/src.pipeline) :\n"
        + "\n".join(hits)
    )


def test_importing_backend_namespace_raises():
    # Le garde backend/__init__.py doit lever, même pour les chaînes dynamiques
    # (import_string de Django) — c'est la couche runtime du tripwire.
    with pytest.raises(ImportError, match="racine nue"):
        importlib.import_module("backend")
```

- [ ] **Step 2: RED — vérifier l'échec du test de garde**

```bash
.venv/Scripts/python.exe -m pytest tests/test_import_hygiene.py -q
```

Attendu : `test_no_backend_or_src_namespace_references` PASSE (Tasks 1-3 faites) ; `test_importing_backend_namespace_raises` ÉCHOUE (`DID NOT RAISE` — `backend/__init__.py` est vide).

- [ ] **Step 3: Écrire le garde**

Remplacer le contenu (vide) de `backend/__init__.py` par :

```python
# Tripwire du namespace unique — ce package ne doit JAMAIS être importé.
# La racine canonique est nue : animetix / animetix_project (via backend/api
# sur sys.path), core / adapters / pipeline / scripts (via backend/ sur
# sys.path). Importer backend.* recrée une seconde identité des mêmes modules
# (modèles/signaux/DI chargés deux fois).
# Voir docs/plans/2026-07-05-unify-import-namespace-design.md.
raise ImportError(
    "Import via 'backend.*' interdit : utilisez la racine nue "
    "(animetix, core, adapters, pipeline, scripts). "
    "Voir docs/plans/2026-07-05-unify-import-namespace-design.md"
)
```

- [ ] **Step 4: GREEN**

```bash
.venv/Scripts/python.exe -m pytest tests/test_import_hygiene.py -q
```

Attendu : 2 passed.

- [ ] **Step 5: Règle ruff TID251**

Dans `pyproject.toml`, remplacer :

```toml
[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]  # Handled by black; strings/comments intentionally left long
```

par :

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "TID251"]
ignore = ["E501"]  # Handled by black; strings/comments intentionally left long

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"backend".msg = "Racine canonique nue : importez animetix/core/adapters/pipeline/scripts directement (docs/plans/2026-07-05-unify-import-namespace-design.md)."
"src".msg = "Le namespace 'src' n'existe plus : importez pipeline.* directement."
```

(attention à conserver le bloc `[tool.ruff.lint.isort]` qui suit tel quel).

- [ ] **Step 6: Vérifier ruff sur tout le repo + collecte + suite backend**

```bash
.venv/Scripts/python.exe -m ruff check backend/ tests/ scripts/
.venv/Scripts/python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
.venv/Scripts/python.exe -m pytest tests/backend/ tests/api/test_companion.py -q -m "not integration" 2>&1 | tail -2
```

Attendu : ruff propre (aucun TID251 — plus d'import banni) ; collecte saine (personne n'importe `backend` pendant la collecte, sinon le garde le révèle immédiatement) ; tests verts.

- [ ] **Step 7: Commit**

```bash
git add tests/test_import_hygiene.py backend/__init__.py pyproject.toml
git commit -m "feat(imports): tripwire — raising backend/__init__, ruff TID251 ban, hygiene test"
```

---

### Task 5: Vérification finale CI-équivalente + clôture docs

**Files:**
- Modify: `TODO.md` (item 🟠 « triple espace de noms »)
- Modify: `docs/HISTORY.md` (entrée de clôture en tête)

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: item d'audit clos, historique archivé.

- [ ] **Step 1: Suite complète CI-équivalente (longue, ~9 min)**

```bash
.venv/Scripts/python.exe -m pytest -m "not integration" --cov=backend --cov-report=term -q 2>&1 | tail -4
```

Attendu : 0 failed (baseline : tout vert) ; `Required test coverage of 75.0% reached`.

- [ ] **Step 2: Greps finaux**

```bash
grep -rnE "backend\.(api\.animetix|animetix|pipeline|adapters|core|scripts)|src\.pipeline" backend/ tests/ scripts/ --include="*.py" | grep -v __pycache__ | grep -v "tests/test_import_hygiene.py"
```

Attendu : aucun résultat (exit 1) — le test d'hygiène est le seul à contenir le motif (dans sa regex).

- [ ] **Step 3: TODO.md — clore l'item**

Remplacer :

```markdown
- [ ] **Backend — triple espace de noms d'import du même package** _(audit dette 2026-07-05)_
  - L'app est enregistrée `animetix` nu ([settings.py:195](backend/api/animetix_project/settings.py#L195)) mais importée aussi en `backend.api.animetix` (10 imports, dont settings) et `backend.animetix` (pipeline). Django peut charger modèles/signaux/singletons DI **deux fois** sous des identités différentes. Racine de plusieurs hacks en cascade (le `MetaPathFinder` custom de [tests/conftest.py:36-66](tests/conftest.py#L36-L66), les imports paresseux `# noqa: E402` partout). Choisir une racine unique.
```

par :

```markdown
- [x] **Backend — triple espace de noms d'import du même package** _(audit dette 2026-07-05 ; **clos** le 2026-07-05, archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - Racine nue unifiée partout (~31 fichiers réécrits, chaînes `@patch`/settings comprises) ; hacks supprimés (sync contextvars de middleware.py, `SrcPipelineMapper` du conftest) ; tripwire 3 couches : garde levante [backend/\_\_init\_\_.py](backend/__init__.py), ruff TID251, [test_import_hygiene.py](tests/test_import_hygiene.py). Spec : [docs/plans/2026-07-05-unify-import-namespace-design.md](docs/plans/2026-07-05-unify-import-namespace-design.md).
```

- [ ] **Step 4: HISTORY — entrée de clôture**

Dans `docs/HISTORY.md`, insérer après la ligne « This document archives... » (avant la première section datée existante) :

```markdown
## [2026-07-05] Session: Unified the import namespace on the bare root

Closure of the 🟠 debt item "triple espace de noms d'import" (2026-07-05 audit). The same packages were importable as `animetix` / `backend.api.animetix` / `backend.animetix` (and `core` / `backend.core`, etc., plus a legacy `src.pipeline` alias in tests), because three sys.path roots (`.`, `backend`, `backend/api`) coexist — Django genuinely loaded both identities in prod (settings mixed them inside MIDDLEWARE/AUTHENTICATION_BACKENDS) and `middleware.py` carried a runtime contextvars-sync hack between the module copies. Unified everything on the bare root (INSTALLED_APPS' identity, ~95% of the code already): ~31 files rewritten (imports, `@patch` targets, `sys.modules` keys, settings dotted strings), both compat hacks deleted (middleware sync, `SrcPipelineMapper`/`AliasLoader` in tests/conftest.py), standalone pipeline script headers cleaned of dead `src/` path entries, and a 3-layer tripwire installed: `backend/__init__.py` now raises ImportError on any `backend.*` import (implicit-namespace-package-proof), ruff TID251 bans `backend`/`src` imports, and `tests/test_import_hygiene.py` scans for textual regressions.
```

- [ ] **Step 5: Commit**

```bash
git add TODO.md docs/HISTORY.md
git commit -m "docs: close the import-namespace debt item (unified on the bare root)"
```
