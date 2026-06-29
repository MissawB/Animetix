import { AkinetixState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/akinetix';

interface RawAkinetixState {
  media_type?: string;
  current_question?: string | null;
  history?: Array<{ q: string; a: string }>;
  game_over?: boolean;
  ai_guess?: string | null;
  is_daily?: boolean;
  confidence?: number;
}

// The API returns snake_case; the UI/types use camelCase. apiClient does not
// convert, so map here (otherwise currentQuestion/gameOver/aiGuess are undefined
// and the board renders with no question).
const normalize = (raw: RawAkinetixState): AkinetixState => ({
  gameOver: !!raw.game_over,
  isDaily: !!raw.is_daily,
  mediaType: raw.media_type ?? 'Anime',
  currentQuestion: raw.current_question ?? null,
  aiGuess: raw.ai_guess ?? null,
  history: raw.history ?? [],
  confidence: typeof raw.confidence === 'number' ? raw.confidence : 0,
});

export const akinetixService = {
  getState: async (): Promise<AkinetixState> => {
    return normalize(await apiClient(`${API_BASE}/state/`));
  },

  startGame: async (mediaType?: string, difficulty?: string): Promise<AkinetixState> => {
    const body: Record<string, string> = {};
    if (mediaType) body.media_type = mediaType;
    if (difficulty) body.difficulty = difficulty;
    return normalize(
      await apiClient(`${API_BASE}/start/`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    );
  },

  submitAnswer: async (answer: string): Promise<AkinetixState> => {
    return normalize(
      await apiClient(`${API_BASE}/answer/`, {
        method: 'POST',
        body: JSON.stringify({ answer }),
      }),
    );
  },

  submitConfirmation: async (isCorrect: boolean, actualTarget?: string): Promise<void> => {
    await apiClient(`${API_BASE}/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ correct: isCorrect, actual_target: actualTarget }),
    });
  },
};
