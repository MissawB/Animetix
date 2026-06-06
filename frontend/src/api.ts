import { 
  AkinetixState, AppConfig, ClassicGameState, DailyChallenge, MediaItem, Profile, User, GraphData,
  DiscoveryClub, ClubMembership 
} from './types';
import { apiClient } from './utils/apiClient';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// --- Config API ---
export async function getAppConfig(): Promise<AppConfig> {
  return apiClient('/api/v1/config/');
}

// --- Search API ---
export async function searchMedia(query: string, mediaType = 'anime'): Promise<MediaItem[]> {
  return apiClient(`/api/v1/search/?q=${encodeURIComponent(query)}&media_type=${mediaType}`);
}

// --- Classic Game API ---
export async function startClassicGame(mediaType = 'anime', difficulty = 'normal'): Promise<ClassicGameState> {
  return apiClient('/api/v1/game/classic/start/', {
    method: 'POST',
    body: JSON.stringify({ media_type: mediaType, difficulty }),
  });
}

export async function getClassicGameState(): Promise<ClassicGameState> {
  return apiClient('/api/v1/game/classic/state/');
}

// --- Akinetix Game API ---
export async function startAkinetixGame(mediaType = 'Anime'): Promise<AkinetixState> {
  return apiClient('/api/v1/game/akinetix/start/', {
    method: 'POST',
    body: JSON.stringify({ media_type: mediaType }),
  });
}

export async function getAkinetixGameState(): Promise<AkinetixState> {
  return apiClient('/api/v1/game/akinetix/state/');
}

export async function answerAkinetixGame(answer: string): Promise<AkinetixState> {
  return apiClient('/api/v1/game/akinetix/answer/', {
    method: 'POST',
    body: JSON.stringify({ answer }),
  });
}

// --- Social API ---
export async function getLeaderboard(): Promise<Profile[]> {
  return apiClient('/api/v1/leaderboard/');
}

export async function getSocialDashboard(): Promise<SocialDashboardData> {
  return apiClient('/api/v1/social/dashboard/');
}

export async function searchUsers(query: string): Promise<(User & { is_following: boolean })[]> {
  return apiClient(`/api/v1/social/search/?q=${encodeURIComponent(query)}`);
}

export async function toggleFollow(userId: number): Promise<{ status: string }> {
  return apiClient(`/api/v1/social/toggle_follow/${userId}/`, {
    method: 'POST',
  });
}

export async function getProfile(username: string): Promise<Profile> {
  return apiClient(`/api/v1/profile/${username}/`);
}

export async function updateAccountSettings(data: { tier?: string }): Promise<{ status: string; tier: string }> {
  return apiClient('/api/v1/profiles/update_settings/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function generateApiKey(): Promise<{ api_key: string; message: string }> {
  return apiClient('/api/v1/profiles/generate_api_key/', {
    method: 'POST',
  });
}

export async function revokeApiKey(): Promise<{ status: string }> {
  return apiClient('/api/v1/profiles/revoke_api_key/', {
    method: 'POST',
  });
}

export async function getAIFeedbackHistory(): Promise<AIFeedback[]> {
  return apiClient('/api/v1/mlops/feedback/submit/');
}

// --- Daily Challenge ---
export async function getDailyChallenge(): Promise<DailyChallenge> {
  return apiClient('/api/v1/daily-challenge/');
}

// --- ARCHETYPIST (LA FORGE) ---

export interface FusionRequest {
  title_A?: string;
  title_B?: string;
  media_type_A?: string;
  media_type_B?: string;
  chaos_level?: number;
  universe_balance?: number;
  art_style?: string;
  parent_id?: number;
}

export interface FusionResponse {
  fusion_id: number;
  task_id: string;
  title_a: string;
  title_b: string;
  item_a_image?: string;
  item_b_image?: string;
}

export interface FusionStatus {
  state: string;
  status: string;
  completed?: boolean;
  scenario?: string;
  image_url?: string;
}

export async function startFusion(params: FusionRequest): Promise<FusionResponse> {
  return apiClient('/api/v1/archetypist/start/', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getFusionStatus(taskId: string, fusionId: number): Promise<FusionStatus> {
  return apiClient(`/api/v1/archetypist/status/?task_id=${taskId}&fusion_id=${fusionId}`);
}

export async function getAuthUser(): Promise<User> {
  const profile = await apiClient('/api/v1/auth/me/', { skipToast: true });
  return {
    id: profile.user.id,
    username: profile.user.username,
    email: profile.user.email,
    is_authenticated: true,
    xp: profile.xp,
    tier: profile.tier,
    has_api_key: profile.has_api_key,
  };
}

export async function loginUser(data: Record<string, any>): Promise<User> {
  await apiClient('/api/v1/auth/login/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return getAuthUser();
}

export async function registerUser(data: Record<string, any>): Promise<User> {
  await apiClient('/api/v1/auth/register/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return getAuthUser();
}

export async function logoutUser(): Promise<void> {
  return apiClient('/api/v1/auth/logout/', {
    method: 'POST',
  });
}

// --- Graph API ---
export async function getGraphNeighborhood(id: string, type: string, depth: number = 1): Promise<GraphData> {
  return apiClient(`/api/v1/graph/neighbors/?id=${id}&type=${type}&depth=${depth}`);
}

// --- Companion API ---
export interface CompanionResponse {
  response: string;
  history: { role: string; content: string }[];
}

// --- VS Battle API ---
export interface VsBattleRequest {
  char_a: string;
  char_b: string;
  char_a_franchise?: string;
  char_b_franchise?: string;
}

export interface VsBattleResult {
  character_a: any;
  character_b: any;
  winner: string;
  verdict_summary: string;
  debate_history: any[];
}

export async function runVsBattle(params: VsBattleRequest): Promise<VsBattleResult> {
  return apiClient('/api/v1/game/vs_battle/run/', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function interactWithCompanion(mentorId: string, message: string, contextUrl: string = ''): Promise<CompanionResponse> {
  return apiClient('/api/v1/companion/interact/', {
    method: 'POST',
    body: JSON.stringify({
      mentor_id: mentorId,
      user_message: message,
      context_url: contextUrl,
    }),
  });
}

// --- Club API ---
export async function getClubs(): Promise<DiscoveryClub[]> {
  const data = await apiClient('/api/v1/clubs/');
  return Array.isArray(data) ? data : data.results || [];
}

export async function getClubDetails(id: number): Promise<DiscoveryClub> {
  return apiClient(`/api/v1/clubs/${id}/`);
}

export async function createClub(data: Partial<DiscoveryClub>): Promise<DiscoveryClub> {
  return apiClient('/api/v1/clubs/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function joinClub(id: number): Promise<{ status: string }> {
  return apiClient(`/api/v1/clubs/${id}/join/`, {
    method: 'POST',
  });
}

export async function leaveClub(id: number): Promise<{ status: string }> {
  return apiClient(`/api/v1/clubs/${id}/leave/`, {
    method: 'POST',
  });
}

export interface ClubEvent {
  id: number;
  club: number;
  title: string;
  description: string;
  event_date: string;
  created_at: string;
}

export async function getClubEvents(clubId: number): Promise<ClubEvent[]> {
  const data = await apiClient(`/api/v1/club-events/?club=${clubId}`);
  return Array.isArray(data) ? data : data.results || [];
}

export async function getClubEventDetails(eventId: number): Promise<ClubEvent> {
  return apiClient(`/api/v1/club-events/${eventId}/`);
}

export async function toggleEventParticipation(eventId: number): Promise<{ status: string; participants_count: number }> {
  return apiClient(`/api/v1/club-events/${eventId}/join/`, {
    method: 'POST',
  });
}

export async function createClubEvent(data: Partial<ClubEvent>): Promise<ClubEvent> {
  return apiClient('/api/v1/club-events/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}



