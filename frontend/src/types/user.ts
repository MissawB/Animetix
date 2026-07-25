import type { components } from './api';

type ApiAchievement = components['schemas']['Achievement'];
type ApiCreativeFusion = components['schemas']['CreativeFusion'];

export interface User {
  id: number;
  username: string;
  email: string;
  is_authenticated: boolean;
  avatar?: string;
  xp?: number;
  level?: number;
  tier?: string;
  has_api_key?: boolean;
  is_staff?: boolean;
  unlocked_badges?: string[];
  custom_username_color?: string;
  // Returned by the wallet/balance endpoint; backend serializer must expose it.
  wallet_balance?: number;
}

export interface Profile {
  username: string;
  xp: number;
  level: number;
  avatar?: string | null;
  rank?: string;
  achievements_count?: number;
  collection_count?: number;
  recent_achievements?: ApiAchievement[];
  top_fusions?: ApiCreativeFusion[];
  unlocked_badges?: string[];
  custom_username_color?: string;
}

export interface UserConfig {
  difficulty: string;
  theme: string;
  visual_theme?: string;
  notifications_enabled: boolean;
  ai_personality: string;
}

export interface Friendship {
  id: number;
  to_user: number;
  username: string;
  level: number;
  created_at: string;
}

export interface SocialDashboardData {
  following: Friendship[];
  followers: Friendship[];
}

export interface PersonalizationFeatures {
  aura: boolean;
  font: boolean;
  accent: boolean;
}

export interface PersonalizationSettings {
  mode: 'auto' | 'manual';
  intensity_multiplier: number;
  manual_archetype?: string;
  features?: PersonalizationFeatures;
}

export interface CurrentArchetype {
  id: string;
  accent: string;
  aura_type: string;
  intensity: number;
  font_vibe: string;
}

export interface TrackerConnection {
  id: number;
  tracker: 'myanimelist' | 'anilist';
  username?: string;
  created_at: string;
}

export interface AIUsageData {
  tier: string;
  limits: {
    daily_tokens: number;
    daily_requests: number;
  };
  usage_today: {
    tokens: number;
    requests: number;
    estimated_cost_usd: number;
    tokens_percent: number;
    requests_percent: number;
  };
  history: {
    date: string;
    tokens: number;
    requests: number;
  }[];
}
