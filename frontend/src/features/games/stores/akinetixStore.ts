import { create } from 'zustand';
import { AkinetixState } from '../../../types';
import { akinetixService } from '../services/akinetixService';

interface AkinetixStore {
  gameState: AkinetixState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  restartGame: () => Promise<void>;
  submitAnswer: (answer: string) => Promise<void>;
  submitConfirmation: (isCorrect: boolean, actualTarget?: string) => Promise<void>;
}

export const useAkinetixStore = create<AkinetixStore>((set) => ({
  gameState: null,
  isLoading: true,
  error: null,

  loadGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await akinetixService.getState();
      set({ gameState: state, isLoading: false });
    } catch {
      try {
        const state = await akinetixService.startGame();
        set({ gameState: state, isLoading: false });
      } catch (err: any) {
        set({ error: err.message || 'Failed to start game', isLoading: false });
      }
    }
  },

  restartGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await akinetixService.startGame();
      set({ gameState: state, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to restart game', isLoading: false });
    }
  },

  submitAnswer: async (answer: string) => {
    set({ isLoading: true, error: null });
    try {
      const state = await akinetixService.submitAnswer(answer);
      set({ gameState: state, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to submit answer', isLoading: false });
    }
  },

  submitConfirmation: async (isCorrect: boolean, actualTarget?: string) => {
    set({ isLoading: true, error: null });
    try {
      await akinetixService.submitConfirmation(isCorrect, actualTarget);
      // Backend resets state on confirmation, we just reload the app state or restart
      window.location.reload();
    } catch (err: any) {
      // Don't reload on error (e.g. cheat detected) so user sees the message
      set({ error: err.message || 'Failed to confirm', isLoading: false });
    }
  }
}));
