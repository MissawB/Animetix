# 🎯 Spécification Technique : Renforcement du Typage TypeScript (Harden Frontend Typing)

- **Date :** 2026-05-26
- **Auteur :** Antigravity
- **Statut :** Approuvé (par défaut après timeout)
- **Composants ciblés :** `types/index.ts`, `api.ts`, `features/games/services/`, `features/games/hooks/`, `features/graph/`

---

## 📌 1. Contexte & Problématique
Le frontend React/Vite/TypeScript comporte actuellement plusieurs zones d'ombre de typage en raison de l'utilisation abusive du type `any` et d'assertions forcées (`as unknown as`) :
1. **Assertions forcées dans les pages de Jeu :** Des pages comme `CovertestPage.tsx` doivent forcer des transtypages verbeux en raison de hooks et de services déclarant des retours `Promise<any>`.
2. **Weak Typings dans l'API de Graphe :** La fonction `getGraphNeighborhood` renvoie `{nodes: any[], links: any[]}` au lieu d'utiliser des structures typées solides, affaiblissant le composant `GraphExplorer.tsx`.

---

## 🏗️ 2. Architecture de Résolution

### 2.1 Centralisation des Interfaces de Jeu & Graphe dans `types/index.ts`
Nous déplaçons et déclarons formellement toutes les interfaces manquantes dans le fichier centralisé de types du frontend :

```typescript
// Dans frontend/src/types/index.ts

// Type de couverture (Cover Quest)
export interface CovertestState extends GameState {
  cover_url: string;
  secret_title?: string;
  guesses: Array<{ title: string; is_correct: boolean }>;
}

// Types pour le Graph Explorer
export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
```

### 2.2 Surcharges de Services & Hooks de Jeu Typés
Nous mettons à jour les services pour renvoyer des types précis au lieu d'`any`, et prenons des arguments d'interfaces structurées.

#### Exemple pour `covertestService.ts` :
```typescript
import { CovertestState } from '../../../types';

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

#### Exemple pour `useCovertest.ts` :
```typescript
import { useQuery, useMutation, useQueryClient, UseMutationResult } from '@tanstack/react-query';
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

---

## 🛠️ 3. Fichiers impactés & Plan d'Action

1. **`types/index.ts`** : Ajouter les interfaces de `CovertestState`, `GraphNode`, `GraphLink`, `GraphData`.
2. **`api.ts`** : Typage complet de `getGraphNeighborhood` avec `Promise<GraphData>`.
3. **`features/graph/useGraphData.ts`** : Supprimer les définitions locales de `GraphNode`/`GraphLink` et importer de `types`.
4. **`features/games/services/covertestService.ts`** & **`emojiService.ts`** : Remplacer les types `any` par les interfaces strictes de jeu.
5. **`features/games/hooks/useCovertest.ts`** & **`useEmoji.ts`** : Surcharger React-Query pour utiliser les types exacts.
6. **`features/games/CovertestPage.tsx`** : Supprimer l'assertion `as unknown as` et utiliser le typage natif propre du hook.
