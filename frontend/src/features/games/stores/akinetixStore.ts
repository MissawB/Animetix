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

export const useAkinetixStore = create<AkinetixStore>((set, get) => ({
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
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to start game';
        set({ error: message, isLoading: false });
      }
    }
  },

  restartGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await akinetixService.startGame();
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to restart game';
      set({ error: message, isLoading: false });
    }
  },

  submitAnswer: async (answer: string) => {
    // Keep the question card mounted (no global loading skeleton) so the board
    // doesn't flash a completely different layout between questions.
    set({ error: null });
    try {
      const state = await akinetixService.submitAnswer(answer);
      set({ gameState: state });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit answer';
      set({ error: message });
    }
  },

  submitConfirmation: async (isCorrect: boolean, actualTarget?: string) => {
    set({ isLoading: true, error: null });
    try {
      await akinetixService.submitConfirmation(isCorrect, actualTarget);
      // Le backend réinitialise l'état à la confirmation : on relance une partie
      // proprement (au lieu d'un window.location.reload() qui rechargeait l'app).
      await get().restartGame();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to confirm';
      // Don't reload on error (e.g. cheat detected) so user sees the message
      set({ error: message, isLoading: false });
    }
  }
}));
