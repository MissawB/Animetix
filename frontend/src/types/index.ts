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

export interface Profile {
  username: string;
  xp: number;
  level: number;
  rank?: string;
  achievements_count?: number;
  collection_count?: number;
  recent_achievements?: any[];
  top_fusions?: any[];
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
}

export interface TransparencyData {
  total_costs: number;
  monthly_costs: number;
  api_costs: number;
  server_costs: number;
  ethics_score: number;
  rag_fidelity: number;
  average_latency: number;
  model_uptime: number;
}

export interface GameState {
  gameOver: boolean;
  mediaType: string;
  isDaily: boolean;
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
