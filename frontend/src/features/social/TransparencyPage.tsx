import React from 'react';
import { ShieldCheck, TrendingUp, DollarSign, Heart, AlertCircle, PieChart, Zap, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

const TransparencyPage: React.FC = () => {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery<any>({
    queryKey: ['transparency'],
    queryFn: () => apiClient('/api/v1/transparency/'),
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
    
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-4">
            OPEN <span className="text-emerald-500">LEDGER</span>
          </h1>
          <p className="text-gray-500 font-bold uppercase tracking-widest flex items-center justify-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-500" /> Transparence Totale & Éthique IA
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <StatCard title="Donations Totales" value={`${data.total_donations}€`} icon={<Heart className="text-red-500" />} />
          <StatCard title="Coûts IA / Serveurs" value={`${data.api_costs + data.server_costs}€`} icon={<TrendingUp className="text-orange-500" />} />
          <StatCard title="Project Balance" value={`${data.balance}€`} icon={<DollarSign className="text-emerald-500" />} />
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
          <Card padding="lg">
              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" /> État de la Base Vectorielle (Drift)
              </h3>
              <div className="space-y-6">
                  {data.embedding_drift && Object.entries(data.embedding_drift).map(([key, info]: [string, any]) => (
                      <div key={key} className="p-5 bg-gray-50 dark:bg-navy-900 rounded-3xl border border-white/5 shadow-inner">
                          <div className="flex justify-between items-center mb-3">
                              <span className="font-black italic uppercase text-xs">{key.toUpperCase()}</span>
                              <Badge variant={info.status === 'healthy' ? 'success' : 'danger'}>
                                  {info.status}
                              </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-1">
                                  <p className="text-[9px] font-bold opacity-30 uppercase">P-Value (KS Test)</p>
                                  <p className="text-lg font-black italic manga-font">{info.p_value ?? 'N/A'}</p>
                              </div>
                              <div className="space-y-1">
                                  <p className="text-[9px] font-bold opacity-30 uppercase">Échantillon</p>
                                  <p className="text-lg font-black italic manga-font">{info.sample_size ?? 0} items</p>
                              </div>
                          </div>
                      </div>
                  ))}
              </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Ethics & Commitments */}
          <Card padding="lg" className="bg-brand-primary text-white border-none relative overflow-hidden flex flex-col justify-between h-full shadow-brand-primary/20">
              <AlertCircle className="w-40 h-40 absolute -right-8 -bottom-8 opacity-10" />
              <div>
                  <h3 className="text-3xl font-black italic manga-font mb-6 leading-tight uppercase">NOS ENGAGEMENTS ÉTHIQUES</h3>
                  <div className="space-y-6 opacity-90 font-bold text-sm italic">
                      <p>• Aucune donnée utilisateur n'est revendue à des tiers.</p>
                      <p>• Les modèles IA utilisés sont prioritairement Open Source.</p>
                      <p>• 100% des donations servent à payer les coûts d'infrastructure.</p>
                  </div>
              </div>
              <div className="mt-8 pt-8 border-t border-white/20">
                  <div className="flex justify-between items-end">
                      <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Ethics Score</span>
                      <span className="text-5xl font-black italic manga-font">{data.ethics_score}%</span>
                  </div>
              </div>
          </Card>

          {/* Knowledge Graph Insights */}
          <Card padding="lg" className="bg-black text-white border-white/10 shadow-2xl">
              <h3 className="text-3xl font-black italic manga-font mb-8 flex items-center gap-3 uppercase">
                  <Zap className="w-8 h-8 text-yellow-400" /> GRAPH INSIGHTS
              </h3>
              <div className="grid grid-cols-2 gap-6">
                  <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                      <p className="text-[10px] font-black opacity-40 uppercase mb-2">Conflits Logiques</p>
                      <p className="text-4xl font-black italic manga-font text-red-400">{data.knowledge_graph?.temporal_conflicts ?? 0}</p>
                  </div>
                  <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                      <p className="text-[10px] font-black opacity-40 uppercase mb-2">Nœuds Isolés</p>
                      <p className="text-4xl font-black italic manga-font text-yellow-400">{data.knowledge_graph?.isolated_nodes ?? 0}</p>
                  </div>
              </div>
              <p className="mt-8 text-[10px] italic opacity-40 leading-relaxed uppercase font-black tracking-wider">Le Knowledge Graph est auto-nettoyé toutes les 24h par l'agent GraphHealer.</p>
          </Card>
        </div>
      </div>
    
  );
};

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon }) => (
    <Card padding="lg" className="text-center transition-all hover:scale-105">
        <div className="w-14 h-14 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner border border-gray-100 dark:border-white/5">
            {icon}
        </div>
        <div className="text-3xl font-black mb-1">{value}</div>
        <div className="text-[10px] font-black uppercase opacity-30 tracking-widest">{title}</div>
    </Card>
);

export default TransparencyPage;
