# Console MLOps (Training) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Développer une interface pour la supervision des boucles d'entraînement DPO et la visualisation des adaptateurs ML.

**Architecture:** Implémentation d'une API backend pour l'état et le contrôle de la boucle DPO et la liste des adaptateurs, et d'une interface frontend React pour afficher ces informations et interagir avec l'API.

**Tech Stack:** Django, DRF (Backend), React, Zustand (Frontend), Tailwind CSS.

---

### Task 1: API Backend MLOps (DPO & Adaptateurs)

**Files:**
- Modify: `backend/api/animetix/api/mlops.py`
- Modify: `backend/api/animetix_project/urls.py`

- [ ] **Step 1: Mettre à jour `mlops.py` pour DPO et Adaptateurs**

```python
# backend/api/animetix/api/mlops.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from animetix.containers import Container
import logging

logger = logging.getLogger('animetix.mlops.api')

@method_decorator(staff_member_required, name='dispatch')
class DPOFeedbackLoopView(APIView):
    def get(self, request):
        container = Container()
        dpo_loop = container.core.dpo_feedback_loop()
        # Ici, vous devriez appeler des méthodes sur dpo_loop pour obtenir le statut et les métriques
        # Pour l'instant, c'est un placeholder
        
        # Exemple de métriques/statut
        dpo_status = "idle" # dpo_loop.get_status()
        last_loss = 0.0 # dpo_loop.get_last_loss()
        last_accuracy = 0.0 # dpo_loop.get_last_accuracy()

        return Response({
            'status': dpo_status,
            'metrics': {'last_loss': last_loss, 'last_accuracy': last_accuracy}
        })

    def post(self, request):
        action = request.data.get('action')
        container = Container()
        dpo_loop = container.core.dpo_feedback_loop()

        if action == 'start':
            # dpo_loop.start()
            logger.info("DPO Feedback Loop: Start action triggered.")
            return Response({'status': 'DPO loop started'})
        elif action == 'pause':
            # dpo_loop.pause()
            logger.info("DPO Feedback Loop: Pause action triggered.")
            return Response({'status': 'DPO loop paused'})
        elif action == 'stop':
            # dpo_loop.stop()
            logger.info("DPO Feedback Loop: Stop action triggered.")
            return Response({'status': 'DPO loop stopped'})
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(staff_member_required, name='dispatch')
class AdaptersView(APIView):
    def get(self, request):
        container = Container()
        adapters_info = {}
        # Ceci est un exemple, la logique réelle serait d'inspecter le container
        # pour lister les adaptateurs et déterminer lequel est actif
        
        # Placeholder pour les adaptateurs d'inférence
        inference_adapter_name = "GoogleGenAIAdapter" # container.inference.current_adapter_name
        adapters_info['inference'] = {
            'active': inference_adapter_name,
            'available': ["GoogleGenAIAdapter", "OpenAIAdapter", "LocalGuardrailAdapter"]
        }
        # Placeholder pour les adaptateurs de persistance
        persistence_adapter_name = "PGVectorRepositoryAdapter" # container.persistence.current_adapter_name
        adapters_info['persistence'] = {
            'active': persistence_adapter_name,
            'available': ["PGVectorRepositoryAdapter", "ChromaDBAdapter"]
        }
        
        return Response(adapters_info)
```

- [ ] **Step 2: Enregistrer les routes dans `urls.py`**

```python
# backend/api/animetix_project/urls.py
# ... autres imports
from animetix.api.mlops import DPOFeedbackLoopView, AdaptersView # Assurez-vous d'importer ces vues

urlpatterns = [
    # ... autres urls
    path('api/mlops/dpo-loop/', DPOFeedbackLoopView.as_view(), name='dpo-feedback-loop'),
    path('api/mlops/adapters/', AdaptersView.as_view(), name='mlops-adapters'),
    # ...
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/mlops.py backend/api/animetix_project/urls.py
git commit -m "feat: add MLOps API endpoints for DPO and adapters"
```

---

### Task 2: Interface Frontend MLOps Console

**Files:**
- Create: `frontend/src/pages/dev/MLOpsConsolePage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [ ] **Step 1: Créer le composant `MLOpsConsolePage`**

```tsx
import React, { useState, useEffect } from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Loader2, Play, Pause, Square, List } from 'lucide-react';
import { apiClient } from "../../utils/apiClient";
import { useQuery, useMutation } from '@tanstack/react-query';

const MLOpsConsolePage: React.FC = () => {
  const [dpoStatus, setDpoStatus] = useState<string>('idle');
  const [metrics, setMetrics] = useState<any>({});
  const [adapters, setAdapters] = useState<any>({});

  // Fetch DPO status and metrics
  const dpoQuery = useQuery({
    queryKey: ['dpoStatus'],
    queryFn: () => apiClient('/api/mlops/dpo-loop/', { method: 'GET' }),
    onSuccess: (data) => {
      setDpoStatus(data.status);
      setMetrics(data.metrics);
    },
    // refetchInterval: 5000, // Polling toutes les 5 secondes
  });

  // Fetch adapters info
  const adaptersQuery = useQuery({
    queryKey: ['mlopsAdapters'],
    queryFn: () => apiClient('/api/mlops/adapters/', { method: 'GET' }),
    onSuccess: (data) => {
      setAdapters(data);
    },
    // refetchInterval: 10000, // Polling toutes les 10 secondes
  });

  // DPO loop actions
  const dpoMutation = useMutation({
    mutationFn: (action: 'start' | 'pause' | 'stop') => apiClient('/api/mlops/dpo-loop/', {
      method: 'POST',
      body: JSON.stringify({ action })
    }),
    onSuccess: () => dpoQuery.refetch(), // Recharger le statut après une action
  });

  return (
    <AnimatedPage>
      <div className="p-8 min-h-screen bg-[#0a0a12] text-white">
        <h1 className="text-3xl font-black italic manga-font uppercase mb-8">Console MLOps</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* DPO Feedback Loop */}
          <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-purple-400" /> DPO Feedback Loop</h2>
            <p>Statut: <span className={`font-bold ${dpoStatus === 'running' ? 'text-green-500' : dpoStatus === 'paused' ? 'text-yellow-500' : 'text-gray-500'}`}>{dpoStatus.toUpperCase()}</span></p>
            <p>Last Loss: {metrics.last_loss?.toFixed(4) || 'N/A'}</p>
            <p>Last Accuracy: {metrics.last_accuracy?.toFixed(4) || 'N/A'}</p>

            <div className="flex gap-4 mt-4">
              <Button onClick={() => dpoMutation.mutate('start')} disabled={dpoMutation.isPending || dpoStatus === 'running'}>
                {dpoMutation.isPending && dpoMutation.variables === 'start' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Start
              </Button>
              <Button onClick={() => dpoMutation.mutate('pause')} disabled={dpoMutation.isPending || dpoStatus !== 'running'}>
                {dpoMutation.isPending && dpoMutation.variables === 'pause' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />} Pause
              </Button>
              <Button onClick={() => dpoMutation.mutate('stop')} disabled={dpoMutation.isPending || dpoStatus === 'idle'}>
                {dpoMutation.isPending && dpoMutation.variables === 'stop' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />} Stop
              </Button>
            </div>
          </Card>

          {/* Adapters Management */}
          <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-blue-400" /> Gestion des Adaptateurs</h2>
            {Object.entries(adapters).map(([type, adapterInfo]: [string, any]) => (
              <div key={type} className="mb-4">
                <h3 className="text-lg font-semibold capitalize">{type} Adapters:</h3>
                <p>Active: <span className="font-bold text-green-400">{adapterInfo.active}</span></p>
                <p>Available: {adapterInfo.available?.join(', ') || 'N/A'}</p>
              </div>
            ))}
          </Card>
        </div>

        {/* Placeholder for Logs */}
        <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl mt-8">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-yellow-400" /> Logs de Training</h2>
            <div className="h-64 bg-black p-4 rounded-md overflow-auto text-sm font-mono text-gray-300">
                <p>Log line 1...</p>
                <p>Log line 2...</p>
                <p>Log line 3...</p>
            </div>
        </Card>

      </div>
    </AnimatedPage>
  );
};
export default MLOpsConsolePage;
```

- [ ] **Step 2: Ajouter la route dans `LabRoutes.tsx`**

```tsx
// ...
const MLOpsConsolePage = lazy(() => import('../../../pages/dev/MLOpsConsolePage'));
// ...
<Route path="/dev/mlops/" element={<MLOpsConsolePage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/dev/MLOpsConsolePage.tsx frontend/src/features/labs/routes/LabRoutes.tsx
git commit -m "feat: add MLOpsConsolePage"
```
