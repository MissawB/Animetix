import { create } from 'zustand';
import { BlindtestState } from '../../../types';
import { blindtestService } from '../services/blindtestService';

interface BlindtestStore {
  gameState: BlindtestState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  restartGame: (type?: 'OP' | 'ED', difficulty?: string) => Promise<void>;
  submitGuess: (guess: string) => Promise<void>;
}

const msg = (err: unknown, fallback: string) =>
  err instanceof Error ? err.message : fallback;

export const useBlindtestStore = create<BlindtestStore>((set, get) => ({
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
        set({ error: msg(err, 'Failed to start game'), isLoading: false });
      }
    }
  },

  restartGame: async (type, difficulty) => {
    set({ isLoading: true, error: null });
    try {
      const state = await blindtestService.startGame({ type, difficulty });
      set({ gameState: state, isLoading: false });
    } catch (err) {
      set({ error: msg(err, 'Failed to restart game'), isLoading: false });
    }
  },

  submitGuess: async (guess: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await blindtestService.submitGuess(guess);
      const prev = get().gameState;
      // Merge so the current track (video_url, theme_type, song…) is preserved.
      set({
        gameState: prev ? { ...prev, ...result } : null,
        isLoading: false,
      });
    } catch (err) {
      set({ error: msg(err, 'Failed to submit guess'), isLoading: false });
    }
  },
}));
