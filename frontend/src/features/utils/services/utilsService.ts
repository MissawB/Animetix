import { apiClient } from '../../../utils/apiClient';
import type { UserConfig } from '../../../types';

export const utilsService = {
  getDaily: async (date?: string) =>
    apiClient(`/api/v1/daily-challenge/${date ? `?date=${encodeURIComponent(date)}` : ''}`),
  getConfig: async () => apiClient('/api/v1/custom-config/'),
  updateConfig: async (config: Partial<UserConfig>) =>
    apiClient('/api/v1/custom-config/', { method: 'POST', body: JSON.stringify(config) }),
};
