import { apiClient } from '../../../utils/apiClient';

export const adminService = { 
  getEval: async () => apiClient('/api/v1/admin/eval/'), 
  getHealth: async () => apiClient('/api/v1/admin/health/') 
};
