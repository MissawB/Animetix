import { BlindtestState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/blindtest';

export const blindtestService = {
  getState: async (): Promise<BlindtestState> => {
    return apiClient(`${API_BASE}/state/`);
  },

  startGame: async (): Promise<BlindtestState> => {
    return apiClient(`${API_BASE}/start/`, { method: 'POST' });
  },

  submitGuess: async (guess: string): Promise<BlindtestState> => {
    return apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ guess })
    });
  }
};
