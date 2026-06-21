import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu,
  Server,
  Database,
  Activity,
  RefreshCw,
  WifiOff,
  Thermometer,
  HardDrive,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { apiClient } from '../../utils/apiClient';

// ─── Types ───────────────────────────────────────────────────────────
interface GpuInfo {
  id: number;
  name: string;
  temperature_c: number;
  utilization_pct: number;
  memory_used_gb: number;
  memory_total_gb: number;
  status: string;
}

interface ClusterNodeDetails {
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

interface ClusterNode {
  id: string;
  name: string;
  type: 'gpu' | 'inference' | 'graph_db' | 'worker';
  status: 'online' | 'offline' | 'unconfigured' | 'throttled' | 'degraded';
  latency_ms: number | null;
  details: ClusterNodeDetails;
  gpus?: GpuInfo[];
}

interface ClusterHealthData {
  timestamp: string;
  global_status: 'healthy' | 'degraded' | 'critical';
  online_count: number;
  total_count: number;
  health_percentage: number;
  nodes: ClusterNode[];
}

// ─── Helpers ─────────────────────────────────────────────────────────
const statusConfig = {
  online: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20', icon: CheckCircle2, label: 'ONLINE' },
  offline: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', glow: 'shadow-red-500/20', icon: XCircle, label: 'OFFLINE' },
  unconfigured: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', glow: 'shadow-yellow-500/20', icon: AlertTriangle, label: 'N/C' },
  throttled: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', glow: 'shadow-amber-500/20', icon: AlertTriangle, label: 'THROTTLED' },
  degraded: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', glow: 'shadow-yellow-500/20', icon: AlertTriangle, label: 'DEGRADED' },
};

const globalStatusConfig = {
  healthy: { color: 'text-emerald-400', bg: 'bg-emerald-500', label: 'HEALTHY', pulse: 'animate-pulse' },
  degraded: { color: 'text-amber-400', bg: 'bg-amber-500', label: 'DEGRADED', pulse: '' },
  critical: { color: 'text-red-400', bg: 'bg-red-500', label: 'CRITICAL', pulse: '' },
};

const nodeTypeIcon = {
  gpu: Cpu,
  inference: Zap,
  graph_db: Database,
  worker: Server,
};

const nodeTypeAccent = {
  gpu: 'text-green-400',
  inference: 'text-cyan-400',
  graph_db: 'text-purple-400',
  worker: 'text-pink-400',
};

// ─── GPU Mini Bar ────────────────────────────────────────────────────
const GpuMiniBar: React.FC<{ gpu: GpuInfo }> = ({ gpu }) => {
  const tempColor = gpu.temperature_c > 75 ? 'bg-red-500' : gpu.temperature_c > 55 ? 'bg-amber-500' : 'bg-emerald-500';
  const utilColor = gpu.utilization_pct > 85 ? 'bg-red-500' : gpu.utilization_pct > 50 ? 'bg-cyan-500' : 'bg-emerald-500';
  const memPct = (gpu.memory_used_gb / gpu.memory_total_gb) * 100;

  return (
    <div className="flex items-center gap-3 py-1.5 px-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors group">
      <span className="text-[9px] font-black uppercase opacity-30 w-16 shrink-0 tracking-wider">{gpu.name}</span>

      {/* Temperature */}
      <div className="flex items-center gap-1.5 w-20">
        <Thermometer className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className={`h-full ${tempColor} transition-all duration-700`} style={{ width: `${Math.min(gpu.temperature_c, 100)}%` }} />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-7 text-right">{gpu.temperature_c}°</span>
      </div>

      {/* Utilization */}
      <div className="flex items-center gap-1.5 w-20">
        <Activity className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className={`h-full ${utilColor} transition-all duration-700`} style={{ width: `${gpu.utilization_pct}%` }} />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-7 text-right">{gpu.utilization_pct}%</span>
      </div>

      {/* Memory */}
      <div className="flex items-center gap-1.5 w-24">
        <HardDrive className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className="h-full bg-violet-500 transition-all duration-700" style={{ width: `${memPct}%` }} />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-14 text-right">{gpu.memory_used_gb}/{gpu.memory_total_gb}G</span>
      </div>
    </div>
  );
};

// ─── Status Indicator Dot ────────────────────────────────────────────
const StatusDot: React.FC<{ status: string; size?: 'sm' | 'md' }> = ({ status, size = 'sm' }) => {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.offline;
  const sizeClass = size === 'md' ? 'w-3 h-3' : 'w-2 h-2';
  return (
    <span className="relative flex items-center">
      <span className={`${sizeClass} rounded-full ${config.bg} ${config.border} border`} />
      {status === 'online' && (
        <span className={`absolute ${sizeClass} rounded-full bg-emerald-400 animate-ping opacity-30`} />
      )}
    </span>
  );
};

// ─── Node Card ───────────────────────────────────────────────────────
const NodeCard: React.FC<{ node: ClusterNode }> = ({ node }) => {
  const config = statusConfig[node.status as keyof typeof statusConfig] || statusConfig.offline;
  const IconComponent = nodeTypeIcon[node.type] || Server;
  const accentColor = nodeTypeAccent[node.type] || 'text-white';

  return (
    <Card padding="lg" className={`bg-black/40 border-white/5 hover:${config.border} transition-all duration-500 group relative overflow-hidden`}>
      {/* Ambient glow */}
      <div className={`absolute -top-20 -right-20 w-40 h-40 rounded-full ${config.bg} blur-3xl opacity-30 group-hover:opacity-50 transition-opacity`} />

      {/* Header */}
      <div className="flex justify-between items-start mb-6 relative z-10">
        <div className={`p-3 rounded-xl ${config.bg} ${config.border} border`}>
          <IconComponent className={`w-6 h-6 ${accentColor}`} />
        </div>
        <div className="flex items-center gap-2">
          <StatusDot status={node.status} size="md" />
          <Badge variant="neutral" className={`text-[9px] uppercase font-black ${config.color}`}>
            {config.label}
          </Badge>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-lg font-black italic manga-font uppercase mb-1 relative z-10">
        {node.name}
      </h3>
      <p className="text-[10px] font-bold uppercase opacity-30 tracking-wider mb-6 relative z-10">
        {node.type === 'gpu' ? 'Compute Cluster' : node.type === 'inference' ? 'LLM Engine' : 'Knowledge Base'}
      </p>

      {/* Latency */}
      {node.latency_ms !== null && (
        <div className="flex items-center gap-2 mb-4 relative z-10">
          <Clock className="w-3 h-3 opacity-30" />
          <span className="text-[10px] font-bold uppercase opacity-40">Latence</span>
          <span className={`text-sm font-black ml-auto ${
            node.latency_ms < 50 ? 'text-emerald-400' : node.latency_ms < 200 ? 'text-amber-400' : 'text-red-400'
          }`}>
            {node.latency_ms}ms
          </span>
        </div>
      )}

      {/* Type-specific details */}
      {node.type === 'gpu' && node.details && (
        <div className="space-y-2 relative z-10">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">GPUs</p>
              <p className="text-2xl font-black italic manga-font text-green-400">{node.details.gpu_count}</p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">VRAM Total</p>
              <p className="text-2xl font-black italic manga-font">{node.details.total_vram_gb}<span className="text-xs opacity-40">GB</span></p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Temp Moy.</p>
              <p className={`text-lg font-black ${
                (node.details.avg_temperature_c ?? 0) > 75 ? 'text-red-400' : (node.details.avg_temperature_c ?? 0) > 55 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {node.details.avg_temperature_c}°C
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Util. Moy.</p>
              <p className="text-lg font-black text-cyan-400">{node.details.avg_utilization_pct}%</p>
            </div>
          </div>
          <div className="pt-3 border-t border-white/5 flex justify-between">
            <span className="text-[9px] font-bold opacity-25 uppercase">CUDA {node.details.cuda_version}</span>
            <span className="text-[9px] font-bold opacity-25 uppercase">Driver {node.details.driver_version}</span>
          </div>
        </div>
      )}

      {node.type === 'inference' && node.details && (
        <div className="space-y-3 relative z-10">
          <div>
            <p className="text-[9px] font-black uppercase opacity-25 mb-1">Engine</p>
            <p className="text-sm font-black text-cyan-400">{node.details.engine}</p>
          </div>
          {node.details.loaded_models && node.details.loaded_models.length > 0 && (
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-2">Modèles Chargés ({node.details.model_count})</p>
              <div className="flex flex-wrap gap-1">
                {node.details.loaded_models.slice(0, 6).map((m: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-bold text-cyan-400 uppercase">
                    {m}
                  </span>
                ))}
                {node.details.loaded_models.length > 6 && (
                  <span className="px-2 py-0.5 text-[9px] font-bold opacity-30">+{node.details.loaded_models.length - 6}</span>
                )}
              </div>
            </div>
          )}
          {node.details.error && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
              <span className="text-[9px] font-bold text-red-400 uppercase break-all">{node.details.error}</span>
            </div>
          )}
        </div>
      )}

      {node.type === 'graph_db' && node.details && (
        <div className="space-y-3 relative z-10">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Nœuds</p>
              <p className="text-2xl font-black italic manga-font text-purple-400">
                {(node.details.node_count || 0).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Relations</p>
              <p className="text-2xl font-black italic manga-font text-purple-300">
                {(node.details.relationship_count || 0).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="pt-3 border-t border-white/5">
            <span className="text-[9px] font-bold opacity-25 uppercase">
              {node.details.database} • {node.details.bolt_uri}
            </span>
          </div>
          {node.details.error && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
              <span className="text-[9px] font-bold text-red-400 uppercase break-all">{node.details.error}</span>
            </div>
          )}
        </div>
      )}

      {node.type === 'worker' && node.details && (
        <div className="space-y-3 relative z-10">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">File d'attente</p>
              <p className="text-2xl font-black italic manga-font text-pink-400">
                {node.details.queue_length || 0}
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Statut Worker</p>
              <p className={`text-sm font-black uppercase ${
                node.details.worker_status === 'active' ? 'text-pink-300' : 'text-emerald-400'
              }`}>
                {node.details.worker_status || 'idle'}
              </p>
            </div>
          </div>
          {node.details.active_task && (
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">Tâche Active</p>
              <p className="text-[10px] font-bold opacity-85 break-all line-clamp-2 bg-white/[0.02] p-1.5 rounded border border-white/5">
                {node.details.active_task}
              </p>
            </div>
          )}
          <div className="pt-3 border-t border-white/5 flex justify-between items-center">
            <span className="text-[9px] font-bold opacity-25 uppercase">Repli API</span>
            <Badge variant="neutral" className={`text-[9px] font-black uppercase px-2 py-0.5 rounded ${
              node.details.fallback_mode === 'active' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
            }`}>
              {node.details.fallback_mode === 'active' ? 'ACTIF (Budget Dépassé)' : 'NOMINAL'}
            </Badge>
          </div>
        </div>
      )}
    </Card>
  );
};

// ─── Main Component ──────────────────────────────────────────────────
const ClusterHealthPanel: React.FC = () => {
  const [data, setData] = useState<ClusterHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchHealth = useCallback(async () => {
    try {
      const result = await apiClient('/api/monitoring/cluster-health/', { skipToast: true });
      setData(result);
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      const e = err as Error;
      setError(e.message || 'Failed to fetch cluster health');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const refresh = useCallback(() => {
    setIsRefreshing(true);
    void fetchHealth();
  }, [fetchHealth]);

  useEffect(() => {
    // Kick off the initial fetch in a microtask so the effect body does not
    // synchronously reach setState (avoids cascading renders). The interval
    // then drives subsequent auto-refreshes (every 15s).
    queueMicrotask(() => {
      void fetchHealth();
    });
    const interval = setInterval(() => {
      void fetchHealth();
    }, 15000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-4 h-4 rounded-full bg-white/10 animate-pulse" />
          <div className="h-8 w-64 bg-white/5 rounded-lg animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-72 bg-white/[0.02] rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <Card padding="lg" className="bg-red-500/5 border-red-500/20">
        <div className="flex items-center gap-4">
          <WifiOff className="w-8 h-8 text-red-400" />
          <div>
            <h3 className="text-lg font-black italic manga-font uppercase text-red-400">Cluster Unreachable</h3>
            <p className="text-[10px] font-bold uppercase opacity-40 mt-1">{error}</p>
          </div>
          <button
            onClick={refresh}
            className="ml-auto p-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition-all"
          >
            <RefreshCw className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </Card>
    );
  }

  const gStatus = data ? globalStatusConfig[data.global_status] : globalStatusConfig.critical;
  const gpuNode = data?.nodes.find(n => n.type === 'gpu');

  return (
    <div className="space-y-8" id="cluster-health-panel">
      {/* ── Global Status Bar ───────────────────────────────────── */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className={`w-4 h-4 rounded-full ${gStatus.bg} ${gStatus.pulse}`} />
            {data?.global_status === 'healthy' && (
              <div className="absolute inset-0 w-4 h-4 rounded-full bg-emerald-400 animate-ping opacity-20" />
            )}
          </div>
          <div>
            <h2 className="text-3xl font-black italic manga-font uppercase tracking-tight">
              Cluster <span className={gStatus.color}>Status</span>
            </h2>
            <p className="text-[10px] font-bold uppercase opacity-30 tracking-widest mt-0.5">
              {data?.online_count}/{data?.total_count} systèmes opérationnels • {data?.health_percentage}% disponibilité
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[9px] font-bold uppercase opacity-20 tracking-wider">
              MAJ {lastRefresh.toLocaleTimeString('fr-FR')}
            </span>
          )}
          <button
            onClick={refresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-[10px] font-black uppercase tracking-widest disabled:opacity-30"
          >
            {isRefreshing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5" />
            )}
            Refresh
          </button>
        </div>
      </div>

      {/* ── Node Cards Grid ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {data?.nodes.map(node => (
          <NodeCard key={node.id} node={node} />
        ))}
      </div>

      {/* ── GPU Detail Grid (if GPU node exists) ────────────────── */}
      {gpuNode?.gpus && gpuNode.gpus.length > 0 && (
        <Card padding="lg" className="bg-black/40 border-white/5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
              <Cpu className="w-4 h-4 text-green-400" /> GPU Instance Detail
            </h3>
            <div className="flex items-center gap-4 text-[9px] font-bold uppercase opacity-25 tracking-wider">
              <span className="flex items-center gap-1"><Thermometer className="w-3 h-3" /> Temp</span>
              <span className="flex items-center gap-1"><Activity className="w-3 h-3" /> Util</span>
              <span className="flex items-center gap-1"><HardDrive className="w-3 h-3" /> VRAM</span>
            </div>
          </div>
          <div className="space-y-0.5">
            {gpuNode.gpus.map(gpu => (
              <GpuMiniBar key={gpu.id} gpu={gpu} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ClusterHealthPanel;
