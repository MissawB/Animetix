import { apiClient } from '../../../utils/apiClient';
import { CovertestState } from '../../../types';

const API_BASE = '/api/v1/game/covertest';

export interface CovertestGuessRequest {
  guess: string;
}

// A guessable manga: its canonical (Japanese romaji) title plus searchable aliases
// (English / native / synonyms) so it can be found by either name.
export interface CovertestTitle {
  title: string;
  aliases: string[];
}

export const covertestService = {
  getState: async (): Promise<CovertestState> => {
    // Probe : peut auto-démarrer côté backend ; le toast d'erreur éventuel est évité.
    return apiClient(`${API_BASE}/state/`, { skipToast: true });
  },
  start: async (isDaily = false, origin?: string): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/start/`, {
      method: 'POST',
      body: JSON.stringify({ is_daily: isDaily, origin: origin || undefined }),
    });
  },
  submit: async (data: CovertestGuessRequest): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  },
  reveal: async (): Promise<CovertestState> => {
    return apiClient(`${API_BASE}/reveal/`, { method: 'POST' });
  },
  getTitles: async (): Promise<CovertestTitle[]> => {
    const data = (await apiClient(`${API_BASE}/titles/`, { skipToast: true })) as { titles?: CovertestTitle[] };
    return data?.titles ?? [];
  },
};
