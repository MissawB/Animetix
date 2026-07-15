import { z } from 'zod';
import { BlindtestState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/blindtest';

const RawBlindtestStateSchema = z.object({
  video_url: z.string().optional(),
  theme_type: z.string().optional(),
  blindtest_sequence: z.union([z.number(), z.string()]).nullable().optional(),
  blindtest_song: z.string().optional(),
  blindtest_artists: z.array(z.string()).optional(),
  guesses: z
    .array(
      z.object({
        title: z.string(),
        is_correct: z.boolean(),
      }),
    )
    .optional(),
  game_over: z.boolean().optional(),
  won: z.boolean().optional(),
  is_daily: z.boolean().optional(),
  secret_title: z.string().optional(),
  secret_image: z.string().nullable().optional(),
  difficulty: z.string().optional(),
  max_attempts: z.number().optional(),
  attempts_left: z.number().optional(),
});

type RawBlindtestState = z.infer<typeof RawBlindtestStateSchema>;

export interface GuessResult {
  gameOver: boolean;
  won: boolean;
  guesses: Array<{ title: string; is_correct: boolean }>;
  secret_title?: string;
  secret_image?: string | null;
  attemptsLeft?: number;
}

const normalize = (raw: RawBlindtestState): BlindtestState => ({
  gameOver: !!raw.game_over,
  isDaily: !!raw.is_daily,
  mediaType: 'Anime',
  video_url: raw.video_url,
  secret_title: raw.secret_title,
  secret_image: raw.secret_image ?? undefined,
  theme_type: raw.theme_type,
  sequence: raw.blindtest_sequence ?? undefined,
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
    const data = await apiClient(`${API_BASE}/state/`, { skipToast: true });
    return normalize(RawBlindtestStateSchema.parse(data));
  },

  startGame: async (
    opts: { type?: 'OP' | 'ED'; difficulty?: string; isDaily?: boolean } = {},
  ): Promise<BlindtestState> => {
    const data = await apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify({
        is_daily: opts.isDaily ?? false,
        type: opts.type,
        difficulty: opts.difficulty,
      }),
    });
    return normalize(RawBlindtestStateSchema.parse(data));
  },

  getTitles: async (): Promise<string[]> => {
    const data = await apiClient<{ titles?: string[] }>(`${API_BASE}/titles/`, { skipToast: true });
    return data?.titles ?? [];
  },

  submitGuess: async (guess: string): Promise<GuessResult> => {
    const data = await apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ guess }),
    });
    const raw = RawBlindtestStateSchema.parse(data);
    return {
      gameOver: !!raw.game_over,
      won: !!raw.won,
      guesses: raw.guesses ?? [],
      secret_title: raw.secret_title,
      secret_image: raw.secret_image ?? undefined,
      attemptsLeft: raw.attempts_left,
    };
  },
};
