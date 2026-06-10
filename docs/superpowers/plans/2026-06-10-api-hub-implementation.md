# Dashboard Développeur (API Hub) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer une interface de documentation interactive (Swagger UI/Redoc) exposée via une page dédiée dans le dashboard développeur frontend.

**Architecture:** Exposition des vues `drf-spectacular` dans les URLs backend, et intégration dans une nouvelle page React (`ApiHubPage`) utilisant les vues exposées.

**Tech Stack:** Django, DRF, drf-spectacular, React, Tailwind CSS.

---

### Task 1: Exposer les vues Swagger/Redoc dans le Backend

**Files:**
- Modify: `backend/api/animetix_project/urls.py`

- [ ] **Step 1: Mettre à jour `urls.py` pour inclure les vues OpenAPI**

```python
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path

urlpatterns = [
    # ... autres urls
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/animetix_project/urls.py
git commit -m "feat: expose Swagger/Redoc endpoints"
```

---

### Task 2: Scaffold `ApiHubPage` Frontend

**Files:**
- Create: `frontend/src/pages/dev/ApiHubPage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [ ] **Step 1: Créer le composant `ApiHubPage`**

```tsx
import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const ApiHubPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6">
        <h1 className="text-3xl font-black italic manga-font uppercase mb-8">API Hub</h1>
        <iframe 
            src="/api/schema/swagger-ui/" 
            className="w-full h-[80vh] border-none rounded-xl"
            title="Swagger UI"
        />
      </div>
    </AnimatedPage>
  );
};

export default ApiHubPage;
```

- [ ] **Step 2: Ajouter la route dans `LabRoutes.tsx`**

```tsx
// ...
const ApiHubPage = lazy(() => import('../../../pages/dev/ApiHubPage'));
// ...
<Route path="/dev/api-hub/" element={<ApiHubPage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/dev/ApiHubPage.tsx frontend/src/features/labs/routes/LabRoutes.tsx
git commit -m "feat: scaffold ApiHubPage with Swagger UI iframe"
```

---

### Task 3: Vérification

- [ ] **Step 1: Vérifier le build et la navigation**

Run: Lancer le backend et le frontend. Vérifier que la page `/dev/api-hub/` affiche bien l'interface Swagger.
Expected: PASS
