import React, { useState } from 'react';
import { 
  Target,
  Zap, 
  Brain, 
  GitBranch,
  RefreshCw,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import _Plot from 'react-plotly.js';
import type * as Plotly from 'plotly.js';


interface PlotProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  style?: React.CSSProperties;
}

const Plot = (_Plot as unknown as { default: React.ComponentType<PlotProps> }).default
  || (_Plot as unknown as React.ComponentType<PlotProps>);

interface CFRResult {
    history: Array<{
        iteration: number;
        avg_strategy: number[];
        regrets: number[];
    }>;
    questions: string[];
    final_strategy: number[];
}

const StrategyLabPage: React.FC = () => {
  const [iterations, setIterations] = useState(100);
  const [result, setResult] = useState<CFRResult | null>(null);

  const mutation = useMutation<CFRResult, Error, { iterations: number }>({
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

  const getStrategyPlotData = () => {
      if (!result) return [];
      const traces: Array<Partial<Plotly.Data>> = [];
      const iterationsArr = result.history.map((step) => step.iteration);

      result.questions.forEach((q: string, idx: number) => {
          traces.push({
              x: iterationsArr,
              y: result.history.map((step) => step.avg_strategy[idx]),
              name: q,
              type: 'scatter',
              mode: 'lines',
              line: { width: 3 }
          } as unknown as Partial<Plotly.Data>);
      });
      return traces;
  };

  const getRegretPlotData = () => {
      if (!result) return [];
      const traces: Array<Partial<Plotly.Data>> = [];
      const iterationsArr = result.history.map((step) => step.iteration);

      result.questions.forEach((q: string, idx: number) => {
          traces.push({
              x: iterationsArr,
              y: result.history.map((step) => step.regrets[idx]),
              name: q,
              type: 'scatter',
              mode: 'lines',
              fill: 'tozeroy'
          } as unknown as Partial<Plotly.Data>);
      });
      return traces;
  };

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
                                <label htmlFor="iter-slider" className="text-[10px] font-black uppercase tracking-widest opacity-30">Itérations de Convergence</label>
                                <span className="text-sm font-black text-red-500">{iterations}</span>
                            </div>
                            <input
                                id="iter-slider"
                                aria-label="Itérations de convergence"
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
                                <Card padding="lg" className="bg-black border-white/5 min-h-[400px]">
                                    <Plot
                                        data={getStrategyPlotData() as Plotly.Data[]}
                                        layout={{
                                            autosize: true,
                                            height: 400,
                                            paper_bgcolor: 'rgba(0,0,0,0)',
                                            plot_bgcolor: 'rgba(0,0,0,0)',
                                            margin: { l: 40, r: 20, b: 40, t: 10 },
                                            showlegend: true,
                                            legend: { font: { color: '#64748b', size: 10 }, orientation: 'h', y: -0.2 },
                                            xaxis: {
                                                title: 'Itérations',
                                                gridcolor: 'rgba(255,255,255,0.05)',
                                                tickfont: { color: '#475569', size: 10 },
                                            },
                                            yaxis: {
                                                title: 'Probabilité',
                                                gridcolor: 'rgba(255,255,255,0.05)',
                                                tickfont: { color: '#475569', size: 10 },
                                                range: [0, 1]
                                            }
                                        }}
                                        config={{ responsive: true, displayModeBar: false }}
                                        style={{ width: '100%', height: '100%' }}
                                    />
                                </Card>
                            </section>

                            {/* Regret Chart */}
                            <section>
                                <div className="flex items-center justify-between mb-8">
                                    <h2 className="text-2xl font-black italic manga-font uppercase tracking-tighter text-blue-500">Regret <span className="text-white/20">Matching</span></h2>
                                    <Badge variant="neutral" className="bg-blue-500/10 text-blue-500 border-none text-[8px] uppercase tracking-widest">ÉVOLUTION DU REGRET</Badge>
                                </div>
                                <Card padding="lg" className="bg-black border-white/5 min-h-[300px]">
                                    <Plot
                                        data={getRegretPlotData() as Plotly.Data[]}
                                        layout={{
                                            autosize: true,
                                            height: 300,
                                            paper_bgcolor: 'rgba(0,0,0,0)',
                                            plot_bgcolor: 'rgba(0,0,0,0)',
                                            margin: { l: 40, r: 20, b: 40, t: 10 },
                                            showlegend: false,
                                            xaxis: {
                                                title: 'Itérations',
                                                gridcolor: 'rgba(255,255,255,0.05)',
                                                tickfont: { color: '#475569', size: 10 },
                                            },
                                            yaxis: {
                                                title: 'Regret',
                                                gridcolor: 'rgba(255,255,255,0.05)',
                                                tickfont: { color: '#475569', size: 10 },
                                            }
                                        }}
                                        config={{ responsive: true, displayModeBar: false }}
                                        style={{ width: '100%', height: '100%' }}
                                    />
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

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-white dark:bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Target className="w-64 h-64 text-red-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-red-600 dark:text-red-400" /> Guide du Stratège
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-red-600 dark:text-red-400">Le Principe :</span> L'IA cherche la meilleure question à poser dans un jeu de devinettes. Réglez le nombre d'itérations avec le curseur, puis lancez la résolution.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-red-600 dark:text-red-400">Le Regret :</span> À chaque itération, l'algorithme mesure le "regret" de ne pas avoir choisi une autre option, puis ajuste sa stratégie pour le réduire.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-red-600 dark:text-red-400">La Convergence :</span> Quand les courbes se stabilisent, la stratégie n'évolue plus : l'IA a trouvé le meilleur dosage de probabilités entre les questions possibles.
                    </p>
                </div>
            </Card>

            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
                <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-red-800/70 dark:text-red-200/60">
                    Simulation de Counterfactual Regret Minimization (CFR+ avec regret matching) exécutée côté serveur : la stratégie moyenne converge vers un équilibre de Nash approché. <br />
                    Les graphiques tracent la probabilité de chaque action et l'évolution du regret au fil des itérations — une visualisation pédagogique de théorie des jeux.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default StrategyLabPage;