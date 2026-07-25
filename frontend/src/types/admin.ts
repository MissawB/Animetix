import type { components } from './api';

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

export interface OpenDataset {
  id: string;
  name: string;
  description: string;
  format: string;
  size_bytes: number;
  updated_at: string;
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
