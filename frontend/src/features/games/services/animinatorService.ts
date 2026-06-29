import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/animinator';

export interface AniminatorResponse {
  answer: string;
  questions_left: number;
  error?: string;
}

export const animinatorService = {
  ask: async (question: string, mediaType?: string): Promise<AniminatorResponse> => {
    return apiClient(`${API_BASE}/ask/`, {
      method: 'POST',
      body: JSON.stringify(mediaType ? { question, media_type: mediaType } : { question }),
    });
  }
};
