import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/game/covertest';

export const covertestService = {
  getState: async (): Promise<any> => {
    return apiClient(`${API_BASE}/state/`);
  },
  submit: async (data: any): Promise<any> => {
    return apiClient(`${API_BASE}/guess/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
