import React from 'react';
import { 
  ShieldCheck, 
  TrendingUp, 
  DollarSign, 
  Heart, 
  AlertCircle, 
  PieChart, 
  Zap, 
  Activity, 
  RefreshCw, 
  Wrench,
  BarChart3,
  Cpu,
  Trophy,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useAuthStore } from '../../store/authStore';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

const TransparencyPage: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  const { data, isLoading, refetch } = useQuery<any>({
    queryKey: ['transparency'],
    queryFn: () => apiClient('/api/v1/transparency/'),
  });

  const adminActionMutation = useMutation({
    mutationFn: async (action: string) => {
        return apiClient('/api/v1/transparency/', {
            method: 'POST',
            body: JSON.stringify({ action }),
            headers: { 'Content-Type': 'application/json' }
        });
    },
    onSuccess: () => {
        refetch();
    }
  });

  if (isLoading) return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );

  if (!data) return null;

  return (
    
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-4">
            OPEN <span className="text-emerald-500 text-glow">LEDGER</span>
          </h1>
          <p className="text-gray-500 font-bold uppercase tracking-widest flex items-center justify-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-500" /> Transparence Totale & Éthique IA
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-12">
          <StatCard title="Donations" value={`${data.total_donations}€`} icon={<Heart className="text-red-500" />} />
          <StatCard title="RAG Fidelity" value={`${(data.rag_fidelity * 100).toFixed(1)}%`} icon={<Zap className="text-blue-500" />} />
          <StatCard title="Inference Latency" value={`${data.average_latency}s`} icon={<Activity className="text-purple-500" />} />
          <StatCard title="Uptime" value={`${data.model_uptime}%`} icon={<ShieldCheck className="text-emerald-500" />} />
          <StatCard title="Balance" value={`${data.balance}€`} icon={<DollarSign className="text-emerald-500" />} />
        </div>

        {/* SOTA Benchmarks Section */}
        <div className="mb-12">
            <header className="flex justify-between items-end mb-8">
                <div>
                    <h2 className="text-4xl font-black italic manga-font uppercase mb-1">
                        SOTA <span className="text-blue-500">BENCHMARKS</span>
                    </h2>
                    <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.3em]">HuggingFace Best Models & Open Source Leaderboard (2026)</p>
                </div>
                <div className="flex items-center gap-4">
                    <Badge variant="neutral" className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[8px] py-1 px-3">SOTA V4.2</Badge>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.sota_benchmarks?.map((model: any, i: number) => (
                    <motion.div
                        key={model.model_id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                    >
                        <Card padding="none" className="bg-black border-white/5 overflow-hidden group hover:border-blue-500/30 transition-all hover:scale-[1.02]">
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500">
                                        <Cpu className="w-5 h-5" />
                                    </div>
                                    <Badge variant={model.is_open_source ? 'success' : 'neutral'} className="text-[8px] py-0.5 px-2">
                                        {model.is_open_source ? 'OPEN SOURCE' : 'PROPRIETARY'}
                                    </Badge>
                                </div>
                                <h3 className="text-lg font-black italic uppercase truncate mb-1" title={model.model_id}>{model.model_id.split('/').pop()}</h3>
                                <p className="text-[10px] font-bold opacity-30 uppercase mb-6 tracking-widest">{model.provider}</p>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                                        <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1"><Trophy className="w-2 h-2" /> ELO SCORE</p>
                                        <p className="text-xl font-black italic manga-font text-emerald-500">{model.elo_score}</p>
                                    </div>
                                    <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                                        <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1"><Zap className="w-2 h-2" /> MMLU</p>
                                        <p className="text-xl font-black italic manga-font text-blue-500">{model.mmlu_score}%</p>
                                    </div>
                                </div>

                                <div className="space-y-2 mb-6">
                                    <div className="flex justify-between items-center text-[9px] font-bold">
                                        <span className="opacity-40 uppercase">Context Window</span>
                                        <span className="uppercase">{model.context_window / 1000}K tokens</span>
                                    </div>
                                    <div className="flex justify-between items-center text-[9px] font-bold">
                                        <span className="opacity-40 uppercase">License</span>
                                        <span className="uppercase truncate max-w-[100px]">{model.license}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="p-4 bg-white/5 border-t border-white/5 flex justify-between items-center">
                                <span className="text-[8px] font-black text-blue-400 opacity-60 uppercase flex items-center gap-1">
                                    <Activity className="w-2 h-2" /> {model.status}
                                </span>
                                {model.huggingface_id && (
                                    <a 
                                        href={`https://huggingface.co/${model.huggingface_id}`} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="p-2 bg-white/5 rounded-lg hover:bg-blue-500/20 text-white/40 hover:text-blue-400 transition-all"
                                    >
                                        <ExternalLink className="w-3 h-3" />
                                    </a>
                                )}
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
          {/* Recent Activity */}
          <Card padding="lg">
              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                  <PieChart className="w-4 h-4" /> Activité Financière Récente
              </h3>
              <div className="space-y-6">
                  {data.recent_donations.map((d: any, i: number) => (
                      <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl border border-gray-100 dark:border-white/5 shadow-inner">
                          <div>
                              <div className="font-black italic uppercase text-sm">{d.user}</div>
                              <div className="text-[10px] opacity-40">{d.date}</div>
                          </div>
                          <div className="text-emerald-500 font-black">+{d.amount}€</div>
                      </div>
                  ))}
                  {data.recent_donations.length === 0 && <p className="text-center opacity-20 italic">Aucune transaction.</p>}
              </div>
          </Card>

          {/* Embedding Drift Report */}
          <Card padding="lg" className="relative overflow-hidden">
              <div className="flex justify-between items-start mb-8">
                <h3 className="text-xs font-black uppercase opacity-40 tracking-[0.2em] flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-400" /> État de la Base Vectorielle (Drift)
                </h3>
                {user?.is_staff && (
                    <Button 
                        size="xs" 
                        variant="outline" 
                        className="text-[8px] font-black"
                        onClick={() => adminActionMutation.mutate('drift_baseline')}
                        disabled={adminActionMutation.isPending}
                    >
                        <RefreshCw className={`w-3 h-3 mr-1 ${adminActionMutation.isPending ? 'animate-spin' : ''}`} /> RECALIBRER
                    </Button>
                )}
              </div>

              <div className="space-y-6">
                  {data.embedding_drift && Object.entries(data.embedding_drift).map(([key, info]: [string, any]) => (
                      <div key={key} className="p-5 bg-gray-50 dark:bg-navy-900 rounded-3xl border border-white/5 shadow-inner group hover:border-blue-500/30 transition-colors">
                          <div className="flex justify-between items-center mb-3">
                              <span className="font-black italic uppercase text-xs tracking-widest">{key.toUpperCase()}</span>
                              <Badge variant={info.status === 'healthy' ? 'success' : 'danger'}>
                                  {info.status}
                              </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-1">
                                  <p className="text-[9px] font-bold opacity-30 uppercase">P-Value (KS Test)</p>
                                  <p className={`text-lg font-black italic manga-font ${info.p_value < 0.05 ? 'text-red-500' : 'text-emerald-500'}`}>
                                    {info.p_value?.toFixed(4) ?? 'N/A'}
                                  </p>
                              </div>
                              <div className="space-y-1">
                                  <p className="text-[9px] font-bold opacity-30 uppercase">Échantillon</p>
                                  <p className="text-lg font-black italic manga-font">{info.sample_size ?? 0} items</p>
                              </div>
                          </div>
                          {info.p_value < 0.05 && (
                              <div className="mt-3 flex items-center gap-2 text-[8px] font-black text-red-500 uppercase animate-pulse">
                                  <AlertCircle className="w-3 h-3" /> Dérive détectée - Ré-entraînement conseillé
                              </div>
                          )}
                      </div>
                  ))}
                  {!data.embedding_drift && <div className="text-center py-8 opacity-20 italic">Données de dérive indisponibles.</div>}
              </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Ethics & Commitments */}
          <Card padding="lg" className="bg-brand-primary text-white border-none relative overflow-hidden flex flex-col justify-between h-full shadow-brand-primary/20">
              <AlertCircle className="w-40 h-40 absolute -right-8 -bottom-8 opacity-10" />
              <div>
                  <h3 className="text-3xl font-black italic manga-font mb-6 leading-tight uppercase tracking-tighter">NOS ENGAGEMENTS ÉTHIQUES</h3>
                  <div className="space-y-6 opacity-90 font-bold text-sm italic uppercase tracking-wider">
                      <p className="flex items-center gap-3"><ShieldCheck className="w-4 h-4 text-emerald-300" /> Aucune donnée utilisateur n'est revendue.</p>
                      <p className="flex items-center gap-3"><ShieldCheck className="w-4 h-4 text-emerald-300" /> Modèles IA prioritairement Open Source.</p>
                      <p className="flex items-center gap-3"><ShieldCheck className="w-4 h-4 text-emerald-300" /> 100% des fonds pour l'infrastructure.</p>
                  </div>
              </div>
              <div className="mt-12 pt-8 border-t border-white/20">
                  <div className="flex justify-between items-end">
                      <span className="text-[10px] font-black uppercase tracking-widest opacity-60 italic">Algorithmic Trust Score</span>
                      <span className="text-7xl font-black italic manga-font leading-none drop-shadow-lg">{data.ethics_score}%</span>
                  </div>
              </div>
          </Card>

          {/* Knowledge Graph Insights */}
          <Card padding="lg" className="bg-black text-white border-white/10 shadow-2xl relative overflow-hidden">
              <div className="flex justify-between items-start mb-8 relative z-10">
                <h3 className="text-3xl font-black italic manga-font flex items-center gap-3 uppercase tracking-tighter">
                    <Zap className="w-8 h-8 text-yellow-400" /> GRAPH INSIGHTS
                </h3>
                {user?.is_staff && (
                    <Button 
                        size="xs" 
                        variant="outline" 
                        className="text-[8px] font-black border-white/20 hover:bg-white/10"
                        onClick={() => adminActionMutation.mutate('graph_cleanup')}
                        disabled={adminActionMutation.isPending}
                    >
                        <Wrench className={`w-3 h-3 mr-1 ${adminActionMutation.isPending ? 'animate-spin' : ''}`} /> RÉPARER LE GRAPHE
                    </Button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-6 relative z-10">
                  <div className="p-6 bg-white/5 rounded-3xl border border-white/5 hover:bg-white/10 transition-colors">
                      <p className="text-[10px] font-black opacity-40 uppercase mb-2 tracking-widest text-red-400">Conflits Logiques</p>
                      <p className="text-5xl font-black italic manga-font text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.3)]">{data.knowledge_graph?.temporal_conflicts ?? 0}</p>
                  </div>
                  <div className="p-6 bg-white/5 rounded-3xl border border-white/5 hover:bg-white/10 transition-colors">
                      <p className="text-[10px] font-black opacity-40 uppercase mb-2 tracking-widest text-yellow-400">Nœuds Isolés</p>
                      <p className="text-5xl font-black italic manga-font text-yellow-500 drop-shadow-[0_0_15px_rgba(234,179,8,0.3)]">{data.knowledge_graph?.isolated_nodes ?? 0}</p>
                  </div>
              </div>
              
              <div className="mt-8 p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-4 relative z-10">
                  <div className="p-2 bg-yellow-500/20 rounded-lg">
                      <BarChart3 className="w-4 h-4 text-yellow-500" />
                  </div>
                  <div>
                      <p className="text-[10px] font-black uppercase opacity-60">Dernier Cycle de Guérison</p>
                      <p className="text-[9px] font-bold opacity-40 uppercase italic">Le Knowledge Graph est auto-nettoyé toutes les 24h par l'agent GraphHealer.</p>
                  </div>
              </div>

              {/* Decorative background element */}
              <Zap className="absolute -right-20 -bottom-20 w-80 h-80 opacity-[0.02] text-yellow-400 rotate-12" />
          </Card>
        </div>

        {/* Admin Feedback Box */}
        {adminActionMutation.isSuccess && (
            <div className="mt-12 p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-4 animate-fade-in">
                <ShieldCheck className="w-6 h-6 text-emerald-500" />
                <p className="text-xs font-black text-emerald-500 uppercase tracking-widest">
                    Action exécutée avec succès. Les métriques ont été synchronisées.
                </p>
            </div>
        )}
      </div>
    
  );
};

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon }) => (
    <Card padding="lg" className="text-center transition-all hover:scale-105 border-white/5 bg-navy-900/30">
        <div className="w-14 h-14 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner border border-gray-100 dark:border-white/5">
            {icon}
        </div>
        <div className="text-4xl font-black italic manga-font mb-1">{value}</div>
        <div className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em]">{title}</div>
    </Card>
);

export default TransparencyPage;
