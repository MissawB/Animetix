import React, { useState } from 'react';
import { 
  Cpu, 
  Database, 
  Settings, 
  Server, 
  Activity, 
  Play, 
  RefreshCw, 
  Terminal,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useHealth } from '../../features/admin/hooks/useHealth';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Skeleton } from "../../components/ui/Skeleton";
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";

import { AnimatedPage } from "../../components/ui/AnimatedPage";

const HealthPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading } = useHealth();
  const [lastAction, setLastAction] = useState<{msg: string, status: 'success'|'error'} | null>(null);

  const pipelineMutation = useMutation({
    mutationFn: (action: string) => 
        apiClient(`/api/v1/admin/pipelines/control/${action}/`, { method: 'POST' }),
    onSuccess: (res) => setLastAction({ msg: res.status || "Action réussie", status: 'success' }),
    onError: (err: any) => setLastAction({ msg: err.message || "Échec de l'action", status: 'error' })
  });

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#0a0a14] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-16 text-black dark:text-white">
            <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-6">
                <div>
                    <h1 className="text-6xl font-black italic manga-font tracking-tighter flex items-center gap-4 uppercase">
                        <Activity className="w-12 h-12 text-blue-500" /> System <span className="text-blue-500">Core</span>
                    </h1>
                    <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] mt-2">
                        Monitoring en temps réel et pilotage des pipelines.
                    </p>
                </div>
                
                {lastAction && (
                    <motion.div 
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={`px-6 py-3 rounded-2xl border-2 flex items-center gap-3 font-black uppercase text-[10px] tracking-widest ${lastAction.status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' : 'bg-red-500/10 border-red-500/20 text-red-500'}`}
                    >
                        {lastAction.status === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                        {lastAction.msg}
                    </motion.div>
                )}
            </header>
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                
                {/* Status Cards */}
                <div className="lg:col-span-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <HealthCard title="BRAIN API" status={isLoading ? '...' : data?.brain_status} Icon={Cpu} color="blue" loading={isLoading} />
                        <HealthCard title="REDIS CACHE" status={isLoading ? '...' : data?.cache_status} Icon={Database} color="amber" loading={isLoading} />
                        <HealthCard title="CELERY" status={isLoading ? '...' : data?.celery_status} Icon={Settings} color="purple" loading={isLoading} />
                        <HealthCard title="POSTGRES" status={isLoading ? '...' : "Connected"} Icon={Server} color="emerald" loading={isLoading} />
                    </div>

                    {/* Quick Logs / Terminal Placeholder */}
                    <Card padding="lg" className="bg-black border-white/5 shadow-2xl rounded-[3rem] overflow-hidden">
                        <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-6">
                            <Terminal className="w-4 h-4 text-blue-500" /> Output Stream (Pipeline)
                        </h3>
                        <div className="font-mono text-[10px] text-blue-500/60 space-y-2 max-h-48 overflow-y-auto custom-scrollbar italic leading-relaxed">
                            <p>[{new Date().toLocaleTimeString()}] CRON: scheduled_sync_neo4j ... OK</p>
                            <p>[{new Date().toLocaleTimeString()}] worker_1: task_id=7782 started (lore_ingestion)</p>
                            <p>[{new Date().toLocaleTimeString()}] guardrail: violation_detected user_id=anonymous action=block</p>
                            <p className="animate-pulse">_</p>
                        </div>
                    </Card>
                </div>

                {/* Pipeline Control Sidebar */}
                <aside className="lg:col-span-4">
                    <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-2xl rounded-[3rem] sticky top-32">
                        <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-8">
                            <Play className="w-4 h-4 text-emerald-500" /> Pipeline Control
                        </h3>

                        <div className="space-y-6">
                            <ControlButton 
                                label="Run Scrapers" 
                                desc="Lancer l'extraction Jikan/AniList." 
                                icon={RefreshCw} 
                                onClick={() => pipelineMutation.mutate('run_scraper')}
                                loading={pipelineMutation.isPending && pipelineMutation.variables === 'run_scraper'}
                            />
                            <ControlButton 
                                label="Sync Neo4j" 
                                desc="Synchroniser le Knowledge Graph." 
                                icon={Database} 
                                onClick={() => pipelineMutation.mutate('sync_neo4j')}
                                loading={pipelineMutation.isPending && pipelineMutation.variables === 'sync_neo4j'}
                            />
                            <ControlButton 
                                label="Beam Ingestion" 
                                desc="Déclencher le pipeline Lore Dataflow." 
                                icon={ArrowRight} 
                                onClick={() => pipelineMutation.mutate('run_beam_ingestion')}
                                loading={pipelineMutation.isPending && pipelineMutation.variables === 'run_beam_ingestion'}
                            />
                        </div>

                        <div className="mt-12 pt-8 border-t border-black/5 dark:border-white/5">
                            <div className="flex items-center gap-3 text-emerald-500/40 text-[9px] font-black uppercase tracking-widest italic">
                                <ShieldCheck size={14} />
                                <span>Accès restreint au staff</span>
                            </div>
                        </div>
                    </Card>
                </aside>

            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

interface HealthCardProps {
  title: string;
  status: string | undefined;
  Icon: React.ElementType;
  color: string;
  loading?: boolean;
}

const HealthCard: React.FC<HealthCardProps> = ({ title, status, Icon, color, loading }) => (
    <Card padding="lg" className="border-none shadow-xl bg-white dark:bg-[#0f0f1a] group hover:scale-[1.02] transition-all duration-300">
        <div className="flex justify-between items-center">
            <h2 className="text-xl font-black italic manga-font flex items-center gap-3">
                <Icon className={`text-${color}-500 w-6 h-6 group-hover:rotate-12 transition-transform`} /> {title}
            </h2>
            {loading ? (
                <Skeleton variant="rectangular" className="w-20 h-6" />
            ) : (
                <Badge variant={status === 'Online' || status === 'Connected' ? 'success' : 'danger'} className="font-black italic px-4 py-1">
                    {status?.toUpperCase()}
                </Badge>
            )}
        </div>
    </Card>
);

const ControlButton: React.FC<{label: string, desc: string, icon: any, onClick: () => void, loading: boolean}> = ({ label, desc, icon: Icon, onClick, loading }) => (
    <button 
        onClick={onClick}
        disabled={loading}
        className="w-full text-left group p-4 rounded-2xl hover:bg-gray-50 dark:hover:bg-white/[0.03] transition-all border border-transparent hover:border-black/5 dark:hover:border-white/5 relative overflow-hidden"
    >
        <div className="flex justify-between items-center mb-1">
            <span className="text-[11px] font-black uppercase tracking-widest text-black dark:text-white group-hover:text-blue-500 transition-colors">{label}</span>
            {loading ? <RefreshCw className="w-3 h-3 animate-spin text-blue-500" /> : <Icon className="w-3 h-3 opacity-20 group-hover:opacity-100 group-hover:text-blue-500 transition-all" />}
        </div>
        <p className="text-[9px] font-bold opacity-30 uppercase tracking-wider">{desc}</p>
        {loading && <div className="absolute bottom-0 left-0 h-0.5 bg-blue-500 animate-progress-indefinite w-full" />}
    </button>
);

export default HealthPage;


