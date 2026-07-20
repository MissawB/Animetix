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
  maintenance_message?: string | null;
  maintenance_until?: string | null;
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

type ApiAchievement = components['schemas']['Achievement'];
type ApiCreativeFusion = components['schemas']['CreativeFusion'];

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

export type CreativeFusion = Omit<
  components['schemas']['CreativeFusion'],
  'image_url' | 'creator_name' | 'is_liked' | 'created_at'
> & {
  image_url?: string;
  creator_name?: string;
  is_liked?: boolean;
  created_at?: string;
};

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

export type CurationTicket = Omit<
  components['schemas']['DataCurationTicket'],
  'source_pg' | 'source_neo4j' | 'is_resolved'
> & {
  source_pg: Record<string, unknown> | null;
  source_neo4j: Record<string, unknown> | null;
  is_resolved: boolean;
};

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
  embedding_drift: Record<string, { status: string; p_value?: number; sample_size?: number }>;
  ethics_score: number | null;
  model_uptime: number | null;
  ethics_audit?: {
    safety_compliance: number | null;
    hallucination_rate: number | null;
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
  /** Progression 0..1 : à quel point l'IA est proche de deviner. */
  confidence: number;
}

export interface EmojiState {
  media_type: string;
  difficulty?: string;
  emojis: string[]; // révélés jusqu'ici (vague → évident), un de plus par essai raté
  total_emojis: number; // longueur totale de la séquence
  game_over: boolean;
  is_daily?: boolean;
  is_ranked?: boolean;
  secret_title?: string;
  guesses: Array<{ title: string; title_en?: string; image: string; is_correct: boolean }>;
}

export interface BlindtestState extends GameState {
  video_url?: string;
  secret_title?: string;
  secret_image?: string | null;
  theme_type?: string;
  sequence?: number | string;
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

export type ClassicHintKey =
  | 'year'
  | 'origin'
  | 'tags'
  | 'genres'
  | 'studio'
  | 'letter'
  | 'words'
  | 'desc';

export interface ClassicHint {
  label: string;
  unlocks_at: number;
  can_reveal: boolean;
  revealed: boolean;
  value: string | null;
}

export type ClassicHints = Partial<Record<ClassicHintKey, ClassicHint>>;

export interface ClassicReason {
  kind: 'public' | 'tags' | 'structure';
  label: string;
  detail: string[];
}

export interface ClassicGuess {
  title: string;
  title_english?: string | null;
  title_native?: string | null;
  image?: string | null;
  score?: number;
  color?: 'danger' | 'warning' | 'primary' | 'secondary' | string;
  is_correct: boolean;
  reasons?: ClassicReason[];
}

export interface ClassicGameState extends GameState {
  difficulty?: string;
  guess_count?: number;
  guesses: ClassicGuess[];
  hints?: ClassicHints;
  secret_title?: string;
  secret_data?: Record<string, unknown> | null;
}

export interface ParadoxState extends GameState {
  items: Array<{ id: number; title: string; image: string }>;
}

export interface DailyChallenge {
  date: string;
  media_type?: string;
  is_today?: boolean;
  prev_date?: string | null;
  next_date?: string | null;
  total_score?: number;
  modes: Array<DailyMode>;
}

export interface DailyMode {
  id: string;
  brush1: string;
  brush2: string;
  gradient: string;
  description: string;
  icon: string;
  media_type?: string;
  url?: string;
  completed: boolean;
  score?: number | null;
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
  locale?: string;
  volume?: string | number;
  author?: string;
  // Backend sends snake_case game_over (GameState.gameOver is unused for covertest).
  game_over?: boolean;
  guesses: Array<{ title: string; image?: string | null; is_correct: boolean }>;
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

export type ClubEvent = Omit<
  components['schemas']['ClubEvent'],
  'is_participant' | 'participants_count' | 'event_date'
> & {
  event_date: string;
  is_participant?: boolean;
  participants_count?: number;
};

export type DiscoveryClub = Omit<
  components['schemas']['DiscoveryClub'],
  'image_url' | 'is_private' | 'events'
> & {
  image_url?: string;
  is_private: boolean;
  events: ClubEvent[];
  is_member?: boolean;
};

export interface ClubMembership {
  id: number;
  user: number;
  username: string;
  role: 'member' | 'admin' | 'owner';
  joined_at: string;
}

export type GoldDatasetEntry = Omit<
  components['schemas']['GoldDatasetEntry'],
  | 'entry_type'
  | 'metadata'
  | 'is_validated'
  | 'ai_validation_score'
  | 'confidence_score'
  | 'is_safe'
> & {
  entry_type: string;
  metadata: Record<string, unknown>;
  is_validated: boolean;
  ai_validation_score: number;
  confidence_score: number;
  is_safe: boolean;
};

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

export interface ArenaCharacter {
  name: string;
  franchise: string;
  image: string;
  source?: 'wiki' | 'synthetic';
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
export type DocumentAttribution = components['schemas']['DocumentAttribution'];
export type LogitLensTrajectory = components['schemas']['LogitLensTrajectory'];
export type ModelDiagnostics = components['schemas']['ModelDiagnostics'];
export type Uncertainty = components['schemas']['Uncertainty'];
export type AgentTraceStep = components['schemas']['AgentTraceStep'];
export type XaiReport = components['schemas']['XaiReport'];

export interface StreamingPlatform {
  platform: string;
  has_vf?: boolean;
  has_vostfr?: boolean;
  status?: string;
}

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
  streaming_platforms?: StreamingPlatform[];
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

export interface PlasticityConfig {
  tau_plus: number;
  tau_minus: number;
  num_concepts: number;
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

export interface UnifiedPlasticityState {
  status: string;
  weights: number[][];
  concepts: string[];
  plasticity_config: PlasticityConfig;
  personalization_settings: PersonalizationSettings;
  current_archetype: CurrentArchetype;
}

export interface UPlayer {
  id: string;
  name: string;
  is_host?: boolean;
  has_voted?: boolean;
  alive?: boolean;
  role?: string;
  word?: string;
  image?: string;
}

export interface UMsg {
  user: string;
  text: string;
  is_system?: boolean;
}

export interface UResult {
  winner: string;
  reason?: string;
  mrwhite_winners?: string[];
}

export type CombatCharacter = components['schemas']['CombatCharacter'];
export type DebateTurn = components['schemas']['DebateTurn'];
export type VsBattleResult = components['schemas']['VsBattleResult'];

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
