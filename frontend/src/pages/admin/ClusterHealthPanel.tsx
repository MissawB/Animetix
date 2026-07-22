import React from 'react';
import { Cpu, RefreshCw, WifiOff, Thermometer, Activity, HardDrive, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { useClusterHealth } from '../../features/admin/hooks/useHealth';
import { ClusterHealthData, globalStatusConfig } from '../../features/admin/types/clusterHealth';
import { NodeCard } from './components/NodeCard';
import { GpuMiniBar } from './components/GpuMiniBar';

const ClusterHealthPanel: React.FC = () => {
  const { t } = useTranslation();
  const query = useClusterHealth();
  const data = (query.data as ClusterHealthData | undefined) ?? null;
  const loading = query.isPending;
  const error = query.error ? (query.error as Error).message : null;
  const lastRefresh = query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : null;
  const isRefreshing = query.isFetching;
  const refresh = () => void query.refetch();

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-4 h-4 rounded-full bg-white/10 animate-pulse" />
          <div className="h-8 w-64 bg-white/5 rounded-lg animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
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
            <h3 className="text-lg font-black italic manga-font uppercase text-red-400">
              Cluster Unreachable
            </h3>
            <p className="text-[10px] font-bold uppercase opacity-40 mt-1">{error}</p>
          </div>
          <button
            onClick={refresh}
            aria-label={t('admin.cluster.refresh', 'Rafraîchir')}
            className="ml-auto p-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition-all"
          >
            <RefreshCw className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </Card>
    );
  }

  const gStatus = data ? globalStatusConfig[data.global_status] : globalStatusConfig.critical;
  const gpuNode = data?.nodes.find((n) => n.type === 'gpu');

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
              {t(
                'admin.cluster.status_summary',
                '{{online}}/{{total}} systèmes opérationnels • {{percentage}}% disponibilité',
                {
                  online: data?.online_count,
                  total: data?.total_count,
                  percentage: data?.health_percentage,
                },
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[9px] font-bold uppercase opacity-20 tracking-wider">
              {t('admin.cluster.updated_at', 'MAJ')} {lastRefresh.toLocaleTimeString('fr-FR')}
            </span>
          )}
          <button
            onClick={refresh}
            disabled={isRefreshing}
            aria-label={t('admin.cluster.refresh', 'Refresh')}
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
        {data?.nodes.map((node) => (
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
              <span className="flex items-center gap-1">
                <Thermometer className="w-3 h-3" /> Temp
              </span>
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" /> Util
              </span>
              <span className="flex items-center gap-1">
                <HardDrive className="w-3 h-3" /> VRAM
              </span>
            </div>
          </div>
          <div className="space-y-0.5">
            {gpuNode.gpus.map((gpu) => (
              <GpuMiniBar key={gpu.id} gpu={gpu} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ClusterHealthPanel;
