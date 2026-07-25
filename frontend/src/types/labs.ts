import type { components } from './api';
import type { PersonalizationSettings, CurrentArchetype } from './user';

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

export interface PlasticityConfig {
  tau_plus: number;
  tau_minus: number;
  num_concepts: number;
}

export interface UnifiedPlasticityState {
  status: string;
  weights: number[][];
  concepts: string[];
  plasticity_config: PlasticityConfig;
  personalization_settings: PersonalizationSettings;
  current_archetype: CurrentArchetype;
}

// Types XAI générés depuis le schéma OpenAPI backend (évènement SSE `xai_report`).
export type DocumentAttribution = components['schemas']['DocumentAttribution'];
export type LogitLensTrajectory = components['schemas']['LogitLensTrajectory'];
export type ModelDiagnostics = components['schemas']['ModelDiagnostics'];
export type Uncertainty = components['schemas']['Uncertainty'];
export type AgentTraceStep = components['schemas']['AgentTraceStep'];
export type XaiReport = components['schemas']['XaiReport'];
