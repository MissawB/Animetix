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

export interface AppConfig {
  version: string;
  maintenance_mode: boolean;
  features: Record<string, boolean>;
}

export interface MediaItem {
  id: string;
  title: string;
  media_type: 'Anime' | 'Manga' | 'Movie' | 'Game' | 'Actor';
  image?: string;
  description?: string;
  popularity?: number;
}

import type { components } from './api';

type ApiAchievement = components["schemas"]["Achievement"];
type ApiCreativeFusion = components["schemas"]["CreativeFusion"];

export interface Profile {
  username: string;
  xp: number;
  level: number;
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

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
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

export interface CreativeFusion {
  id: number;
  title_a: string;
  title_b: string;
  media_type_a: string;
  media_type_b: string;
  image_url?: string;
  scenario_text?: string;
  likes_count: number;
  creator_name?: string;
  is_liked?: boolean;
}

export interface VideoSegment {
  id: string;
  video_id: string | number;
  start: number;
  end: number;
  start_time: number;
  summary: string;
  description?: string;
  media_title?: string;
  type?: 'emotion' | 'action' | 'dialogue';
}

export interface ApiResponse<T> {
  status: string;
  results: T;
  message?: string;
}

export interface CurationTicket {
  id: number;
  item_title: string;
  issue_description: string;
  source_pg: Record<string, unknown> | null;
  source_neo4j: Record<string, unknown> | null;
  is_resolved: boolean;
  created_at: string;
}

export interface DeducedRule {
  id: string;
  rule: string;
  source: string;
  confidence: number;
}

export interface NeuralSignal {
  id: number;
  input_context: string;
  feedback_type: string;
  weight: number;
  is_positive: boolean;
  is_ignored: boolean;
  created_at: string;
}

export interface NeuroMemoryData {
  total_signals: number;
  deduced_rules: DeducedRule[];
  signals: NeuralSignal[];
}

export interface TransparencyMetrics {
  total_feedbacks: number;
  knowledge_nodes: number;
  community_satisfaction: number;
  model_version: string;
  last_training?: string;
}

export interface ModelBenchmark {
  model_id: string;
  provider: string;
  elo_score: number;
  mmlu_score: number;
  context_window: number;
  is_open_source: boolean;
  license?: string;
  status?: string;
  huggingface_id?: string;
}

export interface TransparencyData {
  global_metrics: TransparencyMetrics;
  evolution_timeline: Array<{ date: string; accuracy: number }>;
  sota_benchmarks: ModelBenchmark[];
  embedding_drift: Record<string, { status: string; p_value: number; sample_size: number }>;
  ethics_score: number;
  model_uptime: number;
  ethics_audit?: {
    bias_score: number;
    safety_compliance: number;
    hallucination_rate: number;
  };
}

export interface GameState {
  gameOver: boolean;
  mediaType: string;
  isDaily: boolean;
}

export interface DuelLog {
  id: string;
  type: string;
  player: string;
  message: string;
  timestamp: number;
}

export interface DuelGameState extends GameState {
  roomCode: string;
  players: GamePlayer[];
  currentTurn: string;
  scores: Record<string, number>;
  target_item?: string;
}

export interface VNScene {
  background_url: string;
  character_name: string;
  character_sprite_url: string;
  dialogue: string;
  vibe?: string;
}

export interface AkinetixState extends GameState {
  currentQuestion: string | null;
  history: Array<{ q: string; a: string }>;
  aiGuess: string | null;
}

export interface EmojiState extends GameState {
  emojis: string;
  secret_title?: string;
  guesses: Array<{ title: string; title_en?: string; image: string; is_correct: boolean }>;
}

export interface BlindtestState extends GameState {
  video_url?: string;
  secret_title?: string;
  theme_type?: string;
  song?: string;
  artists?: string[];
  won?: boolean;
  difficulty?: string;
  maxAttempts?: number;
  attemptsLeft?: number;
  guesses: Array<{ title: string; is_correct: boolean }>;
}

export interface VisionState extends GameState {
  image_url: string;
  best_score: number;
  secret_title?: string;
  guesses: Array<{ text: string; score: number }>;
}

export interface ClassicGameState extends GameState {
  guesses: Array<{ title: string; is_correct: boolean }>;
  secret_title?: string;
}

export interface ParadoxState extends GameState {
  items: Array<{ id: number; title: string; image: string }>;
}

export interface DailyChallenge {
  date: string;
  media_type: string;
  modes: Array<DailyMode>;
}

export interface DailyMode {
  id: string;
  brush1: string;
  brush2: string;
  gradient: string;
  description: string;
  icon: string;
  completed: boolean;
}

export interface AudioLabState {
  audio_url?: string;
  status?: string;
}

export interface CompilerResult {
  message: string;
  test_output: string;
  c_code_generated: string;
}

export interface PlasticityResult {
  weights: number[][];
  message: string;
  stdp_log: string[];
}

export interface EvalResult {
  ai_score: number;
  community_score: number;
  is_worthy: boolean;
}

export interface UniverseData {
  name: string;
  genre: string;
  description: string;
  cosmology: string;
  factions: Array<{ name: string; description: string }>;
  characters: Array<{ name: string; role: string; power_level: number }>;
  episodes: Array<{ number: number; title: string; summary: string }>;
}

export interface SearchItem {
  id?: number | string;
  title?: string;
  name?: string;
  image_url?: string;
  type?: string;
}

export interface CovertestState extends GameState {
  cover_url: string;
  secret_title?: string;
  guesses: Array<{ title: string; is_correct: boolean }>;
}

export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, string | number | boolean | string[] | null | undefined>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  properties: Record<string, string | number | boolean | string[] | null | undefined>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// --- Club API Types ---
export interface Seiyuu {
  id: number;
  name: string;
  sample_url: string;
  image?: string;
  role?: string;
}

export interface VoiceProfile {
  id: number;
  name: string;
  language: 'japanese' | 'french' | 'other';
  origin: 'dataset' | 'youtube' | 'upload';
  definition?: string;
  roles?: string;
  impact?: string;
  origin_detail?: string;
  sample_url: string;
  created_at: string;
  updated_at: string;
}


export interface ClubEvent {
  id: number;
  club: number;
  title: string;
  description: string;
  event_date: string;
  created_at: string;
  is_participant?: boolean;
  participants_count?: number;
}

export interface DiscoveryClub {
  id: number;
  name: string;
  description: string;
  creator: number;
  creator_name: string;
  members_count: number;
  image_url?: string;
  is_private: boolean;
  theme?: string;
  events: ClubEvent[];
  created_at: string;
  updated_at: string;
  is_member?: boolean;
}

export interface ClubMembership {
  id: number;
  user: number;
  username: string;
  role: 'member' | 'admin' | 'owner';
  joined_at: string;
}

export interface GoldDatasetEntry {
  id: number;
  entry_type: string;
  context: string;
  instruction: string;
  response: string;
  metadata: Record<string, unknown>;
  is_validated: boolean;
  ai_validation_score: number;
  ai_critique: string | null;
  confidence_score: number;
  is_safe: boolean;
  created_at: string;
}

export interface GraphAudit {
  isolated_nodes: number;
  temporal_conflicts: number;
  orphan_entities: number;
  duplicate_entities: number;
  health_score: number;
  details: Array<{
    t1: string;
    y1: number;
    t2: string;
    y2: number;
  }>;
}

export interface BenchmarkData {
  benchmarks: ModelBenchmark[];
  top_model: ModelBenchmark;
  best_open_source: ModelBenchmark;
}

export interface VsBattleArenaEntry {
  id: number;
  char_a_name: string;
  char_a_franchise: string;
  char_b_name: string;
  char_b_franchise: string;
  winner: string;
  verdict_summary: string;
  likes_count: number;
  is_liked: boolean;
  created_at: string;
}

export interface GamePlayer {
  id: string;
  username: string;
  is_online: boolean;
  is_me?: boolean;
  is_ready?: boolean;
}

export interface ChatMessage {
  user: string;
  text: string;
  timestamp?: number;
}

export interface PlotlyEvent {
  points: Array<{
    customdata: unknown;
    pointNumber: number;
  }>;
}

// Types XAI générés depuis le schéma OpenAPI backend (évènement SSE `xai_report`).
export type DocumentAttribution = components["schemas"]["DocumentAttribution"];
export type LogitLensTrajectory = components["schemas"]["LogitLensTrajectory"];
export type ModelDiagnostics = components["schemas"]["ModelDiagnostics"];
export type Uncertainty = components["schemas"]["Uncertainty"];
export type AgentTraceStep = components["schemas"]["AgentTraceStep"];
export type XaiReport = components["schemas"]["XaiReport"];

export interface MediaDetail extends MediaItem {
  genres?: string[];
  title_english?: string;
  year?: string;
  studios?: string[];
  author?: string;
  micro_tags?: string[];
  related_items?: RelatedItem[];
  metadata?: Record<string, unknown>;
  title_native?: string;
  popularity?: number;
  seiyuu?: Seiyuu[];
}

export interface Appearance {
  id: string;
  title: string;
  image?: string;
}

export interface RelatedItem {
  id: string;
  title: string;
  image?: string;
}

export interface NotableWork {
  id: string;
  title: string;
  image?: string;
  type?: string;
  role?: string;
}

export interface SupportTicket {
  id: number;
  subject: string;
  query: string;
  ai_response?: string | null;
  status: 'open' | 'resolved' | 'closed';
  feedback_score?: number | null;
  created_at: string;
}

export interface AIFeedback {
  id: number;
  user: number;
  username: string;
  feedback_type: string;
  input_context: string;
  output_text: string;
  is_positive: boolean;
  created_at: string;
}

export interface OpenDataset {
  id: string;
  name: string;
  description: string;
  format: string;
  size_bytes: number;
  updated_at: string;
}

export interface FavoriteManga {
  id: number;
  manga: MediaDetail;
  status: 'reading' | 'completed' | 'plan_to_read';
  last_read_chapter: number;
  unread_chapters_count: number;
  created_at: string;
  updated_at: string;
}

