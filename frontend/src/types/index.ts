export interface User {
  id: number;
  username: string;
  email: string;
  is_authenticated: boolean;
  avatar?: string;
  xp?: number;
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
  total_donations: number;
  api_costs: number;
  server_costs: number;
  balance: number;
  recent_donations: Array<{ user: string; amount: number; date: string }>;
  ethics_score: number;
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

