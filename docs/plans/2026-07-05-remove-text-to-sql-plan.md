# Suppression de la surface text-to-SQL — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supprimer de bout en bout la feature morte « text-to-SQL » (SQL généré par LLM, item 🔴 de l'audit dette 2026-07-05), y compris `sql_guard.py`, ses tests, sa dépendance `sqlglot` et ses mentions doc.

**Architecture:** Suppression pure (aucun nouveau code). Ordre : tests d'abord (plus aucune référence), puis chaîne runtime (port → 3 adapters), puis guard/settings/script, puis dépendances, puis docs. Chaque tâche laisse la suite verte.

**Tech Stack:** Django/DRF, pytest, pip-tools (`pip-compile`), ruff/black.

**Spec:** `docs/plans/2026-07-05-remove-text-to-sql-design.md` (validée).

## Global Constraints

- Windows : utiliser le python du venv — `.venv\Scripts\python.exe` — depuis la racine du repo (seul le venv a Django).
- NE PAS lancer la suite `tests/api` complète en local (mass-fail sans backend d'inférence) — tests ciblés uniquement.
- NE PAS toucher : `ALLOYDB_EMBEDDING_MODEL` (settings.py:477, utilisé par `backend/pipeline/vector_client.py`), la migration `0028_alloydb_scann_and_ml`, l'entrée `docs/HISTORY.md` §[2026-06-10].
- mypy local est connu cassé (pin `pathspec<0.13` via dbt — cf. header de `.pre-commit-config.yaml`) : `SKIP=mypy` au commit est attendu ; la CI l'applique.
- `pip-compile` SANS `--upgrade` : seul `sqlglot` doit bouger dans `requirements.txt`.
- Le working tree contient déjà des changements non commités sans rapport (remédiation secrets : `.gcloudignore`, `.dockerignore`, `hf_deploy.py`, `TODO.md`, `docs/HISTORY.md`) — commiter UNIQUEMENT les fichiers listés dans chaque tâche (`git add <paths>` explicites, jamais `git add -A`).

---

### Task 1: Supprimer les tests de la feature

**Files:**
- Delete: `tests/core/test_alloydb_querydata_nl.py`
- Delete: `tests/security/test_sql_fuzzing.py`
- Modify: `tests/adapters/test_pgvector_repository_adapter.py:350-354`

**Interfaces:**
- Consumes: rien.
- Produces: une suite de tests qui ne référence plus `query_data_natural_language` ni `sql_guard` — prérequis pour supprimer le code (Task 2-3) sans casser la collecte.

- [ ] **Step 1: Supprimer les deux fichiers de tests**

```bash
git rm tests/core/test_alloydb_querydata_nl.py tests/security/test_sql_fuzzing.py
```

- [ ] **Step 2: Retirer l'assertion du stub pgvector**

Dans `tests/adapters/test_pgvector_repository_adapter.py`, remplacer :

```python
def test_stub_methods_return_defaults(adapter):
    assert adapter.get_creative_fusion(1) is None
    assert adapter.get_user_gameplay_history(1) == []
    assert adapter.get_user_creative_history(1) == []
    assert adapter.query_data_natural_language("anything") == []
```

par :

```python
def test_stub_methods_return_defaults(adapter):
    assert adapter.get_creative_fusion(1) is None
    assert adapter.get_user_gameplay_history(1) == []
    assert adapter.get_user_creative_history(1) == []
```

- [ ] **Step 3: Vérifier que la suite adapters passe et que la collecte est saine**

```bash
.venv\Scripts\python.exe -m pytest tests/adapters/test_pgvector_repository_adapter.py -q
.venv\Scripts\python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : tests PASS ; collecte sans erreur (`error` absent des dernières lignes).

- [ ] **Step 4: Commit**

```bash
git add tests/adapters/test_pgvector_repository_adapter.py
git commit -m "test: drop text-to-SQL feature tests ahead of its removal" -- tests/core/test_alloydb_querydata_nl.py tests/security/test_sql_fuzzing.py tests/adapters/test_pgvector_repository_adapter.py
```

---

### Task 2: Supprimer la chaîne runtime (port + 3 adapters)

**Files:**
- Modify: `backend/core/ports/repository_port.py:2,109-114`
- Modify: `backend/adapters/persistence/django_repository_adapter.py:2,6,11-41,222-337`
- Modify: `backend/adapters/persistence/unified_repository_adapter.py:2,121-125`
- Modify: `backend/adapters/persistence/pgvector_repository_adapter.py:3,317-324`

**Interfaces:**
- Consumes: la suite de tests nettoyée (Task 1).
- Produces: `RepositoryPort` sans `query_data_natural_language` ; les 3 adapters ne l'implémentent plus ; plus aucun import de `core.utils.sql_guard` (permet Task 3).

- [ ] **Step 1: Port — retirer la méthode abstraite et l'import `Any`**

Dans `backend/core/ports/repository_port.py`, supprimer le bloc :

```python
    @abstractmethod
    def query_data_natural_language(
        self, query: str, llm_service: Optional[Any] = None
    ) -> List[Dict]:
        """Interroge le catalogue en langage naturel (Text-to-SQL) et renvoie les résultats."""
        pass
```

et changer la ligne 2 `from typing import Any, Dict, List, Optional` en :

```python
from typing import Dict, List, Optional
```

- [ ] **Step 2: Adapter Django — retirer le helper, la méthode et les imports orphelins**

Dans `backend/adapters/persistence/django_repository_adapter.py` :

1. Supprimer le bloc module-level (l.11-41) : la variable `_alloydb_nl_supported = None` et toute la fonction `is_alloydb_nl_query_supported()` (de `def is_alloydb_nl_query_supported() -> bool:` jusqu'à `return _alloydb_nl_supported` inclus).
2. Supprimer toute la méthode `query_data_natural_language` (l.222-337) : de `def query_data_natural_language(` jusqu'au `return []` du dernier `except Exception as e:` (celui qui logge `Text-to-SQL: Database execution failed`).
3. Ligne 2 : `from typing import Any, Dict, List, Optional` → `from typing import Dict, List, Optional`.
4. Ligne 6 : supprimer `from django.conf import settings` (plus aucun usage — les deux seuls étaient dans la méthode supprimée).

- [ ] **Step 3: Adapter unifié — retirer la délégation**

Dans `backend/adapters/persistence/unified_repository_adapter.py`, supprimer :

```python
    def query_data_natural_language(
        self, query: str, llm_service: Optional[Any] = None
    ) -> List[Dict]:
        """Délègue la requête Text-to-SQL à l'adaptateur relationnel Django."""
        return self.django.query_data_natural_language(query, llm_service)
```

et ligne 2 : `from typing import Any, Dict, List, Optional` → `from typing import Dict, List, Optional`.

- [ ] **Step 4: Adapter pgvector — retirer le stub**

Dans `backend/adapters/persistence/pgvector_repository_adapter.py`, supprimer :

```python
    def query_data_natural_language(
        self, query: str, llm_service: Optional[Any] = None
    ) -> List[Dict]:
        """PGVector adapter doesn't query relational database directly. Returns empty."""
        logger.warning(
            "PGVectorRepositoryAdapter.query_data_natural_language called, but vector adapter does not support relational Text-to-SQL directly."
        )
        return []
```

et ligne 3 : `from typing import Any, Dict, List, Optional` → `from typing import Dict, List, Optional`.

- [ ] **Step 5: Vérifier lint + tests + collecte**

```bash
.venv\Scripts\python.exe -m ruff check backend/core/ports/repository_port.py backend/adapters/persistence/
.venv\Scripts\python.exe -m pytest tests/adapters/test_pgvector_repository_adapter.py -q
.venv\Scripts\python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : ruff sans erreur (aucun F401 import inutilisé) ; tests PASS ; collecte saine.

- [ ] **Step 6: Commit**

```bash
git add backend/core/ports/repository_port.py backend/adapters/persistence/django_repository_adapter.py backend/adapters/persistence/unified_repository_adapter.py backend/adapters/persistence/pgvector_repository_adapter.py
git commit -m "refactor(security): remove dead LLM text-to-SQL path from port and adapters"
```

---

### Task 3: Supprimer sql_guard, le script d'audit et les settings

**Files:**
- Delete: `backend/core/utils/sql_guard.py`
- Delete: `scripts/verify/audit_sql_guard.py`
- Modify: `backend/api/animetix_project/settings.py:638-640`

**Interfaces:**
- Consumes: Task 2 (plus aucun import de `sql_guard` dans le code).
- Produces: repo sans `sql_guard`/`ALLOYDB_NL_*` — permet le retrait de `sqlglot` (Task 4).

- [ ] **Step 1: Supprimer les deux fichiers**

```bash
git rm backend/core/utils/sql_guard.py scripts/verify/audit_sql_guard.py
```

- [ ] **Step 2: Retirer les settings**

Dans `backend/api/animetix_project/settings.py`, supprimer les 3 lignes :

```python
# --- ALLOYDB AI QUERYDATA (TEXT-TO-SQL) ---
ALLOYDB_NL_QUERY_ACTIVE = env.bool("ALLOYDB_NL_QUERY_ACTIVE", default=False)
ALLOYDB_NL_CONFIG_NAME = env("ALLOYDB_NL_CONFIG_NAME", default="animetix_catalog")
```

(garder la ligne vide entre le bloc VERTEX_AI au-dessus et le bloc STRIPE en dessous).

- [ ] **Step 3: Vérifier zéro référence restante dans le code**

```bash
grep -rn "sql_guard\|validate_sql_query\|ALLOYDB_NL\|is_alloydb_nl_query_supported\|query_data_natural_language" backend/ tests/ scripts/ frontend/src/
.venv\Scripts\python.exe -m pytest tests/ -q --collect-only 2>&1 | tail -3
```

Attendu : grep sans résultat (exit 1) ; collecte saine.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix_project/settings.py
git commit -m "refactor(security): drop sql_guard, its audit script and ALLOYDB_NL settings" -- backend/core/utils/sql_guard.py scripts/verify/audit_sql_guard.py backend/api/animetix_project/settings.py
```

---

### Task 4: Retirer sqlglot des dépendances

**Files:**
- Modify: `requirements.in:28`
- Modify: `requirements.txt` (régénéré)

**Interfaces:**
- Consumes: Task 3 (plus aucun `import sqlglot` dans le repo).
- Produces: lock sans `sqlglot`.

- [ ] **Step 1: Retirer la ligne de requirements.in**

Supprimer la ligne `sqlglot==25.0.0` (l.28, dans le bloc « 2. » entre `redis==7.4.0` et la ligne vide avant `# 3. Testing, Dev Tools, Automation`).

- [ ] **Step 2: Régénérer le lock (commande exacte du header de requirements.txt, SANS --upgrade)**

```bash
.venv\Scripts\python.exe -m piptools compile --allow-unsafe --output-file=requirements.txt --strip-extras requirements.in
```

- [ ] **Step 3: Vérifier que seul sqlglot a bougé**

```bash
git diff requirements.txt | grep -E "^[+-][a-z]" 
```

Attendu : uniquement `-sqlglot==25.0.0` (et rien d'autre — si d'autres pins bougent, `git checkout -- requirements.txt` et investiguer avant de refaire).

- [ ] **Step 4: Commit**

```bash
git add requirements.in requirements.txt
git commit -m "build: drop sqlglot (only consumer was the removed sql_guard)"
```

---

### Task 5: Docs, TODO et vérification finale

**Files:**
- Modify: `README.md:126,213`
- Modify: `docs/ROADMAP.md:59`
- Modify: `docs/FULL_GUIDE.md:100`
- Modify: `docs/HISTORY.md` (nouvelle entrée en tête)
- Modify: `TODO.md` (item 🔴 « SQL généré par LLM »)

**Interfaces:**
- Consumes: Tasks 1-4 terminées.
- Produces: documentation cohérente avec le code ; item d'audit clos.

- [ ] **Step 1: README — retirer les deux bullets**

Supprimer la ligne 126 :

```markdown
* **AlloyDB AI Tools:** Accelerates text-to-SQL operations on database catalogs via native SQL functions (`alloydb_ai_nl.get_sql`).
```

et la ligne 213 :

```markdown
* **Two-Layered SQL Guardrail:** Prior to execution, generated SQL queries are checked by `sql_guard.py` to prevent multi-statement injection, comments, mutating actions, or unauthorized table access.
```

- [ ] **Step 2: ROADMAP et FULL_GUIDE — retirer les mentions**

`docs/ROADMAP.md`, supprimer la ligne 59 :

```markdown
*   **SQL Hardening:** `sql_guard.py` parser and read-only transactions for Text-to-SQL.
```

`docs/FULL_GUIDE.md`, supprimer la ligne 100 :

```markdown
- **SQL Guardrail:** Natural language text-to-SQL inputs are audited via `sql_guard.py` to prevent SQL injection, multi-statement queries, comments, or unauthorized table access.
```

- [ ] **Step 3: HISTORY — entrée de clôture**

Dans `docs/HISTORY.md`, insérer après la ligne « This document archives... » (avant la première section `## [2026-07-05]` existante) :

```markdown
## [2026-07-05] Session: Removed the dead LLM text-to-SQL surface

Closure of the 🔴 debt item "SQL généré par LLM exécuté en base" (2026-07-05 audit). Exploration showed the whole chain was dead code: zero production callers (only the port, adapters and tests referenced it), `ALLOYDB_NL_QUERY_ACTIVE=False` by default, and prod runs on Neon where the native `alloydb_ai_nl.get_sql` path cannot execute — while the LLM fallback would have run with `neondb_owner` privileges gated only by a `READ ONLY` transaction. Decision (user-validated): delete rather than harden — removed `query_data_natural_language` from `RepositoryPort` and its three adapters, `is_alloydb_nl_query_supported()`, `sql_guard.py` (sqlglot AST validator), its fuzzing tests and `scripts/verify/audit_sql_guard.py`, the `ALLOYDB_NL_*` settings, and the `sqlglot` dependency. Everything is recoverable from git if the feature ever ships for real (spec: `docs/plans/2026-07-05-remove-text-to-sql-design.md`).
```

(la section §[2026-06-10] qui documente la création reste intacte.)

- [ ] **Step 4: TODO — clore l'item**

Dans `TODO.md`, remplacer :

```markdown
- [ ] **Sécu — SQL généré par LLM exécuté en base (auto-flaggé HIGH-RISK)** _(audit dette 2026-07-05)_
  - [django_repository_adapter.py:222-329](backend/adapters/persistence/django_repository_adapter.py#L222-L329) : `cursor.execute` sur du SQL produit par le LLM. Garde-fous existants (allowlist regex, `SET TRANSACTION READ ONLY`, timeout 1500ms) mais strip markdown fait main fragile. Durcir : rôle PostgreSQL dédié lecture seule au niveau DB (pas seulement transaction), ou isoler derrière une API paramétrée.
```

par :

```markdown
- [x] **Sécu — SQL généré par LLM exécuté en base (auto-flaggé HIGH-RISK)** _(audit dette 2026-07-05 ; **clos** le 2026-07-05 par suppression, archivé dans [docs/HISTORY.md](docs/HISTORY.md))_
  - Code mort de bout en bout (zéro appelant de production, flag off, prod sur Neon) → feature supprimée plutôt que durcie : port + 3 adapters, `sql_guard.py` + fuzzing + script d'audit, settings `ALLOYDB_NL_*`, dépendance `sqlglot`. Spec : [docs/plans/2026-07-05-remove-text-to-sql-design.md](docs/plans/2026-07-05-remove-text-to-sql-design.md).
```

- [ ] **Step 5: Vérification finale globale**

```bash
grep -rn "sql_guard\|validate_sql_query\|ALLOYDB_NL\|query_data_natural_language\|alloydb_ai_nl" backend/ tests/ scripts/ frontend/src/ README.md docs/ROADMAP.md docs/FULL_GUIDE.md
.venv\Scripts\python.exe -m ruff check backend/ 
.venv\Scripts\python.exe -m black --check backend/adapters/persistence/ backend/core/ports/
.venv\Scripts\python.exe -m pytest tests/adapters/ tests/core/ -q 2>&1 | tail -5
```

Attendu : grep vide ; ruff/black OK ; suites adapters+core vertes (les échecs `integration` skippés sans ollama sont normaux).

- [ ] **Step 6: Commit**

```bash
git add README.md docs/ROADMAP.md docs/FULL_GUIDE.md docs/HISTORY.md TODO.md
git commit -m "docs: close the text-to-SQL debt item (feature removed)"
```

Note : `TODO.md` et `docs/HISTORY.md` portent déjà des modifications non commitées de la session secrets — si `git status` les montre modifiés avant ce task, commiter quand même ces deux fichiers ici (les changements secrets y sont cohérents et documentés), mais NE PAS ajouter `.gcloudignore`/`.dockerignore`/`hf_deploy.py` à ce commit.
