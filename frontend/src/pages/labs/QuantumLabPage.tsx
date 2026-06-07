import React, { useState } from 'react';
import { 
  Atom,
  Zap,
  Loader2,
  ChevronRight,
  ShieldCheck,
  Activity,
  Target
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

const QuantumLabPage: React.FC = () => {
  const [quantumTheme, setQuantumTheme] = useState('shonen');
  const [quantumResult, setQuantumResult] = useState<any | null>(null);

  const quantumMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
    }),
    onSuccess: (data) => setQuantumResult(data)
  });

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-purple-400 mb-4">
                <Atom className="w-3 h-3 animate-spin-slow" /> Quantum Preference Engine
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                QUANTUM <span className="text-purple-500 text-glow">COGNITION</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Modélisation des préférences utilisateur via superposition d'états et effondrement de fonction d'onde.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Configuration */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-6 opacity-10">
                        <Atom className="w-24 h-24 rotate-12" />
                    </div>
                    
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Target className="w-4 h-4 text-purple-500" /> Born's Measurement
                    </h3>

                    <div className="space-y-8">
                        <div className="space-y-4">
                            <label className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] px-2">Observable Thématique</label>
                            <select 
                                value={quantumTheme} 
                                onChange={(e) => setQuantumTheme(e.target.value)} 
                                className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-purple-500 transition-all"
                            >
                                <option value="shonen">SHONEN</option>
                                <option value="seinen">SEINEN</option>
                                <option value="ghibli">GHIBLI</option>
                                <option value="comedy">COMEDY</option>
                                <option value="cyberpunk">CYBERPUNK</option>
                            </select>
                        </div>

                        <Button 
                            onClick={() => quantumMutation.mutate({ action: 'quantum', theme: quantumTheme })} 
                            disabled={quantumMutation.isPending} 
                            className="w-full bg-purple-600 hover:bg-purple-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {quantumMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "EFFECTUER MESURE"}
                        </Button>
                    </div>
                </Card>

                <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-purple-400">Théorie de la Mesure</h4>
                    <p className="text-[10px] font-bold uppercase leading-relaxed mb-4">
                        L'IA traite vos goûts non comme des étiquettes fixes, mais comme des probabilités en superposition.
                    </p>
                    <ul className="space-y-3">
                        <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                            <div className="w-1 h-1 rounded-full bg-purple-500 mt-1" /> Intrication sémantique multi-genres.
                        </li>
                        <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                            <div className="w-1 h-1 rounded-full bg-purple-500 mt-1" /> Effondrement SAT instantané.
                        </li>
                    </ul>
                </Card>
            </div>

            {/* Visualisation */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {quantumResult ? (
                        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-12">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                <div className="space-y-8">
                                    <div className="p-12 bg-purple-500/5 rounded-[3.5rem] border border-purple-500/20 text-center relative overflow-hidden shadow-2xl">
                                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-50" />
                                        <h4 className="text-[10px] font-black uppercase opacity-40 mb-8 tracking-[0.2em]">Mesure de Probabilité</h4>
                                        <div className="text-[10rem] font-black italic text-purple-400 manga-font mb-4 leading-none">
                                            {Math.round(quantumResult.probability * 100)}%
                                        </div>
                                        <Badge className={`px-8 py-3 rounded-full font-black italic uppercase text-xs ${quantumResult.outcome ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'}`}>
                                            OUTCOME: {quantumResult.outcome ? 'COLLAPSED POSITIVE' : 'COLLAPSED NEGATIVE'}
                                        </Badge>
                                    </div>

                                    <Card padding="lg" className="bg-navy-900 border-white/5 relative">
                                        <h5 className="text-[10px] font-black uppercase opacity-30 mb-4 tracking-widest flex items-center gap-2">
                                            <Activity className="w-3 h-3" /> Interprétation de Born
                                        </h5>
                                        <p className="text-sm font-bold leading-relaxed opacity-60 italic text-purple-100/60">
                                            La mesure a forcé le système à sortir de sa superposition pour valider (ou rejeter) l'observable "{quantumTheme.toUpperCase()}". Les thèmes intriqués restent influencés par cet effondrement.
                                        </p>
                                    </Card>
                                </div>

                                <div className="space-y-6">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest flex items-center gap-2 opacity-40 mb-8">
                                        <Zap className="w-4 h-4 text-yellow-500" /> État du Vecteur de Conscience
                                    </h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        {quantumResult.state_vector.map((val: string, i: number) => (
                                            <div key={i} className="p-6 bg-black border border-white/5 rounded-2xl flex items-center justify-between group hover:border-purple-500/30 transition-all">
                                                <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">AMPLITUDE_{i}</span>
                                                <code className="text-sm font-mono text-purple-300 truncate max-w-[200px]">{val}</code>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-12 p-8 bg-purple-600/10 rounded-[2.5rem] border border-purple-500/20 text-center">
                                        <p className="text-xs font-black italic text-purple-400 uppercase tracking-widest">
                                            "L'incertitude est le socle de la créativité numérique."
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center py-32 opacity-10 text-center border-4 border-dashed border-white/5 rounded-[4rem]">
                            <Atom className="w-48 h-48 mb-12 animate-spin-slow" />
                            <h3 className="text-5xl font-black italic uppercase manga-font mb-4">Système en Superposition</h3>
                            <p className="text-lg font-bold uppercase tracking-[0.4em]">Prêt pour une mesure d'observable thématique.</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default QuantumLabPage;

