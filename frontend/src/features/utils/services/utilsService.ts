import { apiClient } from '../../../utils/apiClient';

export const utilsService = { 
  getDaily: async () => apiClient('/api/v1/daily-challenge/'), 
  getConfig: async () => apiClient('/api/v1/custom-config/') 
};
