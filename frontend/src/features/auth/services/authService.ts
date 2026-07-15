import { User } from '../../../types';
import { apiClient } from '../../../utils/apiClient';

export const authService = {
  getAuthUser: async (): Promise<User> => {
    const profile = await apiClient<{
      user: { id: number; username: string; email: string; is_staff: boolean };
      xp: number;
      tier: string;
      wallet_balance: number;
      has_api_key: boolean;
      unlocked_badges: string[];
      custom_username_color?: string;
    }>('/api/v1/auth/me/', { skipToast: true });
    return {
      id: profile.user.id,
      username: profile.user.username,
      email: profile.user.email,
      is_staff: profile.user.is_staff,
      is_authenticated: true,
      xp: profile.xp,
      tier: profile.tier,
      wallet_balance: profile.wallet_balance,
      has_api_key: profile.has_api_key,
      unlocked_badges: profile.unlocked_badges,
      custom_username_color: profile.custom_username_color,
    };
  },
};
