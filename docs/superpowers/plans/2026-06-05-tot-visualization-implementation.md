# Tree of Thoughts Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer une page de visualisation interactive pour explorer l'arbre de raisonnement (ToT) de l'IA.

**Architecture:** 
- Le backend `TreeOfThoughtsSearchService` est enrichi pour capturer l'arbre complet.
- Un nouvel endpoint API expose cette fonctionnalité.
- Le frontend utilise `react-force-graph-2d` pour un rendu interactif.

**Tech Stack:** Django, React, react-force-graph-2d, Framer Motion, TanStack Query.

---

### Task 1: Backend - Enrichissement du Service ToT

**Files:**
- Modify: `backend/core/domain/services/tree_of_thoughts_service.py`
- Test: `tests/core/test_tot_service_tree.py`

- [ ] **Step 1: Créer le test pour la structure de l'arbre**

```python
import pytest
from unittest.mock import MagicMock
from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService

def test_tot_search_returns_full_tree():
    engine = MagicMock()
    engine.generate.return_value = "0.8" # Pour le score
    pm = MagicMock()
    
    service = TreeOfThoughtsSearchService(engine, pm)
    result = service.solve_with_tree_of_thoughts("Test query", breadth=2, depth=2)
    
    assert "full_tree" in result
    assert "nodes" in result["full_tree"]
    assert "links" in result["full_tree"]
    assert len(result["full_tree"]["nodes"]) > 0
```

- [ ] **Step 2: Implémenter la capture de l'arbre dans le service**

Modifier `solve_with_tree_of_thoughts` pour accumuler les nœuds et les liens.

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/services/tree_of_thoughts_service.py
git commit -m "feat(backend): enrich ToT service to capture full exploration tree"
```

---

### Task 2: Backend - API Lab Endpoint

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Créer `TreeOfThoughtsLabView` dans `labs.py`**

```python
class TreeOfThoughtsLabView(APIView):
    permission_classes = [permissions.AllowAny]
    @inject
    def post(self, request, tot_service=Provide[Container.core.tree_of_thoughts_service]):
        query = request.data.get('query')
        if not query: return Response({"error": "Query required"}, status=400)
        result = tot_service.solve_with_tree_of_thoughts(query)
        return Response(result)
```

- [ ] **Step 2: Enregistrer la route dans `urls/api.py`**

```python
path('labs/tot/', api_views.TreeOfThoughtsLabView.as_view(), name='api_tot_lab'),
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/labs.py backend/api/animetix/urls/api.py
git commit -m "feat(backend): add API endpoint for Tree of Thoughts lab"
```

---

### Task 3: Frontend - Page de Visualisation

**Files:**
- Create: `frontend/src/features/labs/TreeOfThoughtsPage.tsx`
- Modify: `frontend/src/features/social/routes/SocialRoutes.tsx`
- Modify: `frontend/src/features/labs/LabHubPage.tsx`

- [ ] **Step 1: Implémenter `TreeOfThoughtsPage.tsx`**
    - Utiliser `ForceGraph2D`.
    - Gérer l'état de la recherche et l'affichage des résultats.
    - Ajouter le side panel pour l'inspection des nœuds.

- [ ] **Step 2: Lier la route et ajouter la tuile dans le Hub**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/labs/TreeOfThoughtsPage.tsx
git commit -m "feat(frontend): implement Tree of Thoughts interactive visualization"
```
