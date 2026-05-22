import { SocialDashboardData } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/social';

export const socialService = {
  getDashboard: async (): Promise<SocialDashboardData> => {
    return apiClient(`${API_BASE}/dashboard/`);
  },

  toggleFollow: async (userId: number): Promise<void> => {
    return apiClient(`${API_BASE}/${userId}/toggle_follow/`, { method: 'POST' });
  }
};
