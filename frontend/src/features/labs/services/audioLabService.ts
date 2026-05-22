import { AudioLabState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/lab/audio';

export const audioLabService = {
  getState: async (): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/state/`);
  },
  process: async (data: any): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/process/`, { method: 'POST', body: JSON.stringify(data) });
  }
};
