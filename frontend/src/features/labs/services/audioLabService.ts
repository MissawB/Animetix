import { AudioLabState } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/labs/audio';

export interface AudioProcessPayload {
  media_id: string;
  source_lang: string;
  target_lang: string;
}

export const audioLabService = {
  getState: async (): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/`);
  },
  process: async (data: AudioProcessPayload): Promise<AudioLabState> => {
    return apiClient(`${API_BASE}/process/`, { method: 'POST', body: JSON.stringify(data) });
  },
  searchSeiyuu: async (query: string): Promise<any> => {
    return apiClient(`${API_BASE}/seiyuu/?q=${encodeURIComponent(query)}`);
  }
};
