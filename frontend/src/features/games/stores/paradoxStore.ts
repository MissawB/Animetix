import { create } from 'zustand';
import { ParadoxState } from '../../../types';
import { paradoxService } from '../services/paradoxService';
import { apiClient } from '../../../utils/apiClient';

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
        const state = await apiClient('/api/v1/game/paradox/start/', { method: 'POST' });
        set({ gameState: state, isLoading: false });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to start game';
        set({ error: message, isLoading: false });
      }
    }
  },

  submitGuess: async (itemId: number) => {
    set({ isLoading: true, error: null });
    try {
      const state = await paradoxService.submit({ intruder_id: itemId });
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit guess';
      set({ error: message, isLoading: false });
    }
  }
}));