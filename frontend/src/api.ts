import { 
  User, 
  AppConfig, 
  MediaItem, 
  Profile, 
  SocialDashboardData,
  AkinetixState,
  DailyChallenge,
  GraphData,
  ClubEvent,
  DiscoveryClub,
  AIFeedback,
  ClassicGameState,
  VideoSegment,
  OpenDataset
} from './types';
import { apiClient } from './utils/apiClient';
import { auth } from './utils/firebase';
import type { components } from './types/api';

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

export async function updateAccountSettings(data: { tier?: string; custom_username_color?: string }): Promise<{ status: string; tier: string; custom_username_color?: string }> {
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

export async function getAIUsage(): Promise<AIUsageData> {
  return apiClient('/api/v1/profiles/usage/');
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
    unlocked_badges: profile.unlocked_badges,
    custom_username_color: profile.custom_username_color,
  };
}

export async function loginUser(data: Record<string, unknown>): Promise<User> {
  await apiClient('/api/v1/auth/login/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return getAuthUser();
}

export async function registerUser(data: Record<string, unknown>): Promise<User> {
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

// --- VS Battle API ---
export interface VsBattleRequest {
  char_a: string;
  char_b: string;
  char_a_franchise?: string;
  char_b_franchise?: string;
}

export interface VsBattleResult {
  character_a: components["schemas"]["CombatCharacter"];
  character_b: components["schemas"]["CombatCharacter"];
  winner: string;
  verdict_summary: string;
  debate_history: components["schemas"]["DebateTurn"][];
}

export async function runVsBattle(params: VsBattleRequest): Promise<VsBattleResult> {
  return apiClient('/api/v1/game/vs_battle/run/', {
    method: 'POST',
    body: JSON.stringify(params),
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

// --- Labs API ---
export async function cloneVoice(text: string, audioFile: File, pitch: number): Promise<{ audio_data: string }> {
  const formData = new FormData();
  formData.append('target_text', text);
  formData.append('reference_audio', audioFile);
  formData.append('pitch', pitch.toString());

  return apiClient('/api/v1/labs/voice-cloning/', {
    method: 'POST',
    body: formData,
    isFormData: true,
  });
}

export async function searchVideoSegments(query: string): Promise<{ status: string; results: VideoSegment[] }> {
  return apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(query)}`);
}

export async function getOpenDatasets(): Promise<{ status: string; datasets: OpenDataset[] }> {
  return apiClient('/api/v1/mlops/open-data/');
}

export async function downloadDataset(datasetId: string, filename: string): Promise<void> {
  const url = `/api/v1/mlops/open-data/download/${datasetId}/`;
  const defaultHeaders: Record<string, string> = {
    'X-Requested-With': 'XMLHttpRequest',
  };

  const firebaseUser = auth.currentUser;
  if (firebaseUser) {
    try {
      const token = await firebaseUser.getIdToken();
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    } catch (err) {
      console.error('Failed to get Firebase ID Token', err);
    }
  }

  const response = await fetch(url, { headers: defaultHeaders });
  if (!response.ok) {
    throw new Error(`Failed to download dataset: ${response.statusText}`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
}
