import { apiClient } from '../../../utils/apiClient';
import { EmojiState } from '../../../types';

const API_BASE = '/api/v1/game/emoji';

export interface EmojiGuessRequest {
  guess: string;
}

export interface EmojiSuggestion {
  title: string;
  title_english?: string | null;
  title_native?: string | null;
  image?: string | null;
}

export const emojiService = {
  getState: async (): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  start: async (mediaType?: string, difficulty?: string): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify({
        ...(mediaType ? { media_type: mediaType } : {}),
        ...(difficulty ? { difficulty } : {}),
      }),
    });
  },
  submit: async (data: EmojiGuessRequest): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  },
  giveUp: async (): Promise<EmojiState> => {
    return apiClient(`${API_BASE}/giveup/`, { method: 'POST', body: JSON.stringify({}) });
  },
  suggest: async (q: string): Promise<EmojiSuggestion[]> => {
    const data = (await apiClient(`${API_BASE}/suggest/?q=${encodeURIComponent(q)}`, {
      skipToast: true,
    })) as { suggestions?: EmojiSuggestion[] };
    return data?.suggestions ?? [];
  },
};

