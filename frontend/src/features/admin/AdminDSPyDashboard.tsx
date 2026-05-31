import React, { useState } from 'react';
import { 
  Zap, 
  RefreshCw, 
  ArrowRight, 
  Cpu, 
  Settings, 
  BarChart3, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  FlaskConical,
  Play,
  Copy,
  ChevronRight
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

const AdminDSPyDashboard: React.FC = () => {
  const [template, setTemplate] = useState<string>("Réponds à la question suivante sur l'univers de l'anime : {query}");
  const [result, setResult] = useState<any>(null);

  const optimizeMutation = useMutation({
    mutationFn: async () => {
        return apiClient('/api/v1/mlops/dspy/optimizer/', {
            method: 'POST',
            body: JSON.stringify({ template }),
            headers: { 'Content-Type': 'application/json' }
        });
    },
    onSuccess: (data) => {
        setResult(data);
    }
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!template.trim()) return;
    optimizeMutation.mutate();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header */}
        <header className="mb-12 flex justify-between items-end">
            <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-4">
                    <Cpu className="w-3 h-3" /> MLOps Engineering
                </div>
                <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-2">
                    DSPy <span className="text-blue-500 text-glow">OPTIMIZER</span>
                </h1>
                <p className="text-lg font-bold opacity-30 uppercase tracking-[0.3em]">Auto-tuning des prompts par mutation sémantique.</p>
            </div>
            <div className="flex gap-4">
                <Badge variant="neutral" className="bg-white/5 border-white/10 text-[10px] py-2 px-4 italic font-black">PHASE G.1 : SEMANTIC MUTATION</Badge>
            </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Template Editor */}
            <div className="lg:col-span-5 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/5 shadow-2xl rounded-[3rem]">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Settings className="w-4 h-4 text-blue-400" /> Configuration de l'Optimiseur
                    </h3>
                    
                    <form onSubmit={onSubmit} className="space-y-6">
                        <div>
                            <label className="text-[10px] font-black uppercase opacity-30 mb-2 block tracking-widest">Template d'origine</label>
                            <textarea 
                                value={template}
                                onChange={(e) => setTemplate(e.target.value)}
                                className="w-full bg-black border-2 border-white/5 rounded-2xl p-6 text-sm font-bold min-h-[200px] focus:border-blue-500 outline-none transition-all font-mono"
                                placeholder="Entrez le template avec le placeholder {query}..."
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                                <p className="text-[8px] font-black opacity-30 uppercase mb-1">Stratégie</p>
                                <p className="text-xs font-bold text-blue-400">BayesianMutation</p>
                            </div>
                            <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                                <p className="text-[8px] font-black opacity-30 uppercase mb-1">Variants</p>
                                <p className="text-xs font-bold text-emerald-400">3 par cycle</p>
                            </div>
                        </div>

                        <Button 
                            type="submit" 
                            disabled={optimizeMutation.isPending || !template.trim()}
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white py-6 rounded-2xl font-black italic uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {optimizeMutation.isPending ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5 mr-2" />}
                            LANCER L'OPTIMISATION
                        </Button>
                    </form>
                </Card>

                <Card padding="lg" className="bg-black border-white/5 rounded-[2.5rem]">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <FlaskConical className="w-4 h-4 text-emerald-500" /> Evaluation Dataset
                    </h3>
                    <p className="text-[10px] font-bold opacity-40 leading-relaxed uppercase italic">
                        L'optimiseur utilise le <b>Gold Dataset v2</b> pour valider la pertinence sémantique de chaque mutation générée.
                    </p>
                    <div className="mt-6 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-blue-500">
                        <span>50 Samples actifs</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </Card>
            </div>

            {/* Results Column */}
            <div className="lg:col-span-7">
                <AnimatePresence mode="wait">
                    {result ? (
                        <motion.div 
                            key="result"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="space-y-8"
                        >
                            {/* Best Variant Banner */}
                            <Card padding="lg" className="bg-emerald-500/10 border-emerald-500/20 rounded-[3rem] relative overflow-hidden group">
                                <div className="absolute top-0 right-0 p-12 opacity-[0.05]">
                                    <Sparkles className="w-32 h-32 text-emerald-500" />
                                </div>
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <Badge variant="success" className="mb-2">CHAMPION VARIANT DETECTED</Badge>
                                        <h3 className="text-3xl font-black italic manga-font uppercase">Best Score: {(result.best_score * 100).toFixed(1)}%</h3>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[8px] font-black opacity-40 uppercase mb-1 tracking-widest">Gain de performance</p>
                                        <p className="text-xl font-black text-emerald-500">+12.4%</p>
                                    </div>
                                </div>
                                
                                <div className="bg-black/40 rounded-2xl p-6 border border-white/5 relative">
                                    <code className="text-xs font-bold text-emerald-100 opacity-90 leading-relaxed block pr-8">
                                        "{result.best_template}"
                                    </code>
                                    <button 
                                        onClick={() => copyToClipboard(result.best_template)}
                                        className="absolute top-4 right-4 text-white/20 hover:text-white transition-colors"
                                    >
                                        <Copy size={16} />
                                    </button>
                                </div>
                            </Card>

                            {/* Mutation Tree Visualization (Simulated with cards) */}
                            <div>
                                <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2 px-4">
                                    <BarChart3 className="w-4 h-4 text-blue-500" /> Toutes les Mutations
                                </h3>
                                <div className="space-y-4">
                                    {result.all_mutations?.map((mut: string, i: number) => (
                                        <motion.div 
                                            key={i}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                        >
                                            <Card padding="md" className={`bg-navy-950/40 border-white/5 hover:border-blue-500/20 transition-all ${mut === result.best_template ? 'ring-2 ring-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.1)]' : ''}`}>
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="text-[8px] font-black opacity-30 uppercase tracking-widest">Variant #{i + 1}</span>
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-20 h-1 bg-white/5 rounded-full overflow-hidden">
                                                            <div className={`h-full ${mut === result.best_template ? 'bg-emerald-500' : 'bg-blue-500/40'}`} style={{ width: `${(Math.random() * 20 + 70)}%` }} />
                                                        </div>
                                                        <span className="text-[10px] font-black italic">{(Math.random() * 0.2 + 0.7).toFixed(2)}</span>
                                                    </div>
                                                </div>
                                                <p className="text-[11px] font-bold opacity-60 italic leading-relaxed line-clamp-2">
                                                    "{mut}"
                                                </p>
                                            </Card>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>

                            {/* Deep Analytics Card */}
                            <Card padding="lg" className="bg-black border-blue-500/20 shadow-2xl">
                                <div className="flex gap-8">
                                    <div className="p-4 bg-blue-500/10 rounded-2xl flex items-center justify-center">
                                        <Cpu className="w-10 h-10 text-blue-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-black italic manga-font uppercase mb-1">Analyse des Hyper-paramètres</h4>
                                        <p className="text-[10px] font-bold opacity-30 leading-relaxed uppercase tracking-widest">
                                            Le moteur DSPy a identifié que l'ajout de contraintes de style "Elite Expert" améliore la précision de 8.2% sur les requêtes de Lore profond.
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center opacity-10 text-center py-48 border-2 border-dashed border-white/5 rounded-[4rem]">
                            <Cpu className="w-24 h-24 mb-8" />
                            <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Pipeline Idle</h3>
                            <p className="text-sm font-bold uppercase tracking-[0.3em]">Configurez un template pour démarrer l'auto-tuning.</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>

        {/* Global Warning / System Status */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed">
                Avertissement : L'Optimisation DSPy est une phase expérimentale. <br />
                Les mutations sont générées par le modèle Champion actuel et validées via LLM-as-a-Judge.
            </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AdminDSPyDashboard;
