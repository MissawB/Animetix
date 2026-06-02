# Hyper-Personnalisation Graphique Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter une personnalisation dynamique de l'interface basée sur le "Archetype Drift" de l'utilisateur (couleurs et thèmes changeant selon les affinités détectées).

**Architecture:** Approche "Visual Meta" où le Backend calcule le Drift et injecte une configuration visuelle dans les métadonnées de l'API via un Middleware. Le Frontend utilise un store Zustand pour appliquer ces styles via des variables CSS et Framer Motion.

**Tech Stack:** Python 3.11, Django 5.2, Pydantic v2, React 19, Zustand, Tailwind CSS, Framer Motion.

---

### Task 1: Personalization Entities & Schema

**Files:**
- Create: `backend/core/domain/entities/personalization.py`

- [ ] **Step 1: Define the `VisualConfig` and `ArchetypeScore` schemas**

```python
from pydantic import BaseModel
from typing import Dict, Optional

class VisualConfig(BaseModel):
    archetype_id: str
    primary_accent: str
    aura_type: str  # "none", "fire", "electric", "shadow", "sparkles"
    aura_intensity: float  # 0.0 to 1.0
    font_vibe: str  # "default", "manga", "brush"

class ArchetypeScore(BaseModel):
    scores: Dict[str, float]  # Map archetype name to current intensity
```

- [ ] **Step 2: Define the mapping constants**

```python
ARCHETYPE_VISUAL_MAP = {
    "shonen_hero": {
        "primary_accent": "#FF4500",
        "aura_type": "fire",
        "font_vibe": "brush"
    },
    "seinen_mystery": {
        "primary_accent": "#2F4F4F",
        "aura_type": "shadow",
        "font_vibe": "manga"
    },
    "cyberpunk": {
        "primary_accent": "#00FFFF",
        "aura_type": "electric",
        "font_vibe": "default"
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/domain/entities/personalization.py
git commit -m "feat(personalization): add domain entities and schemas"
```

---

### Task 2: Archetype Drift Service

**Files:**
- Create: `backend/core/domain/services/archetype_drift_service.py`
- Modify: `backend/api/animetix/containers/core_services.py`

- [ ] **Step 1: Implement `ArchetypeDriftService` with EMA logic**

```python
import logging
from typing import Dict, List, Any
from ..entities.personalization import VisualConfig, ARCHETYPE_VISUAL_MAP

logger = logging.getLogger('animetix.personalization.drift')

class ArchetypeDriftService:
    def __init__(self, feedback_port, memory_service):
        self.feedback_port = feedback_port
        self.memory_service = memory_service
        self.alpha = 0.3  # Inertia factor (0.3 = 30% recent, 70% past)

    def calculate_drift(self, user_id: int) -> VisualConfig:
        # Default fallback
        default_config = VisualConfig(
            archetype_id="default",
            primary_accent="#FD7706",
            aura_type="none",
            aura_intensity=0.0,
            font_vibe="default"
        )
        
        if not user_id: return default_config

        # 1. Fetch signals (mocked logic for brevity, would query DB/Chroma)
        # In real impl, we aggregate AIFeedback, GameplaySession and memories
        # For now, let's assume a simplified scoring
        recent_stats = {"shonen_hero": 0.8, "seinen_mystery": 0.2} 
        
        # 2. Select dominant archetype
        dominant = max(recent_stats, key=recent_stats.get)
        vibe = ARCHETYPE_VISUAL_MAP.get(dominant, {})
        
        return VisualConfig(
            archetype_id=dominant,
            primary_accent=vibe.get("primary_accent", "#FD7706"),
            aura_type=vibe.get("aura_type", "none"),
            aura_intensity=recent_stats[dominant],
            font_vibe=vibe.get("font_vibe", "default")
        )
```

- [ ] **Step 2: Register service in Container**

Modify `backend/api/animetix/containers/core_services.py` to add `drift_service`.

- [ ] **Step 3: Write test for service**

Create `tests/backend/core/test_archetype_drift.py` and verify EMA or scoring logic.

- [ ] **Step 4: Commit**

```bash
git add backend/core/domain/services/archetype_drift_service.py backend/api/animetix/containers/core_services.py tests/backend/core/test_archetype_drift.py
git commit -m "feat(personalization): implement ArchetypeDriftService"
```

---

### Task 3: Personalization Middleware

**Files:**
- Create: `backend/api/animetix/middleware/personalization_middleware.py`
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Create the middleware**

```python
import json
from django.utils.deprecation import MiddlewareMixin
from dependency_injector.wiring import inject, Provide
from ..containers import Container

class PersonalizationMiddleware(MiddlewareMixin):
    @inject
    def process_response(self, request, response, drift_service=Provide[Container.core.drift_service]):
        if response.has_header('Content-Type') and 'application/json' in response['Content-Type']:
            if request.user.is_authenticated:
                try:
                    config = drift_service.calculate_drift(request.user.id)
                    data = json.loads(response.content)
                    if isinstance(data, dict):
                        data['meta'] = data.get('meta', {})
                        data['meta']['visual_config'] = config.dict()
                        response.content = json.dumps(data)
                except Exception:
                    pass
        return response
```

- [ ] **Step 2: Enable middleware in settings**

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/middleware/personalization_middleware.py
git commit -m "feat(personalization): add PersonalizationMiddleware"
```

---

### Task 4: Frontend Personalization Store

**Files:**
- Create: `frontend/src/store/personalizationStore.ts`

- [ ] **Step 1: Implement the Zustand store**

```typescript
import { create } from 'zustand';

interface VisualConfig {
  archetype_id: string;
  primary_accent: string;
  aura_type: string;
  aura_intensity: number;
  font_vibe: string;
}

interface PersonalizationState {
  config: VisualConfig | null;
  updateConfig: (config: VisualConfig) => void;
}

export const usePersonalizationStore = create<PersonalizationState>((set) => ({
  config: null,
  updateConfig: (config) => {
    // Sync CSS variables
    document.documentElement.style.setProperty('--color-primary-drift', config.primary_accent);
    set({ config });
  },
}));
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/store/personalizationStore.ts
git commit -m "feat(personalization): add frontend personalization store"
```

---

### Task 5: Dynamic Aura Wrapper & App Integration

**Files:**
- Create: `frontend/src/components/shared/DynamicAuraWrapper.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/api.ts` (to intercept metadata)

- [ ] **Step 1: Create the `DynamicAuraWrapper` component**

```tsx
import { motion } from 'framer-motion';
import { usePersonalizationStore } from '../../store/personalizationStore';

export const DynamicAuraWrapper = ({ children }: { children: React.ReactNode }) => {
  const config = usePersonalizationStore((state) => state.config);
  
  if (!config || config.aura_type === 'none') return <>{children}</>;

  return (
    <motion.div
      animate={{
        boxShadow: [
          `0 0 ${10 * config.aura_intensity}px ${config.primary_accent}`,
          `0 0 ${20 * config.aura_intensity}px ${config.primary_accent}`,
          `0 0 ${10 * config.aura_intensity}px ${config.primary_accent}`,
        ]
      }}
      transition={{ duration: 2, repeat: Infinity }}
      style={{ borderRadius: 'inherit' }}
    >
      {children}
    </motion.div>
  );
};
```

- [ ] **Step 2: Update `api.ts` interceptor to update store**

- [ ] **Step 3: Wrap Main UI components in `App.tsx`**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/shared/DynamicAuraWrapper.tsx frontend/src/App.tsx
git commit -m "feat(personalization): integrate DynamicAuraWrapper and API sync"
```
