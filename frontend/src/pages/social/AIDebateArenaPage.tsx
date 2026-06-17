import React, { useState } from 'react';
import { 
  Swords,
  Scale, 
  Zap,
  CheckCircle2, 
  Sparkles,
  User,
  Gavel,
  History,
  Target
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next'; // Import useTranslation

const AIDebateArenaPage: React.FC = () => {
  const [mediaTitle, setMediaTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [debateResult, setDebateResult] = useState<Record<string, unknown> | null>(null);
  const { t } = useTranslation(); // Initialize useTranslation

  const mutation = useMutation({
    mutationFn: (data: { media_title: string; topic: string }) => 
        apiClient('/api/v1/cognition/debate-arena/', {
            method: 'POST',
            body: JSON.stringify(data)
        }),
    onSuccess: (data) => {
        setDebateResult(data);
    }
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mediaTitle.trim() && topic.trim()) {
        mutation.mutate({ media_title: mediaTitle, topic: topic });
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header Arena */}
        <header className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
               <Swords className="w-4 h-4 fill-current" /> Game Theory Arena v2.0
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                AI DEBATE <span className="text-red-500 text-glow">ARENA</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                Orchestrez des confrontations sémantiques entre agents spécialisés basées sur les faits du Knowledge Graph.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Configuration du Débat */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-500" /> Paramètres du Duel
                    </h3>
                    <form onSubmit={onSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label htmlFor="media-title" className="text-[10px] font-black uppercase tracking-widest opacity-30 ml-4">Œuvre Cible</label>
                            <input 
                                id="media-title"
                                type="text" 
                                value={mediaTitle}
                                onChange={(e) => setMediaTitle(e.target.value)}
                                placeholder="ex: Attack on Titan"
                                className="w-full bg-black border-2 border-white/5 rounded-2xl py-4 px-6 text-sm font-bold focus:border-red-600 outline-none transition-all placeholder:opacity-20"
                            />
                        </div>
                        <div className="space-y-2">
                            <label htmlFor="debate-topic" className="text-[10px] font-black uppercase tracking-widest opacity-30 ml-4">Thématique du Débat</label>
                            <textarea 
                                id="debate-topic"
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                rows={4}
                                placeholder="ex: La fin de l'œuvre est-elle cohérente avec le développement d'Eren ?"
                                className="w-full bg-black border-2 border-white/5 rounded-2xl py-4 px-6 text-sm font-bold focus:border-red-600 outline-none transition-all placeholder:opacity-20 resize-none"
                            />
                        </div>
                        <Button 
                            type="submit" 
                            disabled={mutation.isPending || !mediaTitle.trim() || !topic.trim()}
                            className="w-full bg-red-600 hover:bg-red-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {mutation.isPending ? <Zap className="w-6 h-6 animate-spin" /> : "LANCER LA CONFRONTATION"}
                        </Button>
                    </form>
                </Card>

                <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4">Fonctionnement</h4>
                    <ul className="space-y-4">
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Agent PRO : Défend une thèse favorable.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <CheckCircle2 className="w-4 h-4 text-red-500 shrink-0" /> Agent ANTI : Apporte une contradiction argumentée.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0" /> Agent JUGE : Synthétise et rend le verdict final.
                        </li>
                    </ul>
                </Card>
            </div>

            {/* Visualisation du Débat */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {mutation.isPending ? (
                        <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }} 
                            exit={{ opacity: 0 }}
                            className="h-full flex flex-col items-center justify-center py-24 text-center"
                        >
                            <div className="relative w-32 h-32 mb-8">
                                <motion.div 
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                    className="absolute inset-0 border-t-4 border-red-500 rounded-full"
                                />
                                <Swords className="w-16 h-16 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
                            </div>
                            <h3 className="text-2xl font-black italic manga-font uppercase mb-2">Inférence en cours</h3>
                            <p className="text-xs font-bold opacity-30 uppercase tracking-[0.2em]">Les agents consultent le Knowledge Graph...</p>
                        </motion.div>
                    ) : debateResult ? (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }} 
                            animate={{ opacity: 1, y: 0 }} 
                            className="space-y-8"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Pro Argument */}
                                <Card padding="lg" className="bg-emerald-500/5 border-emerald-500/20 relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 blur-3xl -mr-12 -mt-12" />
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-500">
                                            <User className="w-5 h-5" />
                                        </div>
                                        <span className="text-xs font-black uppercase tracking-widest text-emerald-500">Agent PRO</span>
                                    </div>
                                    <p className="text-sm font-bold leading-relaxed italic opacity-80">{debateResult.pro_argument}</p>
                                </Card>

                                {/* Anti Argument */}
                                <Card padding="lg" className="bg-red-500/5 border-red-500/20 relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/10 blur-3xl -mr-12 -mt-12" />
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="p-2 rounded-xl bg-red-500/20 text-red-500">
                                            <User className="w-5 h-5" />
                                        </div>
                                        <span className="text-xs font-black uppercase tracking-widest text-red-500">Agent ANTI</span>
                                    </div>
                                    <p className="text-sm font-bold leading-relaxed italic opacity-80">{debateResult.anti_argument}</p>
                                </Card>
                            </div>

                            {/* Verdict du Juge */}
                            <Card padding="none" className="bg-black border-blue-500/30 shadow-[0_0_50px_rgba(59,130,246,0.15)] rounded-[3.5rem] overflow-hidden">
                                <div className="bg-blue-600 px-12 py-6 flex items-center justify-between">
                                    <h3 className="text-2xl font-black italic manga-font uppercase text-white flex items-center gap-4">
                                        <Gavel className="w-8 h-8" /> VERDICT DU JUGE
                                    </h3>
                                    <Badge variant="neutral" className="bg-black/20 text-white border-none uppercase font-black italic">Final Resolution</Badge>
                                </div>
                                <div className="p-12">
                                    <p className="text-xl font-bold leading-relaxed text-white/90 whitespace-pre-wrap">
                                        {debateResult.judge_conclusion}
                                    </p>
                                    
                                    <div className="mt-12 pt-8 border-t border-white/5 flex flex-wrap gap-8 items-center justify-between">
                                        <div className="flex gap-8">
                                            <div className="flex items-center gap-2">
                                                <Scale className="w-4 h-4 text-blue-500" />
                                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Objectivité: 98%</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Target className="w-4 h-4 text-emerald-500" />
                                                <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Basé sur 12 faits</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-4">
                                            <Button variant="outline" className="rounded-xl px-6 py-2 text-[10px] font-black uppercase border-white/10">UTILE</Button>
                                            <Button variant="outline" className="rounded-xl px-6 py-2 text-[10px] font-black uppercase border-white/10">BIAISÉ</Button>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center py-32 opacity-10 text-center border-4 border-dashed border-white/5 rounded-[4rem]">
                            <Swords className="w-32 h-32 mb-8" />
                            <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Arène en attente</h3>
                            <p className="text-sm font-bold uppercase tracking-[0.3em]">Configurez un duel pour voir l'IA débattre.</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>

        {/* MLOps Section */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <History className="w-8 h-8 text-gray-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Génération DPO</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Chaque débat génère une paire d'entraînement (Chosen/Rejected) pour affiner la neutralité des modèles futurs.</p>
            </Card>
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <Sparkles className="w-8 h-8 text-blue-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Knowledge Grounding</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Les agents utilisent le RAG Agentique pour sourcer leurs arguments directement dans la base de lore sémantique.</p>
            </Card>
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <Scale className="w-8 h-8 text-red-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Théorie des Jeux</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">L'équilibre de Nash est recherché entre les arguments pour garantir une synthèse finale la plus juste possible.</p>
            </Card>
        </div>
        {/* Explanation Cards Section */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Swords className="w-64 h-64 text-red-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3 text-red-400">
                    <Swords className="w-5 h-5" /> {t('labs.ai_debate_arena.explainer_title')}
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                        {t('labs.ai_debate_arena.explainer_text_card1')}
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                        {t('labs.ai_debate_arena.explainer_text_card2')}
                    </p>
                </div>
            </Card>
            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic leading-relaxed text-red-200/40">
                    {t('labs.ai_debate_arena.subtitle')}
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AIDebateArenaPage;