import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Cpu, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  Database,
  Network,
  Zap,
  HelpCircle,
  MessageSquare,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

const CoveOraclePage: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [mediaType, setMediaType] = useState('anime');
  const [trace, setTrace] = useState<any>(null);

  const mutation = useMutation({
    mutationFn: (data: { question: string; media_type: string }) => 
        apiClient('/api/v1/cognition/cove-oracle/', {
            method: 'POST',
            body: JSON.stringify(data)
        }),
    onSuccess: (data) => {
        setTrace(data);
    }
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
        mutation.mutate({ question, media_type: mediaType });
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header CoVe */}
        <header className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
               <ShieldCheck className="w-4 h-4 fill-current" /> Oracle Verification Protocol v3.1
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                COVE <span className="text-blue-500 text-glow">ORACLE</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-3xl mx-auto leading-relaxed">
                Réduisez les hallucinations de l'IA via le protocole Chain-of-Verification raccordé au Knowledge Graph.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Input Section */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <Cpu className="w-32 h-32" />
                    </div>
                    
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-500" /> Requête d'Analyse
                    </h3>
                    
                    <form onSubmit={onSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest opacity-30 ml-4">Question sur le Lore</label>
                            <textarea 
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                rows={4}
                                placeholder="ex: Qui a tué le père de Ryuko Matoi dans Kill la Kill ?"
                                className="w-full bg-black border-2 border-white/5 rounded-2xl py-4 px-6 text-sm font-bold focus:border-blue-600 outline-none transition-all placeholder:opacity-20 resize-none"
                            />
                        </div>
                        
                        <div className="flex gap-4">
                            {['anime', 'manga', 'game'].map((type) => (
                                <button
                                    key={type}
                                    type="button"
                                    onClick={() => setMediaType(type)}
                                    className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border-2 ${
                                        mediaType === type 
                                        ? 'bg-blue-600 border-blue-600 text-white' 
                                        : 'bg-white/5 border-white/10 text-white/40 hover:border-white/20'
                                    }`}
                                >
                                    {type}
                                </button>
                            ))}
                        </div>

                        <Button 
                            type="submit" 
                            disabled={mutation.isPending || !question.trim()}
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {mutation.isPending ? <Zap className="w-6 h-6 animate-spin" /> : "VÉRIFIER LES FAITS"}
                        </Button>
                    </form>
                </Card>

                {/* Status Card */}
                <Card padding="lg" className="bg-white/5 border-white/5 rounded-[2rem]">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] font-black uppercase tracking-widest opacity-30">Vérification Pipeline</span>
                        <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-none">ACTIVE</Badge>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 opacity-30">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span className="text-[9px] font-bold uppercase">Multi-claims Decomposition</span>
                        </div>
                        <div className="flex items-center gap-3 opacity-30">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span className="text-[9px] font-bold uppercase">Neo4j Cross-Reference</span>
                        </div>
                        <div className="flex items-center gap-3 opacity-30">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span className="text-[9px] font-bold uppercase">Revised Consensus</span>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Trace Visualization Section */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {!trace && !mutation.isPending && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="h-full min-h-[500px] border-2 border-dashed border-white/5 rounded-[3rem] flex flex-col items-center justify-center text-center p-12"
                        >
                            <HelpCircle className="w-16 h-16 text-white/5 mb-6" />
                            <h3 className="text-2xl font-black italic manga-font uppercase opacity-10">En attente d'une question</h3>
                            <p className="text-sm font-bold opacity-10 uppercase tracking-widest max-w-xs mt-2">
                                Soumettez une requête pour lancer le moteur CoVe et visualiser le graphe de vérification.
                            </p>
                        </motion.div>
                    )}

                    {mutation.isPending && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-12"
                        >
                            <div className="flex flex-col items-center justify-center py-20">
                                <div className="relative">
                                    <div className="w-24 h-24 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <ShieldCheck className="w-8 h-8 text-blue-500 animate-pulse" />
                                    </div>
                                </div>
                                <p className="mt-8 text-sm font-black uppercase tracking-[0.4em] text-blue-500 animate-pulse">Processing Chain-of-Verification...</p>
                            </div>
                        </motion.div>
                    )}

                    {trace && (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-12"
                        >
                            {/* Step 1: Baseline */}
                            <section>
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="w-8 h-8 rounded-lg bg-gray-500/10 flex items-center justify-center text-gray-500 text-xs font-black italic">01</div>
                                    <h2 className="text-xl font-black italic manga-font uppercase tracking-tighter">Réponse Baseline <span className="text-gray-500 opacity-50">(Potentiellement instable)</span></h2>
                                </div>
                                <Card padding="lg" className="bg-white/5 border-white/10 rounded-2xl italic text-white/60 leading-relaxed border-l-4 border-l-gray-500">
                                    {trace.baseline}
                                </Card>
                            </section>

                            {/* Step 2: Verification Plan */}
                            <section>
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="w-8 h-8 rounded-lg bg-yellow-500/10 flex items-center justify-center text-yellow-500 text-xs font-black italic">02</div>
                                    <h2 className="text-xl font-black italic manga-font uppercase tracking-tighter text-yellow-500">Plan de Vérification <span className="text-white/20">Decomposition</span></h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {trace.verification_plan.map((q: string, i: number) => (
                                        <div key={i} className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 flex gap-4 items-start">
                                            <Search className="w-4 h-4 text-yellow-500 shrink-0 mt-1" />
                                            <p className="text-[11px] font-bold uppercase tracking-wide leading-normal">{q}</p>
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* Step 3: Verifications */}
                            <section>
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500 text-xs font-black italic">03</div>
                                    <h2 className="text-xl font-black italic manga-font uppercase tracking-tighter text-emerald-500">Validation Graphe <span className="text-white/20">Neo4j Cross-Ref</span></h2>
                                </div>
                                <div className="space-y-4">
                                    {trace.verifications.map((v: any, i: number) => (
                                        <Card key={i} padding="none" className="bg-black border-white/5 overflow-hidden">
                                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <Network className="w-4 h-4 text-blue-400" />
                                                    <span className="text-[10px] font-black uppercase tracking-widest text-white/40">{v.query}</span>
                                                </div>
                                                {v.context_found && <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-none text-[8px]">CONTEXT FOUND</Badge>}
                                            </div>
                                            <div className="p-6 text-sm font-bold leading-relaxed text-emerald-400/80">
                                                <div className="flex gap-4 items-start">
                                                    <Database className="w-5 h-5 shrink-0" />
                                                    <p>{v.result}</p>
                                                </div>
                                            </div>
                                            <div className="px-6 py-2 bg-white/5 flex gap-2">
                                                {v.entities.map((e: string, j: number) => (
                                                    <span key={j} className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">@{e}</span>
                                                ))}
                                            </div>
                                        </Card>
                                    ))}
                                </div>
                            </section>

                            {/* Step 4: Final Response */}
                            <section>
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-[0_0_20px_rgba(37,99,235,0.5)]">
                                        <Sparkles className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">Final Verified Response</p>
                                        <h2 className="text-3xl font-black italic manga-font uppercase tracking-tighter">Réponse Consolidée</h2>
                                    </div>
                                </div>
                                <Card padding="lg" className="bg-blue-600 text-white border-none shadow-2xl text-xl font-bold leading-relaxed rounded-[2rem] relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-8 opacity-10">
                                        <ShieldCheck className="w-32 h-32" />
                                    </div>
                                    <p className="relative z-10">{trace.final_response}</p>
                                </Card>
                            </section>

                            <div className="pt-12 text-center">
                                <Button 
                                    variant="outline" 
                                    onClick={() => { setTrace(null); setQuestion(''); }}
                                    className="border-white/10 hover:bg-white/5 text-white/40 font-black uppercase italic tracking-widest"
                                >
                                    NOUVELLE ANALYSE
                                </Button>
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

export default CoveOraclePage;
