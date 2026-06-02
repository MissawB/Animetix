import { AkinetixState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/akinetix';

export const akinetixService = {
  getState: async (): Promise<AkinetixState> => {
    return apiClient(`${API_BASE}/state/`);
  },

  startGame: async (): Promise<AkinetixState> => {
    return apiClient(`${API_BASE}/start/`, { method: 'POST' });
  },

  submitAnswer: async (answer: string): Promise<AkinetixState> => {
    return apiClient(`${API_BASE}/answer/`, {
      method: 'POST',
      body: JSON.stringify({ answer })
    });
  },

  submitConfirmation: async (isCorrect: boolean, actualTarget?: string): Promise<void> => {
    return apiClient(`${API_BASE}/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ correct: isCorrect, actual_target: actualTarget })
    });
  }
};

