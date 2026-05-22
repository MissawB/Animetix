import { ClassicGameState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/classic';

export const classicGameService = {
  getState: async (): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  
  submit: async (data: any): Promise<ClassicGameState> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
