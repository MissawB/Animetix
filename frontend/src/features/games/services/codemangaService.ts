import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/codemanga';

export const codemangaService = {
  getState: async (code: string): Promise<any> => {
    return apiClient(`${API_BASE}/room/${code}`);
  },
  submit: async (data: any): Promise<any> => {
    return apiClient(`${API_BASE}/action/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
