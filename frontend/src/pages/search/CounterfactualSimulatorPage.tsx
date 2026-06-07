import React, { useState } from 'react';
import { 
  Zap, 
  RefreshCw, 
  ArrowRight, 
  MessageCircle, 
  ShieldAlert, 
  TrendingUp, 
  AlertCircle,
  Clock,
  Sparkles,
  Search,
  Split
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const CounterfactualSimulatorPage: React.FC = () => {
  const [whatIf, setWhatIf] = useState('');
  const [actualContext, setActualContext] = useState<string>('L\'utilisateur a demandé qui est le plus fort entre Goku et Saitama.');
  const [result, setResult] = useState<any>(null);

  const simulateMutation = useMutation({
    mutationFn: async () => {
        return apiClient('/api/v1/cognition/counterfactual/', {
            method: 'POST',
            body: JSON.stringify({ 
                what_if: whatIf,
                actual_context: [{ role: 'user', content: actualContext }]
            }),
            headers: { 'Content-Type': 'application/json' }
        });
    },
    onSuccess: (data) => {
        setResult(data);
    }
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!whatIf.trim()) return;
    simulateMutation.mutate();
  };

  return (
    <AnimatedPage>
      <div className="max-w-6xl mx-auto px-6 py-12">
        
        {/* Header */}
        <header className="mb-12 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
               <Split className="w-4 h-4" /> Decisions & Regrets
            </div>
            <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-4 text-glow">
                COUNTERFACTUAL <span className="text-purple-500">SIMULATOR</span>
            </h1>
            <p className="text-lg font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                Explorez les timelines alternatives de vos interactions IA et mesurez le "Regret Cognitif".
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Input Column */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/5 shadow-2xl rounded-[2.5rem]">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2 text-purple-400">
                        <Clock className="w-4 h-4" /> Réalité Actuelle
                    </h3>
                    <div className="space-y-4">
                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 italic text-xs opacity-70 leading-relaxed">
                            "{actualContext}"
                        </div>
                        <p className="text-[10px] font-bold opacity-30 uppercase text-center italic">
                            Analyse de la timeline principale...
                        </p>
                    </div>
                </Card>

                <Card padding="lg" className="bg-black border-purple-500/20 rounded-[2.5rem]">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-400" /> What If Scenario
                    </h3>
                    <form onSubmit={onSubmit} className="space-y-6">
                        <textarea 
                            value={whatIf}
                            onChange={(e) => setWhatIf(e.target.value)}
                            placeholder="Et si j'avais demandé..."
                            className="w-full bg-white/5 border-2 border-white/5 rounded-2xl p-4 text-sm font-bold min-h-[120px] focus:border-purple-500 outline-none transition-all"
                        />
                        <Button 
                            type="submit" 
                            disabled={simulateMutation.isPending || !whatIf.trim()}
                            className="w-full bg-purple-600 hover:bg-purple-500 text-white py-6 rounded-2xl font-black italic uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {simulateMutation.isPending ? <RefreshCw className="w-5 h-5 animate-spin" /> : "BRANCHER LA TIMELINE"}
                        </Button>
                    </form>
                </Card>
            </div>

            {/* Results Column */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {result ? (
                        <motion.div 
                            key="result"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="space-y-8"
                        >
                            {/* Regret Badge & Score */}
                            <div className="flex justify-between items-center bg-white/5 p-8 rounded-[3rem] border border-white/10 shadow-2xl relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-12 opacity-[0.03]">
                                    <TrendingUp className="w-32 h-32" />
                                </div>
                                <div>
                                    <h3 className="text-xs font-black uppercase opacity-40 mb-2 tracking-widest">Calcul du Regret Contrefactuel</h3>
                                    <div className="flex items-end gap-3">
                                        <span className={`text-6xl font-black italic manga-font ${result.counterfactual_regret > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                                            {result.counterfactual_regret > 0 ? '+' : ''}{(result.counterfactual_regret * 100).toFixed(1)}%
                                        </span>
                                        <Badge variant={result.counterfactual_regret > 0 ? 'danger' : 'success'} className="mb-2">
                                            {result.counterfactual_regret > 0 ? 'TIMELINE OPTIMISÉE' : 'RÉALITÉ SUPÉRIEURE'}
                                        </Badge>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-[10px] font-black opacity-30 uppercase mb-4">Utilité Alternative</p>
                                    <div className="w-32 h-2 bg-white/5 rounded-full overflow-hidden">
                                        <motion.div 
                                            initial={{ width: 0 }}
                                            animate={{ width: `${result.alternative_utility * 100}%` }}
                                            className="h-full bg-purple-500"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Comparison View */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <Card padding="lg" className="bg-navy-900/40 border-white/5">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                                        <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Réalité Actuelle</span>
                                    </div>
                                    <p className="text-xs font-bold opacity-60 leading-relaxed italic">
                                        "Dans la timeline principale, le système a optimisé les résultats pour maximiser la fidélité sémantique (Fidelity: {(result.actual_utility * 100).toFixed(0)}%)."
                                    </p>
                                </Card>
                                <Card padding="lg" className="bg-purple-900/20 border-purple-500/20">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                                        <span className="text-[10px] font-black uppercase tracking-widest text-purple-400">Timeline Alternative</span>
                                    </div>
                                    <p className="text-xs font-bold text-purple-100/80 leading-relaxed italic">
                                        "{result.alternative_response}"
                                    </p>
                                </Card>
                            </div>

                            {/* Deep Analysis Card */}
                            <Card padding="lg" className="bg-black border-white/5 shadow-2xl relative overflow-hidden group">
                                <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-purple-500/5 blur-[100px] group-hover:bg-purple-500/10 transition-all rounded-full" />
                                <h3 className="text-xl font-black italic manga-font uppercase mb-6 flex items-center gap-3">
                                    <Search className="w-6 h-6 text-purple-500" /> Analyse de l'Inférence
                                </h3>
                                <p className="text-sm font-bold opacity-60 leading-relaxed mb-8">
                                    L'analyse contrefactuelle révèle que l'utilisation du prompt "<b>{result.what_if_query}</b>" {result.counterfactual_regret > 0 ? 'aurait permis d\'extraire plus de corrélations depuis le Knowledge Graph.' : 'est moins efficace que la stratégie de routage actuelle.'}
                                </p>
                                <div className="flex items-center gap-6">
                                    <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4">
                                        <Badge variant="primary" className="bg-purple-500">Z3 SOLVER</Badge>
                                        <span className="text-[9px] font-black uppercase tracking-widest opacity-40">Decision logic: Resolved</span>
                                    </div>
                                    <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4">
                                        <Badge variant="neutral" className="bg-blue-500/20 text-blue-400">RAG TRAJECTORY</Badge>
                                        <span className="text-[9px] font-black uppercase tracking-widest opacity-40">Path distance: 0.42</span>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-48 border-2 border-dashed border-white/5 rounded-[4rem]">
                            <Split className="w-24 h-24 mb-8" />
                            <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Timelines Non-Chargées</h3>
                            <p className="text-sm font-bold uppercase tracking-[0.3em]">Utilisez le panneau de gauche pour simuler un "What If".</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>

        {/* Global Warning / AI Status */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-purple-600/10 to-transparent border border-white/5 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic">
                Avertissement : Le simulateur utilise des modèles de raisonnement sémantique pour projeter des réalités virtuelles. <br />
                Le score de "Regret" est une mesure probabiliste de l'écart d'utilité entre deux trajectoires de dialogue.
            </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default CounterfactualSimulatorPage;


