import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/paradox';

export const paradoxService = {
  getState: async (): Promise<any> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: any): Promise<any> => {
    return apiClient(`${API_BASE}/move/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
