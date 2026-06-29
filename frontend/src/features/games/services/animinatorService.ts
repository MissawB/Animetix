import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/animinator';

export interface AniminatorResponse {
  answer: string;
  questions_left: number;
  error?: string;
}

export interface AniminatorGuessResponse {
  correct: boolean;
  game_over: boolean;
  secret: string | null;
  error?: string;
}

export const animinatorService = {
  ask: async (question: string, mediaType?: string): Promise<AniminatorResponse> => {
    return apiClient(`${API_BASE}/ask/`, {
      method: 'POST',
      body: JSON.stringify(mediaType ? { question, media_type: mediaType } : { question }),
    });
  },
  guess: async (guess: string): Promise<AniminatorGuessResponse> => {
    return apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ guess }),
    });
  },
};
