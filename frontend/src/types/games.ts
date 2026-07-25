import type { components } from './api';

export interface GameState {
  gameOver: boolean;
  mediaType: string;
  isDaily: boolean;
}

export interface GamePlayer {
  id: string;
  username: string;
  is_online: boolean;
  is_me?: boolean;
  is_ready?: boolean;
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

export interface DailyChallenge {
  date: string;
  media_type?: string;
  is_today?: boolean;
  prev_date?: string | null;
  next_date?: string | null;
  total_score?: number;
  modes: Array<DailyMode>;
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
