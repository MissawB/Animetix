# Frontend TypeScript Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate weak frontend typings in the React + TypeScript app by centralizing typings, hardening API queries, and eliminating `as unknown as` casting on game state components.

**Architecture:** Centralize `CovertestState` and `GraphData` structures in `types/index.ts`, and cascade strictly-typed flows through api queries, React-Query hooks, and component states.

**Tech Stack:** React 18, TypeScript 5, Vite, TailwindCSS.

---

### Task 1: Centralize Typings & Harden Graph API

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/features/graph/useGraphData.ts`
- Modify: `frontend/src/features/graph/GraphExplorer.tsx`

- [ ] **Step 1: Declare strict types in types/index.ts**
Add these interfaces to `frontend/src/types/index.ts`:
```typescript
export interface CovertestState extends GameState {
  cover_url: string;
  secret_title?: string;
  guesses: Array<{ title: string; is_correct: boolean }>;
}

export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
```

- [ ] **Step 2: Update api.ts to return typed GraphData**
Update `getGraphNeighborhood` signature in `frontend/src/api.ts`:
```typescript
import { GraphData } from './types';

// --- Graph API ---
export async function getGraphNeighborhood(id: string, type: string, depth: number = 1): Promise<GraphData> {
  return apiClient(`/api/v1/graph/neighbors/?id=${id}&type=${type}&depth=${depth}`);
}
```

- [ ] **Step 3: Update useGraphData.ts to import central types**
Clean up local duplicate definitions in `frontend/src/features/graph/useGraphData.ts`:
```typescript
import { useState, useEffect } from 'react';
import { getGraphNeighborhood } from '../../api';
import { GraphData } from '../../types';

export function useGraphData(id: string, type: string, depth: number) {
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // ... rest of useGraphData hook remains unchanged ...
```

- [ ] **Step 4: Update GraphExplorer.tsx to remove dynamic as casts**
Update variable bindings in `frontend/src/features/graph/GraphExplorer.tsx` (L63-71):
```typescript
          <ForceGraph2D
            graphData={data}
            nodeAutoColorBy={(node) => (node as GraphNode).labels?.[0]}
            nodeColor={(node) => getNodeColor(node as GraphNode)}
            nodeLabel={(node) => getLabel(node as GraphNode)}
            linkLabel={(link) => (link as GraphLink).type}
            backgroundColor="#111827"
          />
```
*Note: Make sure to import `GraphNode` and `GraphLink` from `../../types` in GraphExplorer.tsx.*

- [ ] **Step 5: Run compiler to verify graph explorer builds cleanly**
Run:
```powershell
npx tsc --noEmit --project frontend/tsconfig.json
```
Expected: Success (no compile errors for graph explorer modules).

- [ ] **Step 6: Commit**
```bash
git add frontend/src/types/index.ts frontend/src/api.ts frontend/src/features/graph/useGraphData.ts frontend/src/features/graph/GraphExplorer.tsx
git commit -m "feat: centralize graph typings and strictly type GraphExplorer components"
```

---

### Task 2: Harden Game Services, Hooks & Covertest Page

**Files:**
- Modify: `frontend/src/features/games/services/covertestService.ts`
- Modify: `frontend/src/features/games/services/emojiService.ts`
- Modify: `frontend/src/features/games/hooks/useCovertest.ts`
- Modify: `frontend/src/features/games/hooks/useEmoji.ts`
- Modify: `frontend/src/features/games/CovertestPage.tsx`

- [ ] **Step 1: Harden covertestService.ts and emojiService.ts**
Update `frontend/src/features/games/services/covertestService.ts`:
```typescript
import { apiClient } from '../../../utils/apiClient';
import { CovertestState } from '../../../types';

const API_BASE = '/api/v1/game/covertest';

export interface CovertestGuessRequest {
  guess: string;
}

export const covertestService = {
  getState: async (): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: CovertestGuessRequest): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
```
Update `frontend/src/features/games/services/emojiService.ts`:
```typescript
import { apiClient } from '../../../utils/apiClient';
import { EmojiState } from '../../../types';

const API_BASE = '/api/v1/game/emoji';

export interface EmojiGuessRequest {
  guess: string;
}

export const emojiService = {
  getState: async (): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: EmojiGuessRequest): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
```

- [ ] **Step 2: Harden useCovertest.ts and useEmoji.ts hooks**
Update `frontend/src/features/games/hooks/useCovertest.ts`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { covertestService, CovertestGuessRequest } from '../services/covertestService';
import { CovertestState } from '../../../types';

export const useCovertest = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['covertest-state'];

  const { data: gameState, isLoading: loading } = useQuery<CovertestState>({
    queryKey: QUERY_KEY,
    queryFn: () => covertestService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation<CovertestState, Error, CovertestGuessRequest>({
    mutationFn: covertestService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
  };
};
```
Update `frontend/src/features/games/hooks/useEmoji.ts`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { emojiService, EmojiGuessRequest } from '../services/emojiService';
import { EmojiState } from '../../../types';

export const useEmoji = () => {
  const queryClient = useQueryClient();
  const QUERY_KEY = ['emoji-state'];

  const { data: gameState, isLoading: loading } = useQuery<EmojiState>({
    queryKey: QUERY_KEY,
    queryFn: () => emojiService.getState(),
    refetchOnWindowFocus: false,
  });

  const guessMutation = useMutation<EmojiState, Error, EmojiGuessRequest>({
    mutationFn: emojiService.submit,
    onSuccess: (newState) => {
      queryClient.setQueryData(QUERY_KEY, newState);
    },
  });

  return {
    gameState,
    loading,
    handleGuess: guessMutation.mutateAsync,
  };
};
```

- [ ] **Step 3: Update CovertestPage.tsx to use typed hook outputs**
Update `frontend/src/features/games/CovertestPage.tsx`:
- Delete the duplicate local `interface CovertestState`.
- Import `CovertestState` from `../../types`.
- Simplify hook invocation to eliminate unsafe casting:
```typescript
import React, { useState } from 'react';
import { ImageIcon, Send, RotateCcw } from 'lucide-react';
import { useCovertest } from './hooks/useCovertest';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { CovertestState } from '../../types';

const CovertestPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, loading, handleGuess } = useCovertest();
  const [guess, setGuess] = useState<string>('');

  const onSubmit = async () => {
    await handleGuess({ guess });
    setGuess('');
  };
  
  // ... rest of page rendering continues to use typed gameState ...
```

- [ ] **Step 4: Run compiler to verify the entire frontend builds successfully**
Run:
```powershell
npm run build --prefix frontend
```
Expected: SUCCESS (compiles completely with no types errors).

- [ ] **Step 5: Commit**
```bash
git add frontend/src/features/games/services/covertestService.ts frontend/src/features/games/services/emojiService.ts frontend/src/features/games/hooks/useCovertest.ts frontend/src/features/games/hooks/useEmoji.ts frontend/src/features/games/CovertestPage.tsx
git commit -m "feat: strictly type game services and hooks, removing unsafe page casting"
```
