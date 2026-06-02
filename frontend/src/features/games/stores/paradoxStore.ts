import { create } from 'zustand';
import { ParadoxState } from '../../../types';
import { paradoxService } from '../services/paradoxService';

interface ParadoxStore {
  gameState: ParadoxState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  submitGuess: (itemId: number) => Promise<void>;
}

export const useParadoxStore = create<ParadoxStore>((set) => ({
  gameState: null,
  isLoading: true,
  error: null,

  loadGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await paradoxService.getState();
      set({ gameState: state, isLoading: false });
    } catch {
      try {
        // Fallback pour démarrer si pas d'état actif
        const res = await fetch('/api/v1/game/paradox/start/', { method: 'POST' });
        const state = await res.json();
        if (!res.ok) throw new Error(state.error || 'Failed to start game');
        set({ gameState: state, isLoading: false });
      } catch (err: any) {
        set({ error: err.message || 'Failed to start game', isLoading: false });
      }
    }
  },

  submitGuess: async (itemId: number) => {
    set({ isLoading: true, error: null });
    try {
      const state = await paradoxService.submit({ intruder_id: itemId });
      set({ gameState: state, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to submit guess', isLoading: false });
    }
  }
}));