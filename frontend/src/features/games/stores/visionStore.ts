import { create } from 'zustand';
import { VisionState } from '../../../types';
import { visionService } from '../services/visionService';

interface VisionStore {
  gameState: VisionState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  restartGame: () => Promise<void>;
  submitGuess: (description: string) => Promise<void>;
}

export const useVisionStore = create<VisionStore>((set) => ({
  gameState: null,
  isLoading: true,
  error: null,

  loadGame: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await visionService.getState();
      set({ gameState: state, isLoading: false });
    } catch {
      try {
        const state = await visionService.startGame();
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
      const state = await visionService.startGame();
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to restart game';
      set({ error: message, isLoading: false });
    }
  },

  submitGuess: async (guess: string) => {
    set({ isLoading: true, error: null });
    try {
      const state = await visionService.submitGuess(guess);
      set({ gameState: state, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit guess';
      set({ error: message, isLoading: false });
    }
  }

}));