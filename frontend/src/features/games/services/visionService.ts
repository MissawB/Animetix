import { VisionState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/vision';

export const visionService = {
  getState: async (): Promise<VisionState> => {
    return apiClient(`${API_BASE}/state/`);
  },

  startGame: async (): Promise<VisionState> => {
    return apiClient(`${API_BASE}/start/`, { method: 'POST' });
  },

  submitGuess: async (description: string): Promise<VisionState> => {
    return apiClient(`${API_BASE}/guess/`, {
      method: 'POST',
      body: JSON.stringify({ description })
    });
  }
};
