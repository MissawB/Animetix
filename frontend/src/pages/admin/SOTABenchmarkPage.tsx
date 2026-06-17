import React from 'react';
import { 
  Trophy, 
  Cpu, 
  BarChart3,
  Globe, 
  Zap,
  Activity,
  Code,
  Sparkles
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

import { BenchmarkData, ModelBenchmark } from '../../types';

const SOTABenchmarkPage: React.FC = () => {
  const { data, isLoading, isError } = useQuery<BenchmarkData>({
    queryKey: ['sota-benchmarks'],
    queryFn: () => apiClient('/api/v1/mlops/sota/benchmarks/'),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-32 flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_20px_rgba(6,182,212,0.5)]"></div>
        <p className="text-sm font-black uppercase tracking-[0.3em] animate-pulse opacity-40">Syncing SOTA Metrics...</p>
    </div>
  );

  if (isError || !data) return (
    <div className="max-w-7xl mx-auto px-6 py-32 text-center text-red-500">
        <h2 className="text-3xl font-black italic uppercase">Sync Failure</h2>
        <p className="opacity-50 mt-4">Impossible de récupérer les benchmarks en temps réel.</p>
    </div>
  );

  const { benchmarks, top_model, best_open_source } = data;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-12">
          
          {/* Header Dashboard */}
          <header className="mb-16 relative text-black dark:text-white">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-black/5 dark:border-white/10 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-4">
                  <Globe className="w-3 h-3" /> Global Intelligence Metrics
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  SOTA <span className="text-blue-500 text-glow">BENCHMARK</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Suivi en temps réel de la domination algorithmique et des capacités cognitives des modèles IA.
              </p>
          </header>

          {/* Top Model Spotlight */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16 text-black dark:text-white">
              <Card padding="none" className="bg-white dark:bg-[#0f0f1a] border-none shadow-2xl rounded-[3.5rem] overflow-hidden relative group">
                  <div className="absolute top-0 right-0 p-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Trophy className="w-48 h-48 -rotate-12" />
                  </div>
                  <div className="bg-blue-600 px-12 py-6 flex items-center justify-between">
                      <h3 className="text-2xl font-black italic manga-font uppercase text-white flex items-center gap-4">
                          <Zap className="w-8 h-8 fill-current" /> APEX MODEL
                      </h3>
                      <Badge variant="neutral" className="bg-black/20 text-white border-none uppercase font-black italic">Leaderboard #1</Badge>
                  </div>
                  <div className="p-12 relative z-10">
                      <h2 className="text-5xl font-black italic manga-font uppercase mb-2 tracking-tighter text-black dark:text-white">{top_model.model_id}</h2>
                      <p className="text-[10px] font-black uppercase tracking-widest text-blue-500 mb-8">Provider: {top_model.provider}</p>
                      
                      <div className="grid grid-cols-2 gap-8">
                          <div>
                              <p className="text-[8px] font-black opacity-30 uppercase mb-2">Arena ELO Score</p>
                              <p className="text-4xl font-black italic text-black dark:text-white">{top_model.elo_score}</p>
                          </div>
                          <div className="border-l border-black/5 dark:border-white/5 pl-8">
                              <p className="text-[8px] font-black opacity-30 uppercase mb-2">MMLU Accuracy</p>
                              <p className="text-4xl font-black italic text-emerald-500">{top_model.mmlu_score}%</p>
                          </div>
                      </div>
                  </div>
              </Card>

              <Card padding="none" className="bg-white dark:bg-[#0f0f1a] border-none shadow-2xl rounded-[3.5rem] overflow-hidden relative group">
                  <div className="bg-gray-50 dark:bg-white/5 px-12 py-6 flex items-center justify-between border-b border-black/5 dark:border-white/5">
                      <h3 className="text-2xl font-black italic manga-font uppercase text-black dark:text-white flex items-center gap-4">
                          <Code className="w-8 h-8" /> BEST OPEN SOURCE
                      </h3>
                      <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-500 border-none uppercase font-black italic">Weights Available</Badge>
                  </div>
                  <div className="p-12 relative z-10">
                      <h2 className="text-5xl font-black italic manga-font uppercase mb-2 tracking-tighter text-black dark:text-white">{best_open_source.model_id}</h2>
                      <p className="text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-8">License: {best_open_source.license}</p>
                      
                      <div className="grid grid-cols-2 gap-8">
                          <div>
                              <p className="text-[8px] font-black opacity-30 uppercase mb-2">Efficiency Rating</p>
                              <p className="text-4xl font-black italic text-black dark:text-white">S-TIER</p>
                          </div>
                          <div className="border-l border-black/5 dark:border-white/5 pl-8">
                              <p className="text-[8px] font-black opacity-30 uppercase mb-2">Context Window</p>
                              <p className="text-4xl font-black italic text-blue-400">{Math.floor(best_open_source.context_window / 1000)}k</p>
                          </div>
                      </div>
                  </div>
              </Card>
          </div>

          {/* Benchmarks Table */}
          <Card padding="none" className="bg-white dark:bg-[#0f0f1a] border-none rounded-[3rem] overflow-hidden mb-16 shadow-2xl">
              <header className="px-12 py-8 border-b border-black/5 dark:border-white/5 flex justify-between items-center text-black dark:text-white">
                  <h3 className="text-2xl font-black italic manga-font uppercase flex items-center gap-3">
                      <BarChart3 className="w-6 h-6 text-blue-500" /> Comparison Matrix
                  </h3>
                  <span className="text-[10px] font-bold opacity-30 uppercase tracking-widest">Last Update: {new Date().toLocaleDateString()}</span>
              </header>
              
              <div className="overflow-x-auto">
                  <table className="w-full text-left text-black dark:text-white">
                      <thead className="bg-gray-50 dark:bg-black/40">
                          <tr>
                              <th className="px-12 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40">Rank</th>
                              <th className="px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40">Model ID</th>
                              <th className="px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40 text-center">ELO Score</th>
                              <th className="px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40 text-center">MMLU</th>
                              <th className="px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40 text-center">Context</th>
                              <th className="px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] opacity-40 text-right">License</th>
                          </tr>
                      </thead>
                      <tbody className="divide-y divide-black/5 dark:divide-white/5">
                          {[...benchmarks].sort((a: ModelBenchmark, b: ModelBenchmark) => b.elo_score - a.elo_score).map((m: ModelBenchmark, i: number) => (
                              <tr key={m.model_id} className="group hover:bg-gray-50/50 dark:hover:bg-white/[0.02] transition-colors">
                                  <td className="px-12 py-6">

                                      <span className={`text-xl font-black italic manga-font ${i === 0 ? 'text-yellow-500' : 'opacity-20'}`}>
                                          #0{i + 1}
                                      </span>
                                  </td>
                                  <td className="px-8 py-6">
                                      <div className="flex flex-col">
                                          <span className="text-sm font-black italic uppercase tracking-wider group-hover:text-blue-500 transition-colors">{m.model_id}</span>
                                          <span className="text-[9px] font-bold opacity-30 uppercase tracking-widest">{m.provider}</span>
                                      </div>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                      <Badge variant="neutral" className="bg-black/5 dark:bg-white/5 border-none font-mono text-xs text-black dark:text-white">{m.elo_score}</Badge>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                      <span className="text-sm font-black italic text-emerald-500">{m.mmlu_score}%</span>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                      <span className="text-xs font-bold opacity-50 uppercase">{Math.floor(m.context_window / 1000)}k tokens</span>
                                  </td>
                                  <td className="px-8 py-6 text-right">
                                      <Badge variant="neutral" className={`border-none text-[8px] uppercase tracking-widest ${m.is_open_source ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                                          {m.is_open_source ? 'Open Weights' : 'Proprietary'}
                                      </Badge>
                                  </td>
                              </tr>
                          ))}
                      </tbody>
                  </table>
              </div>
          </Card>

          {/* Global Stats Footer */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-black dark:text-white">
              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-xl">
                  <Activity className="w-8 h-8 text-blue-500 mb-4" />
                  <h4 className="text-xs font-black uppercase tracking-widest mb-2">Domination Anthropic</h4>
                  <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Claude 3.5 Sonnet maintient un ratio de préférence utilisateur exceptionnel dans le domaine de la génération de code et du raisonnement complexe.</p>
              </Card>
              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-xl">
                  <Cpu className="w-8 h-8 text-purple-500 mb-4" />
                  <h4 className="text-xs font-black uppercase tracking-widest mb-2">Scaling Laws</h4>
                  <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Llama-3.1-405B redéfinit la limite supérieure des modèles Open Weights, égalant les performances des solutions propriétaires fermées.</p>
              </Card>
              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-xl">
                  <Sparkles className="w-8 h-8 text-yellow-500 mb-4" />
                  <h4 className="text-xs font-black uppercase tracking-widest mb-2">Animetix Multi-Model</h4>
                  <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Le backend Animetix route dynamiquement vos requêtes vers les modèles du Top 3 pour garantir une précision sémantique maximale.</p>
              </Card>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SOTABenchmarkPage;


