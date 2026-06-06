import { apiClient } from '../../../utils/apiClient';

export const goldDatasetService = {
  getList: async () => {
    const data = await apiClient('/api/v1/mlops/gold-dataset/');
    return data.results || data;
  },
  
  validateEntry: async (id: number) => {
    return apiClient(`/api/v1/mlops/gold-dataset/${id}/validate/`, { method: 'POST' });
  },
  
  syncPositiveFeedback: async () => {
    return apiClient('/api/v1/mlops/gold-dataset/sync_positive_feedback/', { method: 'POST' });
  },
  
  deleteEntry: async (id: number) => {
    return apiClient(`/api/v1/mlops/gold-dataset/${id}/`, { method: 'DELETE' });
  }
};
