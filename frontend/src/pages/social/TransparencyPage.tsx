import React from 'react';
import { 
  ShieldCheck, 
  TrendingUp, 
  AlertCircle, 
  Zap, 
  Activity,
  Clock,
  Cpu,
  Trophy,
  ExternalLink,
  Users,
  Database,
  Lock,
  Brain,
  AlertTriangle,
  Scale} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";


import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import _Plot from 'react-plotly.js';

import { TransparencyData, ModelBenchmark } from '../../types';

const Plot =
  (_Plot as unknown as { default?: React.ComponentType<Record<string, unknown>> }).default ??
  (_Plot as unknown as React.ComponentType<Record<string, unknown>>);

const TransparencyPage: React.FC = () => {
  const { t } = useTranslation();
  
  

  const { data, isLoading } = useQuery<TransparencyData>({
    queryKey: ['transparency'],
    queryFn: () => apiClient('/api/v1/transparency/'),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-32 flex flex-col items-center justify-center">
        <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-8" />
        <p className="text-blue-500 font-black italic uppercase tracking-[0.3em] animate-pulse">{t('social.transparency.loading', 'Synchronisation avec le Nexus...')}</p>
    </div>
  );

  if (!data) return null;

  const metrics = data.global_metrics;

  // Timeline réelle (précision d'évaluation par mois). Le graphe n'est affiché
  // qu'à partir de deux points, sinon il ne serait pas lisible.
  const timeline = data.evolution_timeline || [];

  return (
    <div className="min-h-screen bg-[#05050a] text-white">
      {/* Hero Section with Live Pulse */}
      <section className="relative py-24 overflow-hidden border-b border-white/5">
          <div className="absolute inset-0 bg-gradient-to-b from-blue-600/10 to-transparent" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 blur-[120px] rounded-full animate-pulse" />
          
          <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
              {data.model_uptime != null && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-8">
                    <Activity className="w-3 h-3 animate-pulse" /> {t('social.transparency.uptime_badge', 'Fiabilité du modèle : {{pct}}% (réponses sans hallucination)', { pct: data.model_uptime })}
                </div>
              )}
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-6 leading-tight">
                  HUB DE <span className="text-blue-500">{t('social.transparency.title_accent', 'TRANSPARENCE')}</span> IA
              </h1>
              <p className="max-w-3xl mx-auto text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                  {t('social.transparency.subtitle', 'Découvrez comment vos interactions façonnent le cerveau d\'Animetix. Nous croyons en une intelligence artificielle ouverte, auditable et alignée sur sa communauté.')}
              </p>
          </div>
      </section>

      <div className="max-w-7xl mx-auto px-6 py-20 space-y-24">
        {/* Key Performance Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <Card className="bg-navy-900/20 border-white/5 p-8 flex flex-col items-center text-center transition-all hover:scale-105">
                <Users className="w-8 h-8 text-blue-500 mb-4" />
                <span className="text-4xl font-black italic mb-1">{(metrics?.total_feedbacks || 0).toLocaleString()}</span>
                <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{t('social.transparency.kpi_feedbacks', 'Feedbacks Reçus')}</span>
            </Card>
            <Card className="bg-navy-900/20 border-white/5 p-8 flex flex-col items-center text-center transition-all hover:scale-105">
                <Database className="w-8 h-8 text-emerald-500 mb-4" />
                <span className="text-4xl font-black italic mb-1">{(metrics?.knowledge_nodes || 0).toLocaleString()}</span>
                <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{t('social.transparency.kpi_engrams', 'Engrammes Indexés')}</span>
            </Card>
            <Card className="bg-navy-900/20 border-white/5 p-8 flex flex-col items-center text-center transition-all hover:scale-105">
                <Brain className="w-8 h-8 text-purple-500 mb-4" />
                <span className="text-4xl font-black italic mb-1">{(metrics?.community_satisfaction * 100).toFixed(0)}%</span>
                <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{t('social.transparency.kpi_satisfaction', 'Satisfaction IA')}</span>
            </Card>
            <Card className="bg-navy-900/20 border-white/5 p-8 flex flex-col items-center text-center transition-all hover:scale-105">
                <Zap className="w-8 h-8 text-yellow-500 mb-4" />
                <span className="text-2xl font-black italic mb-1 uppercase line-clamp-1">{metrics?.model_version || 'Champion v2.4'}</span>
                <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{t('social.transparency.kpi_version', 'Version Actuelle')}</span>
            </Card>
        </div>

        {/* Evolution Chart */}
        <section>
            <div className="flex items-center justify-between mb-12">
                <h2 className="text-4xl font-black italic uppercase manga-font tracking-tighter flex items-center gap-4">
                    <TrendingUp className="w-10 h-10 text-blue-500" /> {t('social.transparency.evolution_title', 'Évolution du Modèle Expert')}
                </h2>
                <Badge variant="neutral" className="bg-white/5 border-white/10 uppercase text-[10px] py-2 px-4">Metric: Semantic Accuracy</Badge>
            </div>
            
            <Card className="bg-navy-900/20 border-white/5 p-10 h-[450px]">
                {timeline.length >= 2 ? (
                    <Plot
                        data={[{
                            x: timeline.map((d) => d.date),
                            y: timeline.map((d) => d.accuracy),
                            type: 'scatter',
                            mode: 'lines',
                            fill: 'tozeroy',
                            line: { color: '#3b82f6', width: 4, shape: 'spline' },
                            fillcolor: 'rgba(59,130,246,0.18)',
                            hovertemplate: 'Accuracy: %{y:.0%}<extra></extra>',
                        }]}
                        layout={{
                            autosize: true,
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            margin: { l: 44, r: 20, t: 10, b: 36 },
                            xaxis: { gridcolor: 'rgba(255,255,255,0.03)', tickfont: { color: '#ffffff33', size: 10 }, showline: false, zeroline: false },
                            yaxis: { gridcolor: 'rgba(255,255,255,0.03)', tickfont: { color: '#ffffff33', size: 10 }, showline: false, zeroline: false, tickformat: '.0%' },
                            font: { family: 'Montserrat', color: '#fff' },
                            hovermode: 'x unified',
                            showlegend: false,
                        }}
                        config={{ responsive: true, displayModeBar: false }}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler
                    />
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                        <TrendingUp className="w-12 h-12 mb-4" />
                        <p className="text-xs font-black uppercase tracking-widest">{t('social.transparency.not_enough_data', 'Pas encore assez de données d\'évaluation')}</p>
                        <p className="text-[10px] font-bold uppercase tracking-widest mt-1 opacity-60">{t('social.transparency.chart_hint', 'La courbe apparaîtra dès plusieurs cycles d\'évaluation enregistrés.')}</p>
                    </div>
                )}
            </Card>
        </section>

        {/* SOTA Benchmarks & Embedding Drift */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-12">
            <div className="xl:col-span-2 space-y-12">
                <header>
                    <h2 className="text-3xl font-black italic manga-font uppercase mb-1">
                        SOTA <span className="text-blue-500">BENCHMARKS</span>
                    </h2>
                    <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.3em]">HuggingFace Best Models (2026)</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {data.sota_benchmarks?.map((model: ModelBenchmark, i: number) => (
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

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                                            <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1"><Trophy className="w-2 h-2" /> ELO SCORE</p>
                                            <p className="text-xl font-black italic manga-font text-emerald-500">{model.elo_score}</p>
                                        </div>
                                        <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                                            <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1"><Zap className="w-2 h-2" /> MMLU</p>
                                            <p className="text-xl font-black italic manga-font text-blue-500">{model.mmlu_score}%</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-4 bg-white/5 border-t border-white/5 flex justify-between items-center text-[10px] font-black uppercase text-blue-400 opacity-60">
                                    <span className="flex items-center gap-1"><Activity className="w-2 h-2" /> {model.status}</span>
                                    {model.huggingface_id && <ExternalLink className="w-3 h-3" />}
                                </div>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            </div>

            <div className="space-y-12">
                <header>
                    <h2 className="text-3xl font-black italic manga-font uppercase mb-1">
                        DRIFT <span className="text-blue-500">AUDIT</span>
                    </h2>
                    <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.2em]">{t('social.transparency.vector_base', 'Base Vectorielle')}</p>
                </header>

                <div className="space-y-4">
                    {data.embedding_drift && Object.entries(data.embedding_drift).map(([key, info]: [string, { status: string; p_value?: number; sample_size?: number }]) => (
                        <div key={key} className="p-6 bg-white/5 rounded-3xl border border-white/5 flex flex-col gap-4 group hover:bg-white/10 transition-all">
                            <div className="flex justify-between items-center">
                                <span className="font-black italic uppercase text-xs tracking-widest">{key}</span>
                                <Badge variant={info.status === 'healthy' ? 'success' : info.status === 'alert' ? 'danger' : 'neutral'}>{info.status}</Badge>
                            </div>
                            <div className="flex items-end justify-between">
                                <div>
                                    <p className="text-[8px] font-black opacity-30 uppercase mb-1">P-Value (KS Test)</p>
                                    <p className={`text-2xl font-black italic manga-font ${info.p_value == null ? 'text-gray-500' : info.p_value < 0.05 ? 'text-red-500' : 'text-emerald-500'}`}>
                                        {info.p_value != null ? info.p_value.toFixed(4) : 'N/A'}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-[8px] font-black opacity-30 uppercase mb-1">{t('social.transparency.sample', 'Échantillon')}</p>
                                    <p className="text-sm font-bold uppercase tracking-tighter">{info.sample_size != null ? `${info.sample_size} items` : '—'}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Ethics & Commitments */}
            <Card padding="lg" className="bg-blue-600 text-white border-none relative overflow-hidden flex flex-col justify-between h-full shadow-blue-600/20 rounded-[3rem]">
                <AlertCircle className="w-40 h-40 absolute -right-8 -bottom-8 opacity-10" />
                <div>
                    <h3 className="text-4xl font-black italic manga-font mb-8 leading-tight uppercase tracking-tighter">{t('social.transparency.ethics_title', 'ENGAGEMENTS ÉTHIQUES')}</h3>
                    <div className="space-y-6 opacity-90 font-bold text-sm italic uppercase tracking-wider">
                        <p className="flex items-center gap-4"><ShieldCheck className="w-5 h-5 text-blue-200" /> {t('social.transparency.ethics_1', 'Aucune donnée utilisateur n\'est revendue.')}</p>
                        <p className="flex items-center gap-4"><ShieldCheck className="w-5 h-5 text-blue-200" /> {t('social.transparency.ethics_2', 'Modèles IA prioritairement Open Source.')}</p>
                        <p className="flex items-center gap-4"><ShieldCheck className="w-5 h-5 text-blue-200" /> {t('social.transparency.ethics_3', 'Infrastructure 100% transparente.')}</p>
                    </div>
                </div>
                <div className="mt-12 pt-8 border-t border-white/20">
                    <div className="flex justify-between items-end">
                        <span className="text-[10px] font-black uppercase tracking-widest opacity-60 italic">Algorithmic Trust Score</span>
                        {data.ethics_score != null ? (
                            <span className="text-7xl font-black italic manga-font leading-none drop-shadow-lg">{data.ethics_score}%</span>
                        ) : (
                            <span className="text-lg font-black italic uppercase tracking-widest opacity-70">{t('social.transparency.insufficient_data', 'Données insuffisantes')}</span>
                        )}
                    </div>
                </div>
            </Card>

            {/* Ethics Audit & Hallucination */}
            <section className="p-10 rounded-[3rem] bg-navy-900/40 border border-white/5 space-y-10">
                <h3 className="text-2xl font-black italic uppercase manga-font tracking-tight flex items-center gap-3 text-purple-400">
                    <Scale className="w-6 h-6" /> {t('social.transparency.security_audit', 'Audit de Sécurité')}
                </h3>
                <div className="space-y-8">
                    <AuditRow
                        label={t('social.transparency.safety_compliance', 'Conformité Sécurité')}
                        value={data.ethics_audit?.safety_compliance != null ? (data.ethics_audit.safety_compliance * 100).toFixed(1) : t('social.transparency.insufficient_data', 'Données insuffisantes')}
                        suffix={data.ethics_audit?.safety_compliance != null ? '%' : ''}
                        icon={<Lock className="text-purple-400" />}
                    />
                    <AuditRow
                        label={t('social.transparency.hallucination_rate', 'Taux d\'Hallucination')}
                        value={data.ethics_audit?.hallucination_rate != null ? (data.ethics_audit.hallucination_rate * 100).toFixed(1) : t('social.transparency.insufficient_data', 'Données insuffisantes')}
                        suffix={data.ethics_audit?.hallucination_rate != null ? '%' : ''}
                        icon={<AlertTriangle className="text-purple-400" />}
                    />
                </div>

                <p className="pt-8 border-t border-white/5 text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
                    {t('social.transparency.audit_footnote', 'Conformité = part des interactions évaluées non bloquées par le garde-fou. Hallucination = part des réponses signalées par l\'évaluation automatique.')}
                </p>
            </section>
        </div>

        {/* Participation CTA */}
        <section className="p-20 rounded-[4rem] bg-gradient-to-br from-blue-600 to-indigo-700 flex flex-col items-center text-center shadow-[0_0_60px_rgba(37,99,235,0.4)] relative overflow-hidden group">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
            <h2 className="text-6xl font-black italic manga-font uppercase mb-8 tracking-tighter relative z-10">{t('social.transparency.cta_title', 'Devenez Curateur du Nexus')}</h2>
            <p className="max-w-3xl text-blue-100 font-bold uppercase tracking-widest text-xs mb-12 leading-relaxed relative z-10 opacity-80">
                {t('social.transparency.cta_desc', 'Chaque interaction avec l\'IA renforce la base de connaissance commune. Grâce au protocole DPO (Direct Preference Optimization), vos choix guident l\'apprentissage du modèle Champion.')}
            </p>
            <div className="flex flex-wrap gap-6 justify-center relative z-10">
                <Button as={Link} to="/lab/" variant="primary" className="bg-white text-blue-600 px-12 py-7 rounded-2xl border-none shadow-xl hover:scale-105 transition-transform font-black italic uppercase no-underline">{t('social.transparency.cta_lab', 'DÉCOUVRIR LE LAB')}</Button>
                <Button as={Link} to="/research/papers/" variant="outline" className="border-white/30 text-white hover:bg-white/10 px-12 py-7 rounded-2xl font-black italic uppercase no-underline">{t('social.transparency.cta_research', 'LA RECHERCHE IA')}</Button>
            </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 bg-black/40">
           <div className="max-w-7xl mx-auto px-6 flex items-center justify-center gap-4 opacity-30">
               <Clock className="w-5 h-5" />
               <span className="text-[10px] font-black uppercase tracking-widest">
                   {metrics?.last_training
                       ? t('social.transparency.last_eval', 'Dernière évaluation : {{date}}', { date: metrics.last_training })
                       : t('social.transparency.no_eval', 'Aucune évaluation enregistrée pour le moment')}
               </span>
           </div>
      </footer>
    </div>
  );
};

const AuditRow = ({ label, value, suffix, icon }: { label: string, value: number | string, suffix: string, icon: React.ReactNode }) => (
    <div className="flex items-center justify-between group">
        <div className="flex items-center gap-4">
            <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-purple-500/10 transition-colors">{icon}</div>
            <span className="text-[11px] font-black uppercase tracking-widest opacity-60">{label}</span>
        </div>
        <span className="font-black italic text-sm">{typeof value === 'number' && value < 1 ? value.toFixed(3) : value}{suffix}</span>
    </div>
);

export default TransparencyPage;
