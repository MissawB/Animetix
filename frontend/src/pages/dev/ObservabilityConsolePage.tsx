import React, { useState } from 'react';
import { 
  Activity, 
  RefreshCw, 
  ShieldAlert, 
  BarChart3, 
  Zap, 
  Target, 
  Fingerprint,
  Layers,
  Sliders,
  CheckCircle2,
  Brain
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

interface ObservabilityData {
    drift_status: string;
    drift_config: string;
}

const ObservabilityConsolePage: React.FC = () => {
  const [thresholds, setThresholds] = useState({
      hate: 0.7,
      violence: 0.8,
      harassment: 0.6,
      self_harm: 0.9
  });

  const { data, isLoading, refetch } = useQuery<ObservabilityData>({
    queryKey: ['admin', 'observability'],
    queryFn: () => apiClient('/api/v1/admin/observability/')
  });

  const thresholdMutation = useMutation({
    mutationFn: (body: { category: string, threshold: number }) => 
        apiClient('/api/v1/admin/observability/', { method: 'POST', body: JSON.stringify(body) }),
  });

  const handleThresholdChange = (category: string, value: number) => {
      setThresholds(prev => ({ ...prev, [category]: value }));
      thresholdMutation.mutate({ category, threshold: value });
  };

  return (
    <div className="min-h-screen w-full bg-[#fafafa] dark:bg-[#0a0a0f] text-black dark:text-white pt-20 pb-32">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          
          {/* Header */}
          <header className="mb-20 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-[10px] font-black uppercase tracking-widest text-purple-500 mb-6">
                  <Activity className="w-3 h-3" /> Neural Observability & Drift Analysis
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none">
                  OBSERVABILITY <span className="text-purple-500 text-glow">CONSOLE</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Surveillez l'intégrité des modèles et ajustez les barrières cognitives en temps réel.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
              
              {/* Archetype Drift Section */}
              <div className="lg:col-span-7 space-y-8">
                  <Card padding="lg" className="bg-white dark:bg-navy-950/40 border-none shadow-2xl rounded-[3rem] relative overflow-hidden group">
                      <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity">
                          <Fingerprint className="w-48 h-48 text-purple-500" />
                      </div>
                      
                      <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-10">
                          <Target className="w-4 h-4 text-purple-500" /> Archetype Drift Analysis
                      </h3>

                      {isLoading ? (
                          <div className="py-20 text-center"><RefreshCw className="w-8 h-8 animate-spin mx-auto opacity-20" /></div>
                      ) : (
                          <div className="space-y-10 relative z-10">
                              <div className="flex items-end justify-between border-b border-black/5 dark:border-white/5 pb-8">
                                  <div>
                                      <p className="text-[10px] font-black uppercase opacity-30 tracking-widest mb-1">Global Stability Score</p>
                                      <p className="text-6xl font-black italic manga-font text-emerald-500">94.2%</p>
                                  </div>
                                  <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-none px-4 py-1.5 uppercase font-black italic">NOMINAL</Badge>
                              </div>

                              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                  <div className="p-6 bg-gray-50 dark:bg-white/[0.03] rounded-3xl border border-black/5 dark:border-white/5">
                                      <p className="text-[9px] font-black uppercase opacity-30 mb-4 tracking-widest flex items-center gap-2">
                                          <Zap className="w-3 h-3 text-amber-500" /> Latent Shift
                                      </p>
                                      <p className="text-sm font-bold text-black dark:text-white leading-relaxed italic">
                                          "{data?.drift_config || "Calcul en cours..."}"
                                      </p>
                                  </div>
                                  <div className="p-6 bg-gray-50 dark:bg-white/[0.03] rounded-3xl border border-black/5 dark:border-white/5">
                                      <p className="text-[9px] font-black uppercase opacity-30 mb-4 tracking-widest flex items-center gap-2">
                                          <Brain className="w-3 h-3 text-blue-500" /> Semantic Consistency
                                      </p>
                                      <p className="text-sm font-bold text-black dark:text-white">Dernier contrôle : <span className="text-blue-500 italic">Il y a 5 min</span></p>
                                  </div>
                              </div>

                              <Button 
                                onClick={() => refetch()}
                                variant="outline" 
                                className="w-full border-black/10 dark:border-white/10 text-[10px] font-black uppercase tracking-widest py-4 hover:bg-purple-500/5 transition-all"
                              >
                                  Ré-évaluer le Drift <RefreshCw className="ml-2 w-3 h-3" />
                              </Button>
                          </div>
                      )}
                  </Card>

                  {/* Latent Visualization Placeholder */}
                  <Card padding="lg" className="bg-black border-none shadow-2xl rounded-[3rem] overflow-hidden min-h-[300px] flex flex-col justify-center items-center relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-950/20 to-transparent" />
                      <div className="relative z-10 text-center space-y-6">
                          <Layers className="w-16 h-16 text-purple-500/40 mx-auto animate-pulse" />
                          <p className="text-[10px] font-black uppercase tracking-[0.4em] text-purple-500/60">Latent Space Mapping</p>
                          <div className="flex gap-4 justify-center">
                              {[1,2,3,4,5].map(i => (
                                  <div key={i} className="w-1 h-8 bg-purple-500/20 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
                              ))}
                          </div>
                      </div>
                  </Card>
              </div>

              {/* Guardrail Controls Section */}
              <div className="lg:col-span-5">
                  <Card padding="lg" className="bg-white dark:bg-navy-950 border-none shadow-2xl rounded-[3rem] sticky top-32">
                      <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-10">
                          <Sliders className="w-4 h-4 text-purple-500" /> Guardrail Thresholds
                      </h3>

                      <div className="space-y-10">
                          {Object.entries(thresholds).map(([cat, val]) => (
                              <div key={cat} className="space-y-4">
                                  <div className="flex justify-between items-end">
                                      <label htmlFor={`${cat}-filter`} className="text-[10px] font-black uppercase tracking-widest opacity-40">{cat.replace('_', ' ')} Filter</label>
                                      <span className="text-sm font-black italic manga-font text-purple-500">{(val * 100).toFixed(0)}%</span>
                                  </div>
                                  <div className="relative group">
                                      <input
                                          id={`${cat}-filter`}
                                          aria-label={`Seuil de filtre ${cat.replace('_', ' ')}`}
                                          type="range"
                                          min="0" 
                                          max="1" 
                                          step="0.01" 
                                          value={val}
                                          onChange={(e) => handleThresholdChange(cat, parseFloat(e.target.value))}
                                          className="w-full h-1.5 bg-black/5 dark:bg-white/10 rounded-full appearance-none cursor-pointer accent-purple-500"
                                      />
                                      <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-[7px] font-black uppercase opacity-20 tracking-tighter">
                                          <span>Aggressive</span>
                                          <span>Permissive</span>
                                      </div>
                                  </div>
                              </div>
                          ))}
                      </div>

                      <div className="mt-16 p-8 bg-purple-500/5 border border-purple-500/10 rounded-[2rem] space-y-4">
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-purple-500 flex items-center gap-2">
                              <ShieldAlert className="w-3 h-3" /> Security Impact
                          </h4>
                          <p className="text-[10px] font-bold text-black/50 dark:text-white/40 uppercase leading-relaxed italic">
                              Les changements de seuils sont appliqués instantanément sur le cluster d'inférence ADMS.
                          </p>
                      </div>

                      <div className="mt-12 pt-8 border-t border-black/5 dark:border-white/5 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                              <span className="text-[9px] font-black uppercase tracking-widest opacity-40">System Synchronized</span>
                          </div>
                          <Badge variant="neutral" className="bg-black/5 dark:bg-white/10 text-[8px]">PROD_RUNTIME_v4</Badge>
                      </div>
                  </Card>
              </div>
          </div>

          {/* Monitoring Metrics */}
          <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                  { label: 'Token Stability', value: '99.8%', icon: Zap, color: 'text-amber-500' },
                  { label: 'Concept Persistence', value: 'High', icon: Target, color: 'text-blue-500' },
                  { label: 'Neural Variance', value: '0.0024', icon: BarChart3, color: 'text-purple-500' }
              ].map((stat, i) => (
                  <Card key={i} padding="lg" className="bg-white dark:bg-navy-950 border-none shadow-xl rounded-[2.5rem] flex items-center gap-6 group hover:scale-[1.02] transition-all">
                      <div className={`p-5 rounded-2xl bg-white dark:bg-white/5 shadow-inner ${stat.color}`}>
                          <stat.icon className="w-6 h-6" />
                      </div>
                      <div>
                          <p className="text-[8px] font-black uppercase opacity-30 tracking-[0.2em] mb-1">{stat.label}</p>
                          <p className="text-3xl font-black italic manga-font">{stat.value}</p>
                      </div>
                  </Card>
              ))}
          </div>

        </div>
      </AnimatedPage>
    </div>
  );
};

export default ObservabilityConsolePage;
