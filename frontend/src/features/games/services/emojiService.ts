import { apiClient } from '../../../utils/apiClient';
import { EmojiState } from '../../../types';

const API_BASE = '/api/v1/game/emoji';

export interface EmojiGuessRequest {
  guess: string;
}

export const emojiService = {
  getState: async (): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  start: async (mediaType?: string): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify(mediaType ? { media_type: mediaType } : {}),
    });
  },
  submit: async (data: EmojiGuessRequest): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};

