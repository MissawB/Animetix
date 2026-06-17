import { SocialDashboardData, DiscoveryClub, ClubEvent } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

const API_BASE = '/api/v1/social';

export const socialService = {
  getDashboard: async (): Promise<SocialDashboardData> => {
    return apiClient(`${API_BASE}/dashboard/`);
  },

  toggleFollow: async (userId: number): Promise<void> => {
    return apiClient(`${API_BASE}/${userId}/toggle_follow/`, { method: 'POST' });
  },

  createClub: async (data: { name: string, description: string, theme: string, is_private: boolean }): Promise<DiscoveryClub> => {
    return apiClient('/api/v1/clubs/', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' }
    });
  },

  getClubDetails: async (id: number): Promise<DiscoveryClub> => {
    return apiClient(`/api/v1/clubs/${id}/`);
  },

  getClubEvents: async (clubId: number): Promise<ClubEvent[]> => {
    return apiClient(`/api/v1/club-events/?club=${clubId}`);
  }
};
