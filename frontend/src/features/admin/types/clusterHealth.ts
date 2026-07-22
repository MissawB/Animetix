import { Cpu, Server, Database, Zap, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

export interface GpuInfo {
  id: number;
  name: string;
  temperature_c: number;
  utilization_pct: number;
  memory_used_gb: number;
  memory_total_gb: number;
  status: string;
}

export interface ClusterNodeDetails {
  // GPU node
  gpu_count?: number;
  total_vram_gb?: number;
  avg_temperature_c?: number;
  avg_utilization_pct?: number;
  cuda_version?: string;
  driver_version?: string;
  // Inference node
  engine?: string;
  loaded_models?: string[];
  model_count?: number;
  // Graph DB node
  node_count?: number;
  relationship_count?: number;
  database?: string;
  bolt_uri?: string;
  // Worker node
  queue_length?: number;
  worker_status?: string;
  active_task?: string;
  fallback_mode?: string;
  // Shared
  error?: string;
}

export interface ClusterNode {
  id: string;
  name: string;
  type: 'gpu' | 'inference' | 'graph_db' | 'worker';
  status: 'online' | 'offline' | 'unconfigured' | 'throttled' | 'degraded';
  latency_ms: number | null;
  details: ClusterNodeDetails;
  gpus?: GpuInfo[];
}

export interface ClusterHealthData {
  timestamp: string;
  global_status: 'healthy' | 'degraded' | 'critical';
  online_count: number;
  total_count: number;
  health_percentage: number;
  nodes: ClusterNode[];
}

export const statusConfig = {
  online: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    glow: 'shadow-emerald-500/20',
    icon: CheckCircle2,
    label: 'ONLINE',
  },
  offline: {
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    glow: 'shadow-red-500/20',
    icon: XCircle,
    label: 'OFFLINE',
  },
  unconfigured: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    glow: 'shadow-yellow-500/20',
    icon: AlertTriangle,
    label: 'N/C',
  },
  throttled: {
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    glow: 'shadow-amber-500/20',
    icon: AlertTriangle,
    label: 'THROTTLED',
  },
  degraded: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    glow: 'shadow-yellow-500/20',
    icon: AlertTriangle,
    label: 'DEGRADED',
  },
};

export const globalStatusConfig = {
  healthy: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-500',
    label: 'HEALTHY',
    pulse: 'animate-pulse',
  },
  degraded: { color: 'text-amber-400', bg: 'bg-amber-500', label: 'DEGRADED', pulse: '' },
  critical: { color: 'text-red-400', bg: 'bg-red-500', label: 'CRITICAL', pulse: '' },
};

export const nodeTypeIcon = {
  gpu: Cpu,
  inference: Zap,
  graph_db: Database,
  worker: Server,
};

export const nodeTypeAccent = {
  gpu: 'text-green-400',
  inference: 'text-cyan-400',
  graph_db: 'text-purple-400',
  worker: 'text-pink-400',
};
