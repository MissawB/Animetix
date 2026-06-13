# MangaReader Multi-Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implémenter un composant `MangaReader` capable de basculer entre trois modes de lecture (Webtoon, Traditionnel, Interactif) avec un état global pour mémoriser le mode préféré.

**Architecture:**
- Créer une nouvelle feature `src/features/manga-reader`.
- Utiliser Zustand pour gérer l'état `readerMode`.
- Créer des composants enfants pour chaque mode (`WebtoonMode`, `TraditionalMode`, `InteractiveMode`).
- Utiliser un conteneur principal `MangaReader` qui switch dynamiquement.

**Tech Stack:** React 19, TypeScript, Tailwind CSS, Zustand.

---

### Task 1: Setup State Management (Zustand)

**Files:**
- Create: `frontend/src/features/manga-reader/stores/useReaderStore.ts`
- Test: `frontend/src/features/manga-reader/stores/useReaderStore.test.ts`

- [ ] **Step 1: Write test for reader store**
```typescript
import { useReaderStore } from './useReaderStore';
import { act } from '@testing-library/react';

test('should switch reader mode', () => {
  const { result } = renderHook(() => useReaderStore());
  act(() => result.current.setMode('webtoon'));
  expect(result.current.mode).toBe('webtoon');
});
```
- [ ] **Step 2: Implement store**
```typescript
import { create } from 'zustand';

type ReaderMode = 'webtoon' | 'traditional' | 'interactive';

interface ReaderStore {
  mode: ReaderMode;
  setMode: (mode: ReaderMode) => void;
}

export const useReaderStore = create<ReaderStore>((set) => ({
  mode: 'traditional',
  setMode: (mode) => set({ mode }),
}));
```
- [ ] **Step 3: Run test and commit**

### Task 2: Implement Base Component and Switcher

**Files:**
- Create: `frontend/src/features/manga-reader/components/MangaReader.tsx`
- Modify: `frontend/src/features/manga-reader/index.ts`

- [ ] **Step 1: Create MangaReader container**
```tsx
import React from 'react';
import { useReaderStore } from '../stores/useReaderStore';

export const MangaReader: React.FC = () => {
  const { mode, setMode } = useReaderStore();
  
  return (
    <div className="w-full h-full">
      <div className="flex gap-2 mb-4">
        {['webtoon', 'traditional', 'interactive'].map((m) => (
          <button 
            key={m} 
            onClick={() => setMode(m as any)}
            className={mode === m ? 'bg-anime-accent' : 'bg-gray-800'}
          >
            {m}
          </button>
        ))}
      </div>
      {/* Component mode switch here */}
    </div>
  );
};
```
- [ ] **Step 2: Commit**

### Task 3: Implement Mode Components (Stub)

**Files:**
- Create: `frontend/src/features/manga-reader/components/modes/WebtoonMode.tsx`
- Create: `frontend/src/features/manga-reader/components/modes/TraditionalMode.tsx`
- Create: `frontend/src/features/manga-reader/components/modes/InteractiveMode.tsx`

- [ ] **Step 1: Create stub components**
- [ ] **Step 2: Update MangaReader to switch between them**
- [ ] **Step 3: Commit**
