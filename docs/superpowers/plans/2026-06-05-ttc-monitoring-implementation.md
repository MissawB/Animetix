# Dynamic Budget TTC Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer un dashboard d'administration pour suivre l'allocation et la consommation du budget de réflexion (TTC) de l'IA.

**Architecture:** 
- Le modèle `AITokenUsage` est enrichi avec un champ `allocated_budget`.
- L'adaptateur d'usage est mis à jour pour persister ce budget.
- Un nouvel API Viewset fournit des statistiques d'agrégation.
- Une nouvelle page frontend visualise les données.

**Tech Stack:** Django, React, Tailwind CSS, TanStack Query, Framer Motion.

---

### Task 1: Backend - Évolution du Modèle et Migration

**Files:**
- Modify: `backend/api/animetix/models.py`
- Create: Migration file (via `makemigrations`)

- [ ] **Step 1: Ajouter le champ `allocated_budget`**

```python
# backend/api/animetix/models.py
class AITokenUsage(models.Model):
    # ... champs existants ...
    allocated_budget = models.IntegerField(default=0) # Nouveau champ
```

- [ ] **Step 2: Créer et appliquer la migration**

Run: `cd backend/api; python manage.py makemigrations; python manage.py migrate`

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/models.py backend/api/animetix/migrations/
git commit -m "feat(backend): add allocated_budget field to AITokenUsage model"
```

---

### Task 2: Backend - Mise à jour de l'Adaptateur d'Usage

**Files:**
- Modify: `backend/core/ports/usage_port.py`
- Modify: `backend/adapters/persistence/django_usage_adapter.py`
- Modify: `backend/core/domain/services/llm_service.py` (ou là où `log_usage` est appelé)

- [ ] **Step 1: Mettre à jour le port `UsagePort`**

```python
# backend/core/ports/usage_port.py
    @abstractmethod
    def log_usage(
        self, 
        engine: str, 
        input_tokens: int = 0, 
        output_tokens: int = 0, 
        units: int = 0,
        user_id: Optional[int] = None,
        allocated_budget: int = 0 # Ajouté
    ):
```

- [ ] **Step 2: Mettre à jour l'implémentation `DjangoUsageAdapter`**

```python
# backend/adapters/persistence/django_usage_adapter.py
    def log_usage(self, ..., allocated_budget: int = 0):
        # ... cost calculation ...
        AITokenUsage.objects.create(
            # ...
            allocated_budget=allocated_budget
        )
```

- [ ] **Step 3: S'assurer que le budget est passé lors du log**

Vérifier les appels dans `backend/adapters/inference/` (ex: `brain_api_adapter.py`, `google_genai_adapter.py`).

- [ ] **Step 4: Commit**

```bash
git add backend/core/ports/usage_port.py backend/adapters/persistence/django_usage_adapter.py
git commit -m "feat(backend): update usage adapter to record allocated budget"
```

---

### Task 3: Backend - API Admin TTC

**Files:**
- Modify: `backend/api/animetix/api/admin_api.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Implémenter l'endpoint de monitoring dans `admin_api.py`**

```python
# backend/api/animetix/api/admin_api.py
class TTCMonitoringAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Stats globales 24h
        today = timezone.now() - timedelta(hours=24)
        qs = AITokenUsage.objects.filter(created_at__gte=today, allocated_budget__gt=0)
        
        total_allocated = qs.aggregate(Sum('allocated_budget'))['allocated_budget__sum'] or 0
        total_consumed = qs.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0
        
        # Live Feed (dernières 50)
        recent_logs = qs.order_by('-created_at')[:50]
        
        return Response({
            "summary": {
                "total_allocated": total_allocated,
                "total_consumed": total_consumed,
                "efficiency": round((total_consumed / total_allocated * 100), 1) if total_allocated > 0 else 100
            },
            "logs": [
                {
                    "id": l.id,
                    "engine": l.engine,
                    "allocated": l.allocated_budget,
                    "consumed": l.total_tokens,
                    "timestamp": l.created_at
                } for l in recent_logs
            ]
        })
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/animetix/api/admin_api.py
git commit -m "feat(backend): add TTC monitoring API endpoint for admins"
```

---

### Task 4: Frontend - Dashboard TTC Monitoring

**Files:**
- Create: `frontend/src/features/admin/TTCMonitoringPage.tsx`
- Modify: `frontend/src/features/admin/MLOpsDashboard.tsx`
- Modify: `frontend/src/features/admin/routes/AdminRoutes.tsx`

- [ ] **Step 1: Créer la page de visualisation avec des cartes KPI et un tableau**

- [ ] **Step 2: Lier dans le MLOps Dashboard**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/admin/TTCMonitoringPage.tsx
git commit -m "feat(frontend): implement TTC Budget Monitoring dashboard"
```
