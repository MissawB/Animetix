# Console d'Observabilité & Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Développer une console d'observabilité permettant le monitoring des dérives d'archétypes et des violations de guardrails, et l'ajustement dynamique des seuils de sécurité IA.

**Architecture:** Exposition d'APIs Django pour lire/écrire les configurations de sécurité et les données de dérive (via `ArchetypeDriftService`), et interface frontend React avec des composants interactifs de contrôle.

**Tech Stack:** Django (Backend), React + Zustand (Frontend), Tailwind CSS.

---

### Task 1: API d'Observabilité (Backend)

**Files:**
- Create: `backend/api/animetix/api/observability.py`
- Modify: `backend/api/animetix_project/urls.py`

- [ ] **Step 1: Créer l'API d'observabilité (`ObservabilityView`)**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from animetix.containers import Container

@method_decorator(staff_member_required, name='dispatch')
class ObservabilityView(APIView):
    def get(self, request):
        container = Container()
        drift = container.core.archetype_drift_service().calculate_drift(user_id=1) # Exemple
        return Response({'drift': drift.archetype_id, 'guardrail_status': 'online'})
    
    def post(self, request):
        # Logique pour mettre à jour les seuils (ex: via GuardrailService)
        return Response({'status': 'configuration updated'})
```

- [ ] **Step 2: Enregistrer la route**

```python
path('api/observability/', ObservabilityView.as_view(), name='observability'),
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/observability.py backend/api/animetix_project/urls.py
git commit -m "feat: add observability and guardrail API endpoints"
```

---

### Task 2: Interface Frontend (Console Observabilité)

**Files:**
- Create: `frontend/src/pages/dev/ObservabilityConsolePage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [ ] **Step 1: Créer `ObservabilityConsolePage`**

```tsx
import React, { useState } from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";

const ObservabilityConsolePage: React.FC = () => {
  const [threshold, setThreshold] = useState(0.5);

  return (
    <AnimatedPage>
      <div className="p-8">
        <h1 className="text-2xl font-black uppercase">Console Observabilité</h1>
        <div className="mt-6">
          <label>Seuil de sécurité: {threshold}</label>
          <input type="range" min="0" max="1" step="0.1" value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} />
          <Button onClick={() => console.log('Update', threshold)}>Appliquer</Button>
        </div>
      </div>
    </AnimatedPage>
  );
};
export default ObservabilityConsolePage;
```

- [ ] **Step 2: Ajouter la route**

```tsx
<Route path="/dev/observability/" element={<ObservabilityConsolePage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/dev/ObservabilityConsolePage.tsx frontend/src/features/labs/routes/LabRoutes.tsx
git commit -m "feat: add ObservabilityConsolePage"
```
