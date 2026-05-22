import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/animinator';

export const animinatorService = {
  getState: async (): Promise<any> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: any): Promise<any> => {
    return apiClient(`${API_BASE}/frame/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
