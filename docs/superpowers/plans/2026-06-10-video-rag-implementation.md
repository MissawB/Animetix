# Video-RAG Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Développer une interface utilisateur dédiée à l'exploration créative de vidéos via RAG, incluant une timeline interactive, recherche sémantique et outils d'extraction.

**Architecture:** Utilisation d'un store Zustand pour gérer l'état de la vidéo (segments, recherche, sélection) et de composants React modulaires pour la timeline, la recherche et l'inspecteur.

**Tech Stack:** React 19, Zustand, TanStack Query, Tailwind CSS, Framer Motion.

---

### Task 1: Scaffold `VideoRagPage` et Routing

**Files:**
- Create: `frontend/src/pages/labs/VideoRagPage.tsx`
- Modify: `frontend/src/features/labs/routes/LabRoutes.tsx`

- [ ] **Step 1: Créer le composant `VideoRagPage` (squelette)**

```tsx
import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const VideoRagPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6">
        <h1 className="text-3xl font-black italic manga-font uppercase">Video-RAG Explorer</h1>
        {/* Zones à implémenter */}
      </div>
    </AnimatedPage>
  );
};

export default VideoRagPage;
```

- [ ] **Step 2: Ajouter la route dans `LabRoutes.tsx`**

```tsx
// Dans LabRoutes.tsx
const VideoRagPage = lazy(() => import('../../../pages/labs/VideoRagPage'));
// ...
<Route path="/lab/video-rag/" element={<VideoRagPage />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/labs/VideoRagPage.tsx frontend/src/features/labs/routes/LabRoutes.tsx
git commit -m "feat: scaffold VideoRagPage and add route"
```

---

### Task 2: Implementer le Store Zustand

**Files:**
- Create: `frontend/src/features/labs/stores/videoRagStore.ts`

- [ ] **Step 1: Définir le store pour gérer les segments et la sélection**

```typescript
import { create } from 'zustand';

interface Segment {
  id: string;
  start: number;
  end: number;
  description: string;
  type: 'emotion' | 'action' | 'dialogue';
}

interface VideoRagState {
  segments: Segment[];
  selectedSegmentId: string | null;
  favorites: string[];
  setSegments: (segments: Segment[]) => void;
  selectSegment: (id: string | null) => void;
  toggleFavorite: (id: string) => void;
}

export const useVideoRagStore = create<VideoRagState>((set) => ({
  segments: [],
  selectedSegmentId: null,
  favorites: [],
  setSegments: (segments) => set({ segments }),
  selectSegment: (id) => set({ selectedSegmentId: id }),
  toggleFavorite: (id) => set((state) => ({
    favorites: state.favorites.includes(id) 
      ? state.favorites.filter(fid => fid !== id) 
      : [...state.favorites, id]
  })),
}));
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/labs/stores/videoRagStore.ts
git commit -m "feat: add videoRagStore for segment management"
```

---

### Task 3: Composant Timeline interactive

**Files:**
- Create: `frontend/src/components/video/Timeline.tsx`

- [ ] **Step 1: Créer le composant Timeline**

```tsx
import React from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';

export const Timeline: React.FC = () => {
  const { segments, selectSegment } = useVideoRagStore();
  
  return (
    <div className="h-24 bg-black/50 border border-white/5 rounded-xl flex items-center px-4 overflow-x-auto">
      {segments.map(seg => (
        <button 
          key={seg.id}
          className={`h-16 w-32 flex-shrink-0 border ${seg.type === 'emotion' ? 'bg-purple-500/30' : 'bg-yellow-500/30'}`}
          onClick={() => selectSegment(seg.id)}
        />
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/video/Timeline.tsx
git commit -m "feat: add Timeline component"
```

---

### Task 4: Composant Inspecteur (Fav/Export)

**Files:**
- Create: `frontend/src/components/video/Inspector.tsx`

- [ ] **Step 1: Créer l'inspecteur**

```tsx
import React from 'react';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { Heart, Download } from 'lucide-react';

export const Inspector: React.FC = () => {
  const { selectedSegmentId, segments, toggleFavorite } = useVideoRagStore();
  const segment = segments.find(s => s.id === selectedSegmentId);

  if (!segment) return <div className="p-4 opacity-50">Sélectionnez un segment</div>;

  return (
    <div className="p-6 bg-navy-950 rounded-xl">
      <p>{segment.description}</p>
      <div className="flex gap-4 mt-4">
        <button onClick={() => toggleFavorite(segment.id)}><Heart /></button>
        <button onClick={() => console.log('Export', segment.id)}><Download /></button>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/video/Inspector.tsx
git commit -m "feat: add Inspector component"
```

---

### Task 5: Integration dans `VideoRagPage`

**Files:**
- Modify: `frontend/src/pages/labs/VideoRagPage.tsx`

- [ ] **Step 1: Intégrer les composants dans la page**

```tsx
// ...
import { Timeline } from "../../components/video/Timeline";
import { Inspector } from "../../components/video/Inspector";

const VideoRagPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6">
        <h1 className="text-3xl font-black italic manga-font uppercase">Video-RAG Explorer</h1>
        <div className="mt-8">
            <Timeline />
            <Inspector />
        </div>
      </div>
    </AnimatedPage>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/labs/VideoRagPage.tsx
git commit -m "feat: integrate video components in VideoRagPage"
```
