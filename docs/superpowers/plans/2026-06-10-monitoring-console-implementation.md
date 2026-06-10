# Console de Monitoring Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Développer une console de monitoring permettant de déclencher manuellement les scrapers et la synchronisation Neo4j, et de visualiser les logs en temps réel.

**Architecture:** Exposition d'APIs Django management commands via des endpoints protégés, et création d'une interface frontend réactive avec polling pour les logs et statuts.

**Tech Stack:** Django (Backend), React + Zustand (Frontend), Tailwind CSS.

---

### Task 1: API de pilotage (Backend)

**Files:**
- Create: `backend/api/animetix/api/monitoring.py`
- Modify: `backend/api/animetix_project/urls.py`

- [ ] **Step 1: Créer l'API de monitoring**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name='dispatch')
class PipelineControlView(APIView):
    def post(self, request, action):
        if action == 'run_scraper':
            call_command('run_scrapers')
            return Response({'status': 'Scrapers triggered'})
        elif action == 'sync_neo4j':
            call_command('sync_catalog') # Ajuster selon le nom exact
            return Response({'status': 'Neo4j sync triggered'})
        return Response({'error': 'Invalid action'}, status=400)
```

- [ ] **Step 2: Enregistrer la route**

```python
path('api/monitoring/<str:action>/', PipelineControlView.as_view(), name='pipeline-control'),
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/monitoring.py backend/api/animetix_project/urls.py
git commit -m "feat: add pipeline control API endpoints"
```

---

### Task 2: Interface Frontend (Console)

**Files:**
- Create: `frontend/src/pages/dev/MonitoringConsolePage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [ ] **Step 1: Créer le composant `MonitoringConsolePage`**

```tsx
import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";

const MonitoringConsolePage: React.FC = () => {
  const triggerAction = async (action: string) => {
    await fetch(`/api/monitoring/${action}/`, { method: 'POST' });
  };

  return (
    <AnimatedPage>
      <div className="p-8">
        <h1 className="text-2xl font-black uppercase">Console Pipeline</h1>
        <div className="flex gap-4 mt-6">
          <Button onClick={() => triggerAction('run_scraper')}>Lancer Scrapers</Button>
          <Button onClick={() => triggerAction('sync_neo4j')}>Synchro Neo4j</Button>
        </div>
      </div>
    </AnimatedPage>
  );
};
export default MonitoringConsolePage;
```

- [ ] **Step 2: Ajouter la route**

```tsx
<Route path="/dev/monitoring/" element={<MonitoringConsolePage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/dev/MonitoringConsolePage.tsx frontend/src/features/labs/routes/LabRoutes.tsx
git commit -m "feat: add MonitoringConsolePage"
```
