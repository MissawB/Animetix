import {
  SocialDashboardData,
  DiscoveryClub,
  ClubEvent,
  User,
  Profile,
  TrackerConnection,
  AIUsageData,
} from '../../../types';
import { apiClient } from '../../../utils/apiClient';
import { TrackerLinkSummary } from '../types/profileTypes';

const API_BASE = '/api/v1/social';

export const socialService = {
  getDashboard: async (): Promise<SocialDashboardData> => {
    return apiClient(`${API_BASE}/dashboard/`);
  },

  toggleFollow: async (userId: number): Promise<void> => {
    return apiClient(`${API_BASE}/${userId}/toggle_follow/`, { method: 'POST' });
  },

  createClub: async (data: Partial<DiscoveryClub>): Promise<DiscoveryClub> => {
    return apiClient('/api/v1/clubs/', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' },
    });
  },

  getClubDetails: async (id: number): Promise<DiscoveryClub> => {
    return apiClient(`/api/v1/clubs/${id}/`);
  },

  joinClub: async (id: number): Promise<{ status: string }> => {
    return apiClient(`/api/v1/clubs/${id}/join/`, { method: 'POST' });
  },

  leaveClub: async (id: number): Promise<{ status: string }> => {
    return apiClient(`/api/v1/clubs/${id}/leave/`, { method: 'POST' });
  },

  getClubEvents: async (clubId: number): Promise<ClubEvent[]> => {
    return apiClient(`/api/v1/club-events/?club=${clubId}`);
  },

  getClubEventDetails: async (eventId: number): Promise<ClubEvent> => {
    return apiClient(`/api/v1/club-events/${eventId}/`);
  },

  toggleEventParticipation: async (
    eventId: number,
  ): Promise<{ status: string; participants_count: number }> => {
    return apiClient(`/api/v1/club-events/${eventId}/join/`, { method: 'POST' });
  },

  createClubEvent: async (data: Partial<ClubEvent>): Promise<ClubEvent> => {
    return apiClient('/api/v1/club-events/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getLeaderboard: async (): Promise<Profile[]> => {
    // Classement par XP (la page Hall of Fame est centrée sur l'XP).
    return apiClient('/api/v1/leaderboard/?mode=xp');
  },

  searchUsers: async (query: string): Promise<(User & { is_following: boolean })[]> => {
    return apiClient(`/api/v1/social/search/?q=${encodeURIComponent(query)}`);
  },

  getProfile: async (username: string): Promise<Profile> => {
    return apiClient(`/api/v1/profile/${username}/`);
  },

  uploadAvatar: async (file: File): Promise<Profile> => {
    const form = new FormData();
    form.append('avatar', file);
    return apiClient('/api/v1/profiles/avatar/', {
      method: 'POST',
      body: form,
      isFormData: true,
    });
  },

  updateAccountSettings: async (data: {
    tier?: string;
    custom_username_color?: string;
  }): Promise<{ status: string; tier: string; custom_username_color?: string }> => {
    return apiClient('/api/v1/profiles/update_settings/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  getAIUsage: async (): Promise<AIUsageData> => {
    return apiClient('/api/v1/profiles/usage/');
  },

  getTrackerConnections: async (): Promise<TrackerConnection[]> => {
    return apiClient('/api/v1/profile/trackers/');
  },

  linkTracker: async (
    tracker: string,
    username: string,
    token: string,
  ): Promise<{ success: boolean }> => {
    return apiClient('/api/v1/profile/trackers/link/', {
      method: 'POST',
      body: JSON.stringify({ tracker, username, token }),
    });
  },

  unlinkTracker: async (tracker: string): Promise<{ success: boolean }> => {
    return apiClient('/api/v1/profile/trackers/unlink/', {
      method: 'POST',
      body: JSON.stringify({ tracker }),
    });
  },

  getTrackerLinks: async (): Promise<TrackerLinkSummary[]> => {
    return apiClient('/api/v1/profile/trackers/links/');
  },

  unlinkTrackerLink: async (mangaId: string, tracker: string): Promise<{ success: boolean }> => {
    return apiClient(`/api/v1/media/Manga/${mangaId}/trackers/${tracker}/`, {
      method: 'DELETE',
    });
  },

  getAchievements: async () => {
    return apiClient('/api/v1/achievements/');
  },

  getGameplayHistory: async (limit: number = 10) => {
    return apiClient(`/api/v1/social/gameplay-history/?limit=${limit}`);
  },
};
