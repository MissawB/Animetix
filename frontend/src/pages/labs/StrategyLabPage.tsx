import React, { useState } from 'react';
import { 
  Target, 
  TrendingUp, 
  Activity, 
  BarChart3, 
  Zap, 
  Brain, 
  GitBranch,
  Search,
  Maximize2,
  RefreshCw,
  Layers,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

const StrategyLabPage: React.FC = () => {
  const [iterations, setIterations] = useState(100);
  const [result, setResult] = useState<any>(null);

  const mutation = useMutation({
    mutationFn: (data: { iterations: number }) => 
        apiClient('/api/v1/cognition/cfr-strategy-lab/', {
            method: 'POST',
            body: JSON.stringify(data)
        }),
    onSuccess: (data) => {
        setResult(data);
    }
  });

  const runSimulation = () => {
    mutation.mutate({ iterations });
  };

  const getChartData = () => {
    if (!result) return [];
    return result.history.map((step: any) => ({
      name: step.iteration,
      ...step.avg_strategy.reduce((acc: any, val: number, idx: number) => {
        acc[result.questions[idx]] = val;
        return acc;
      }, {})
    }));
  };

  const getRegretData = () => {
    if (!result) return [];
    return result.history.map((step: any) => ({
      name: step.iteration,
      ...step.regrets.reduce((acc: any, val: number, idx: number) => {
        acc[result.questions[idx]] = val;
        return acc;
      }, {})
    }));
  };

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header CFR */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -right-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-500 mb-4">
                <Target className="w-3 h-3" /> Game Theory Division
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                STRATEGY <span className="text-red-600 text-glow">LAB</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Visualisez la convergence de l'équilibre de Nash via la minimisation du regret contrefactuel (CFR).
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Control Panel */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <Brain className="w-32 h-32" />
                    </div>
                    
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-500" /> Paramètres du Solveur
                    </h3>
                    
                    <div className="space-y-8">
                        <div className="space-y-4">
                            <div className="flex justify-between">
                                <label className="text-[10px] font-black uppercase tracking-widest opacity-30">Itérations de Convergence</label>
                                <span className="text-sm font-black text-red-500">{iterations}</span>
                            </div>
                            <input 
                                type="range" 
                                min="50" 
                                max="500" 
                                step="50"
                                value={iterations}
                                onChange={(e) => setIterations(parseInt(e.target.value))}
                                className="w-full accent-red-600 bg-white/5 h-1 rounded-full appearance-none"
                            />
                        </div>

                        <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                            <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 opacity-30">Algorithme</h4>
                            <div className="flex items-center gap-3">
                                <Badge variant="neutral" className="bg-red-500/10 text-red-500 border-none text-[8px] uppercase">CFR+</Badge>
                                <Badge variant="neutral" className="bg-blue-500/10 text-blue-500 border-none text-[8px] uppercase">Regret Matching</Badge>
                            </div>
                        </div>

                        <Button 
                            onClick={runSimulation}
                            disabled={mutation.isPending}
                            className="w-full bg-red-600 hover:bg-red-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {mutation.isPending ? <RefreshCw className="w-6 h-6 animate-spin" /> : "LANCER LA RÉSOLUTION"}
                        </Button>
                    </div>
                </Card>

                {/* Info Card */}
                <Card padding="lg" className="bg-white/5 border-white/5 rounded-[2rem]">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 opacity-30">Qu'est-ce que le CFR ?</h4>
                    <p className="text-[11px] font-bold leading-relaxed opacity-40 uppercase italic">
                        Le "Counterfactual Regret Minimization" est l'algorithme utilisé pour résoudre les jeux à information incomplète. 
                        Il permet à l'IA d'apprendre de ses erreurs passées en calculant le "regret" de ne pas avoir posé une meilleure question.
                    </p>
                </Card>
            </div>

            {/* Visualization Section */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {!result && !mutation.isPending && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="h-full min-h-[600px] border-2 border-dashed border-white/5 rounded-[3rem] flex flex-col items-center justify-center text-center p-12"
                        >
                            <Target className="w-16 h-16 text-white/5 mb-6" />
                            <h3 className="text-2xl font-black italic manga-font uppercase opacity-10">En attente de simulation</h3>
                            <p className="text-sm font-bold opacity-10 uppercase tracking-widest max-w-xs mt-2">
                                Appuyez sur le bouton pour observer comment l'IA optimise son arbre de décision.
                            </p>
                        </motion.div>
                    )}

                    {mutation.isPending && (
                        <div className="h-full min-h-[600px] flex flex-col items-center justify-center space-y-8">
                             <div className="relative">
                                <div className="w-32 h-32 border-4 border-red-500/20 border-t-red-500 rounded-full animate-spin"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <Brain className="w-12 h-12 text-red-500 animate-pulse" />
                                </div>
                            </div>
                            <p className="text-sm font-black uppercase tracking-[0.4em] text-red-500 animate-pulse">Minimizing Regret...</p>
                        </div>
                    )}

                    {result && (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-12"
                        >
                            {/* Strategy Convergence Chart */}
                            <section>
                                <div className="flex items-center justify-between mb-8">
                                    <h2 className="text-2xl font-black italic manga-font uppercase tracking-tighter">Convergence de <span className="text-red-500">Nash</span></h2>
                                    <Badge variant="neutral" className="bg-white/5 border-none text-[8px] uppercase tracking-widest">PROBABILITÉ D'ACTION</Badge>
                                </div>
                                <Card padding="lg" className="bg-black border-white/5 h-[400px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={getChartData()}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                            <XAxis dataKey="name" stroke="#ffffff30" fontSize={10} label={{ value: 'Itérations', position: 'insideBottom', offset: -5, fill: '#ffffff30' }} />
                                            <YAxis stroke="#ffffff30" fontSize={10} domain={[0, 1]} />
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: '#0a0a12', border: '1px solid #ffffff10', borderRadius: '12px' }}
                                                itemStyle={{ fontSize: '10px', fontWeight: 'bold', textTransform: 'uppercase' }}
                                            />
                                            <Legend wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', paddingTop: '20px' }} />
                                            {result.questions.map((q: string, i: number) => (
                                                <Line 
                                                    key={q} 
                                                    type="monotone" 
                                                    dataKey={q} 
                                                    stroke={colors[i % colors.length]} 
                                                    strokeWidth={3}
                                                    dot={false}
                                                    animationDuration={1500}
                                                />
                                            ))}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </Card>
                            </section>

                            {/* Regret Chart */}
                            <section>
                                <div className="flex items-center justify-between mb-8">
                                    <h2 className="text-2xl font-black italic manga-font uppercase tracking-tighter text-blue-500">Regret <span className="text-white/20">Matching</span></h2>
                                    <Badge variant="neutral" className="bg-blue-500/10 text-blue-500 border-none text-[8px] uppercase tracking-widest">ÉVOLUTION DU REGRET</Badge>
                                </div>
                                <Card padding="lg" className="bg-black border-white/5 h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={getRegretData()}>
                                            <defs>
                                                {result.questions.map((q: string, i: number) => (
                                                    <linearGradient key={`grad-${i}`} id={`color-${i}`} x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor={colors[i % colors.length]} stopOpacity={0.3}/>
                                                        <stop offset="95%" stopColor={colors[i % colors.length]} stopOpacity={0}/>
                                                    </linearGradient>
                                                ))}
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                            <XAxis dataKey="name" hide />
                                            <YAxis stroke="#ffffff30" fontSize={10} />
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: '#0a0a12', border: '1px solid #ffffff10', borderRadius: '12px' }}
                                            />
                                            {result.questions.map((q: string, i: number) => (
                                                <Area 
                                                    key={q} 
                                                    type="monotone" 
                                                    dataKey={q} 
                                                    stroke={colors[i % colors.length]} 
                                                    fillOpacity={1} 
                                                    fill={`url(#color-${i})`} 
                                                />
                                            ))}
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </Card>
                            </section>

                            {/* Decision Results */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <Card padding="lg" className="bg-white/5 border-white/5 rounded-[2rem]">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-6 opacity-30 flex items-center gap-2">
                                        <GitBranch className="w-4 h-4" /> Meilleur Chemin Décidé
                                    </h4>
                                    <div className="space-y-4">
                                        {result.questions.map((q: string, i: number) => (
                                            <div key={i} className="flex items-center justify-between p-4 bg-black/40 rounded-2xl border border-white/5">
                                                <span className="text-xs font-bold uppercase truncate max-w-[200px]">{q}</span>
                                                <span className="text-xs font-black italic text-red-500">{(result.final_strategy[i] * 100).toFixed(1)}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </Card>

                                <Card padding="lg" className="bg-red-600 text-white border-none shadow-2xl rounded-[2rem] flex flex-col justify-center items-center text-center">
                                    <ShieldCheck className="w-12 h-12 mb-4" />
                                    <p className="text-[10px] font-black uppercase tracking-[0.3em] mb-2 opacity-60">Solution Optimale</p>
                                    <h3 className="text-2xl font-black italic manga-font uppercase mb-4 leading-tight">
                                        {result.questions[result.final_strategy.indexOf(Math.max(...result.final_strategy))]}
                                    </h3>
                                    <div className="text-[10px] font-bold uppercase tracking-widest opacity-40">
                                        Confiance: {(Math.max(...result.final_strategy) * 100).toFixed(2)}%
                                    </div>
                                </Card>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default StrategyLabPage;
