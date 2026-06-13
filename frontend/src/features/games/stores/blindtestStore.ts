import { create } from 'zustand';
import { BlindtestState } from '../../../types';
import { blindtestService } from '../services/blindtestService';

interface BlindtestStore {
  gameState: BlindtestState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  restartGame: () => Promise<void>;
  submitGuess: (guess: string) => Promise<void>;
}

export const useBlindtestStore = create<BlindtestStore>((set) => ({
  gameState: null,
  isLoading: true,
  error: null,

  loadGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await blindtestService.getState();
      set({ gameState: state, isLoading: false });
    } catch {
      try {
        const state = await blindtestService.startGame();
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
      const state = await blindtestService.startGame();
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to restart game';
      set({ error: message, isLoading: false });
    }
  },

  submitGuess: async (guess: string) => {
    set({ isLoading: true, error: null });
    try {
      const state = await blindtestService.submitGuess(guess);
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit guess';
      set({ error: message, isLoading: false });
    }
  }
}));