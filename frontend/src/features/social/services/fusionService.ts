import { apiClient } from '../../../utils/apiClient';
import { CreativeFusion } from '../../../types';

export const fusionService = {
  getFeed: async (): Promise<CreativeFusion[]> => {
    const data = await apiClient('/api/v1/fusions/');
    return Array.isArray(data) ? data : data.results || [];
  },
  
  likeFusion: async (id: number): Promise<{ status: string, likes_count: number }> => {
    return apiClient(`/api/v1/fusions/${id}/like/`, { method: 'POST' });
  },
  
  remixFusion: async (id: number): Promise<CreativeFusion> => {
    return apiClient(`/api/v1/fusions/${id}/remix/`, { method: 'POST' });
  }
};
