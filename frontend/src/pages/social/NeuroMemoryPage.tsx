import React from 'react';
import { 
  Brain, 
  ShieldCheck, 
  Trash2, 
  Activity, 
  Zap, 
  RefreshCw, 
  Layers, 
  Lock,
  ChevronRight,
  Fingerprint,
  Target,
  Scale,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const NeuroMemoryPage: React.FC = () => {
  const { data, isLoading, refetch } = useQuery<any>({
    queryKey: ['neuro-memory'],
    queryFn: () => apiClient('/api/v1/cognition/neuro-memory/'),
  });

  const resetMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/cognition/neuro-memory/', {
        method: 'POST',
        body: JSON.stringify({ action: 'reset' })
    }),
    onSuccess: () => refetch()
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-32 flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_20px_rgba(99,102,241,0.5)]"></div>
        <p className="text-sm font-black uppercase tracking-[0.3em] animate-pulse opacity-40">Accessing Neural Engrams...</p>
    </div>
  );

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-4">
                <Fingerprint className="w-3 h-3" /> Cognitive Privacy Protocol
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                NEURO <span className="text-indigo-500 text-glow">MEMORY</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Gérez les règles logiques déduites par l'IA et contrôlez votre empreinte cognitive.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Logic Profile Summary */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-indigo-600 text-white border-none shadow-2xl relative overflow-hidden">
                    <div className="absolute -right-8 -top-8 opacity-20 rotate-12">
                        <Brain className="w-48 h-48" />
                    </div>
                    <h3 className="text-2xl font-black italic manga-font uppercase mb-6 flex items-center gap-3">
                        <ShieldCheck className="w-8 h-8" /> Trust Center
                    </h3>
                    <p className="text-sm font-bold opacity-90 leading-relaxed uppercase mb-8 relative z-10">
                        Vous avez un contrôle total sur ce que le solveur Z3 déduit de vos interactions. Vous pouvez réinitialiser votre profil logique à tout moment.
                    </p>
                    <div className="bg-black/20 rounded-2xl p-6 mb-8 relative z-10">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Neural Signals</span>
                            <span className="text-xl font-black italic manga-font">{data.total_signals}</span>
                        </div>
                        <div className="w-full h-1.5 bg-black/20 rounded-full overflow-hidden">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: '75%' }}
                                className="h-full bg-white" 
                            />
                        </div>
                    </div>
                    <Button 
                        onClick={() => resetMutation.mutate()}
                        disabled={resetMutation.isPending}
                        fullWidth
                        className="bg-black text-white hover:bg-navy-950 py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                    >
                        {resetMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "RESET LOGIC PROFILE"}
                    </Button>
                </Card>

                <Card padding="lg" className="bg-navy-950 border-white/5 opacity-50">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4">Système de Déduction</h4>
                    <ul className="space-y-4">
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Target className="w-4 h-4 text-indigo-500 shrink-0" /> Formal Solver: Z3 Theorem Prover.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Scale className="w-4 h-4 text-indigo-500 shrink-0" /> Contraintes: Logique SAT binaire.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Lock className="w-4 h-4 text-indigo-500 shrink-0" /> Confidentialité: Local-first Inference.
                        </li>
                    </ul>
                </Card>
            </div>

            {/* Deduced Rules List */}
            <div className="lg:col-span-8">
                <Card padding="none" className="bg-navy-900/40 border-white/10 rounded-[3rem] overflow-hidden shadow-2xl">
                    <header className="px-12 py-8 border-b border-white/5 flex justify-between items-center">
                        <h3 className="text-2xl font-black italic manga-font uppercase flex items-center gap-3">
                            <Layers className="w-6 h-6 text-indigo-500" /> Neural Engrams
                        </h3>
                        <Badge variant="neutral" className="bg-indigo-500/10 text-indigo-500 border-none uppercase font-black italic">ACTIVE RULES</Badge>
                    </header>
                    
                    <div className="p-8">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {data.deduced_rules && data.deduced_rules.length > 0 ? (
                                data.deduced_rules.map((item: any) => (
                                    <div key={item.id} className="group p-6 bg-black/40 rounded-[2rem] border border-white/5 hover:border-indigo-500/30 transition-all flex flex-col justify-between">
                                        <div>
                                            <div className="flex justify-between items-start mb-4">
                                                <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-500">
                                                    <Zap className="w-5 h-5 fill-current" />
                                                </div>
                                                <Badge variant="neutral" className="bg-white/5 border-none text-[8px] uppercase">{item.source}</Badge>
                                            </div>
                                            <h4 className="text-lg font-black italic manga-font uppercase text-white mb-2 tracking-tighter">
                                                {item.rule.replace(' == ', ': ')}
                                            </h4>
                                            <p className="text-[9px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
                                                Déduté via analyse sémantique des feedbacks récents.
                                            </p>
                                        </div>
                                        <div className="mt-8 pt-6 border-t border-white/5 flex justify-between items-center">
                                            <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Confidence: {item.confidence * 100}%</span>
                                            <button className="text-red-500/40 hover:text-red-500 transition-colors">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full py-24 text-center">
                                    <Activity className="w-20 h-20 text-indigo-500 mx-auto mb-6 opacity-10 animate-pulse" />
                                    <h4 className="text-2xl font-black italic manga-font uppercase opacity-20">Insufficient data for deduction</h4>
                                </div>
                            )}
                        </div>
                    </div>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default NeuroMemoryPage;


