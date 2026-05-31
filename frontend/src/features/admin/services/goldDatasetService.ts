import { apiClient } from '../../../utils/apiClient';

export const goldDatasetService = {
  getList: async () => {
    return apiClient('/api/v1/mlops/gold-dataset/');
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
