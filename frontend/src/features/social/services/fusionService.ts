import { apiClient } from '../../../utils/apiClient';
import { CreativeFusion } from '../../../types';

export const fusionService = {
  getFeed: async (): Promise<CreativeFusion[]> => {
    return apiClient('/api/v1/fusions/');
  },
  
  likeFusion: async (id: number): Promise<{ status: string, likes_count: number }> => {
    return apiClient(`/api/v1/fusions/${id}/like/`, { method: 'POST' });
  },
  
  remixFusion: async (id: number): Promise<CreativeFusion> => {
    return apiClient(`/api/v1/fusions/${id}/remix/`, { method: 'POST' });
  }
};
