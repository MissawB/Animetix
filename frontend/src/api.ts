import { AkinetixState, AppConfig, ClassicGameState, DailyChallenge, MediaItem, Profile, User, GraphData } from './types';
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

export async function getProfile(username: string): Promise<Profile> {
  return apiClient(`/api/v1/profile/${username}/`);
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
  return apiClient('/api/v1/auth/me/');
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


