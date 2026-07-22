import React from 'react';
import { Server, Clock, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import {
  ClusterNode,
  statusConfig,
  nodeTypeIcon,
  nodeTypeAccent,
} from '../../../features/admin/types/clusterHealth';
import { StatusDot } from './StatusDot';

export const NodeCard: React.FC<{ node: ClusterNode }> = ({ node }) => {
  const { t } = useTranslation();
  const config = statusConfig[node.status as keyof typeof statusConfig] || statusConfig.offline;
  const IconComponent = nodeTypeIcon[node.type] || Server;
  const accentColor = nodeTypeAccent[node.type] || 'text-white';

  return (
    <Card
      padding="lg"
      className={`bg-black/40 border-white/5 hover:${config.border} transition-all duration-500 group relative overflow-hidden`}
    >
      {/* Ambient glow */}
      <div
        className={`absolute -top-20 -right-20 w-40 h-40 rounded-full ${config.bg} blur-3xl opacity-30 group-hover:opacity-50 transition-opacity`}
      />

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
        {node.type === 'gpu'
          ? 'Compute Cluster'
          : node.type === 'inference'
            ? 'LLM Engine'
            : 'Knowledge Base'}
      </p>

      {/* Latency */}
      {node.latency_ms !== null && (
        <div className="flex items-center gap-2 mb-4 relative z-10">
          <Clock className="w-3 h-3 opacity-30" />
          <span className="text-[10px] font-bold uppercase opacity-40">
            {t('admin.cluster.latency', 'Latence')}
          </span>
          <span
            className={`text-sm font-black ml-auto ${
              node.latency_ms < 50
                ? 'text-emerald-400'
                : node.latency_ms < 200
                  ? 'text-amber-400'
                  : 'text-red-400'
            }`}
          >
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
              <p className="text-2xl font-black italic manga-font text-green-400">
                {node.details.gpu_count}
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">VRAM Total</p>
              <p className="text-2xl font-black italic manga-font">
                {node.details.total_vram_gb}
                <span className="text-xs opacity-40">GB</span>
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">
                {t('admin.cluster.temp_avg', 'Temp Moy.')}
              </p>
              <p
                className={`text-lg font-black ${
                  (node.details.avg_temperature_c ?? 0) > 75
                    ? 'text-red-400'
                    : (node.details.avg_temperature_c ?? 0) > 55
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                }`}
              >
                {node.details.avg_temperature_c}°C
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">
                {t('admin.cluster.util_avg', 'Util. Moy.')}
              </p>
              <p className="text-lg font-black text-cyan-400">
                {node.details.avg_utilization_pct}%
              </p>
            </div>
          </div>
          <div className="pt-3 border-t border-white/5 flex justify-between">
            <span className="text-[9px] font-bold opacity-25 uppercase">
              CUDA {node.details.cuda_version}
            </span>
            <span className="text-[9px] font-bold opacity-25 uppercase">
              Driver {node.details.driver_version}
            </span>
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
              <p className="text-[9px] font-black uppercase opacity-25 mb-2">
                {t('admin.cluster.loaded_models', 'Modèles Chargés')} ({node.details.model_count})
              </p>
              <div className="flex flex-wrap gap-1">
                {node.details.loaded_models.slice(0, 6).map((m: string, i: number) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-bold text-cyan-400 uppercase"
                  >
                    {m}
                  </span>
                ))}
                {node.details.loaded_models.length > 6 && (
                  <span className="px-2 py-0.5 text-[9px] font-bold opacity-30">
                    +{node.details.loaded_models.length - 6}
                  </span>
                )}
              </div>
            </div>
          )}
          {node.details.error && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
              <span className="text-[9px] font-bold text-red-400 uppercase break-all">
                {node.details.error}
              </span>
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
              <span className="text-[9px] font-bold text-red-400 uppercase break-all">
                {node.details.error}
              </span>
            </div>
          )}
        </div>
      )}

      {node.type === 'worker' && node.details && (
        <div className="space-y-3 relative z-10">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">
                {t('admin.cluster.queue_length', "File d'attente")}
              </p>
              <p className="text-2xl font-black italic manga-font text-pink-400">
                {node.details.queue_length || 0}
              </p>
            </div>
            <div>
              <p className="text-[9px] font-black uppercase opacity-25 mb-1">
                {t('admin.cluster.worker_status', 'Statut Worker')}
              </p>
              <p
                className={`text-sm font-black uppercase ${
                  node.details.worker_status === 'active' ? 'text-pink-300' : 'text-emerald-400'
                }`}
              >
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
            <span className="text-[9px] font-bold opacity-25 uppercase">
              {t('admin.cluster.api_fallback', 'Repli API')}
            </span>
            <Badge
              variant="neutral"
              className={`text-[9px] font-black uppercase px-2 py-0.5 rounded ${
                node.details.fallback_mode === 'active'
                  ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                  : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
              }`}
            >
              {node.details.fallback_mode === 'active'
                ? t('admin.cluster.fallback_active', 'ACTIF (Budget Dépassé)')
                : 'NOMINAL'}
            </Badge>
          </div>
        </div>
      )}
    </Card>
  );
};
