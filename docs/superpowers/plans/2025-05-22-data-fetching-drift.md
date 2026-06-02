# Task 1: Data Fetching for Drift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add history methods to `RepositoryPort` and implement them in `DjangoRepositoryAdapter` and `UnifiedRepositoryAdapter` to fetch user gameplay and creative history.

**Architecture:** Extend the existing repository port-adapter pattern to include user-specific history data retrieval from the relational database (Django).

**Tech Stack:** Python, Django ORM.

---

### Task 1: Update RepositoryPort

**Files:**
- Modify: `backend/core/ports/repository_port.py`

- [ ] **Step 1: Add abstract history methods**

Add `get_user_gameplay_history` and `get_user_creative_history` to the `RepositoryPort` class.

```python
    @abstractmethod
    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Récupère l'historique des sessions de jeu d'un utilisateur."""
        pass

    @abstractmethod
    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Récupère l'historique des fusions créatives d'un utilisateur."""
        pass
```

- [ ] **Step 2: Verify syntax**

Ensure the imports `List` and `Dict` are available (they already are).

---

### Task 2: Implement in DjangoRepositoryAdapter

**Files:**
- Modify: `backend/adapters/persistence/django_repository_adapter.py`

- [ ] **Step 1: Implement `get_user_gameplay_history`**

```python
    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import GameplaySession
        sessions = GameplaySession.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
        return [{"target": s.target_item, "media_type": s.media_type, "won": s.was_won} for s in sessions]
```

- [ ] **Step 2: Implement `get_user_creative_history`**

```python
    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import CreativeFusion
        fusions = CreativeFusion.objects.filter(creator_id=user_id).order_by('-created_at')[:limit]
        return [{"art_style": f.art_style, "titles": f"{f.title_a} x {f.title_b}"} for f in fusions]
```

---

### Task 3: Update UnifiedRepositoryAdapter

**Files:**
- Modify: `backend/adapters/persistence/unified_repository_adapter.py`

- [ ] **Step 1: Delegate history methods**

Delegate both new methods to `self.django`.

```python
    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.django.get_user_gameplay_history(user_id, limit)

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.django.get_user_creative_history(user_id, limit)
```

---

### Task 4: Verification and Commit

- [ ] **Step 1: Run a smoke test (optional but recommended)**

Since this requires a Django environment, a simple check of the added methods is enough.

- [ ] **Step 2: Commit changes**

```bash
git add backend/core/ports/repository_port.py backend/adapters/persistence/django_repository_adapter.py backend/adapters/persistence/unified_repository_adapter.py
git commit -m "feat(personalization): add user history methods to repository ports and adapters"
```
