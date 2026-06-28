import { BlindtestState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/blindtest';

interface RawBlindtestState {
  video_url?: string;
  theme_type?: string;
  blindtest_song?: string;
  blindtest_artists?: string[];
  guesses?: Array<{ title: string; is_correct: boolean }>;
  game_over?: boolean;
  won?: boolean;
  is_daily?: boolean;
  secret_title?: string;
  difficulty?: string;
  max_attempts?: number;
  attempts_left?: number;
}

export interface GuessResult {
  gameOver: boolean;
  won: boolean;
  guesses: Array<{ title: string; is_correct: boolean }>;
  secret_title?: string;
  attemptsLeft?: number;
}

const normalize = (raw: RawBlindtestState): BlindtestState => ({
  gameOver: !!raw.game_over,
  isDaily: !!raw.is_daily,
  mediaType: 'Anime',
  video_url: raw.video_url,
  secret_title: raw.secret_title,
  theme_type: raw.theme_type,
  song: raw.blindtest_song,
  artists: raw.blindtest_artists,
  won: raw.won,
  difficulty: raw.difficulty,
  maxAttempts: raw.max_attempts,
  attemptsLeft: raw.attempts_left,
  guesses: raw.guesses ?? [],
});

export const blindtestService = {
  getState: async (): Promise<BlindtestState> => {
    // No active game yields a 400 — let the store fall back to startGame without a toast.
    return normalize(await apiClient(`${API_BASE}/state/`, { skipToast: true }));
  },

  startGame: async (
    opts: { type?: 'OP' | 'ED'; difficulty?: string; isDaily?: boolean } = {},
  ): Promise<BlindtestState> => {
    return normalize(
      await apiClient(`${API_BASE}/start/`, {
        method: 'POST',
        body: JSON.stringify({
          is_daily: opts.isDaily ?? false,
          type: opts.type,
          difficulty: opts.difficulty,
        }),
      }),
    );
  },

  getTitles: async (): Promise<string[]> => {
    const data = (await apiClient(`${API_BASE}/titles/`, { skipToast: true })) as { titles?: string[] };
    return data?.titles ?? [];
  },

  submitGuess: async (guess: string): Promise<GuessResult> => {
    const raw = (await apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ guess }),
    })) as RawBlindtestState;
    return {
      gameOver: !!raw.game_over,
      won: !!raw.won,
      guesses: raw.guesses ?? [],
      secret_title: raw.secret_title,
      attemptsLeft: raw.attempts_left,
    };
  },
};
