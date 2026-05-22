import { apiClient } from '../../../utils/apiClient';

export const utilsService = { 
  getDaily: async () => apiClient('/api/v1/utils/daily/'), 
  getConfig: async () => apiClient('/api/v1/utils/config/') 
};
