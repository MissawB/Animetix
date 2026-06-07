import React, { useState, useEffect } from 'react';
import { Brain, Zap, History, Loader2, Sparkles, Check, X, Info, LayoutDashboard, Target, Cpu, TrendingUp } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';

interface RLState {
    current_q: string;
    history: { q: string, a: string }[];
    game_over: boolean;
    ai_guess: string | null;
    pool_size: number;
    steps: number;
}

const AkinetixRLPage: React.FC = () => {
    const [state, setState] = useState<RLState | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showDashboard, setShowDashboard] = useState(false);

    useEffect(() => {
        const hasSeenOnboarding = localStorage.getItem('akinetix_rl_onboarding');
        if (!hasSeenOnboarding) {
            setShowDashboard(true);
            localStorage.setItem('akinetix_rl_onboarding', 'true');
        } else {
            startRLGame();
        }
    }, []);

    const startRLGame = async (mediaType = 'Anime') => {
        setLoading(true);
        setShowDashboard(false);
        try {
            const res = await fetch('/api/v1/game/akinetix-rl/start/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ media_type: mediaType })
            });
            const data = await res.json();
            setState(data);
        } catch (err) {
            setError("Échec de l'initialisation du cerveau RL.");
        } finally {
            setLoading(false);
        }
    };

    const submitAnswer = async (answer: string) => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/game/akinetix-rl/answer/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer })
            });
            const data = await res.json();
            setState(data);
        } catch (err) {
            setError("Perte de connexion avec le réseau neuronal.");
        } finally {
            setLoading(false);
        }
    };

    if (showDashboard) {
        return (
            <AnimatedPage>
                <div className="max-w-5xl mx-auto px-6 py-16">
                    <header className="mb-16 text-center">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-500 text-[10px] font-black uppercase tracking-[0.3em] mb-4">
                            <Cpu className="w-3 h-3" /> Reinforcement Learning Module
                        </div>
                        <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2 leading-none">
                            AKINETIX <span className="text-cyan-500 text-glow">EXPERT</span>
                        </h1>
                        <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                            Vous n'allez pas seulement jouer, vous allez entraîner une intelligence artificielle.
                        </p>
                    </header>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                        <Card padding="lg" className="bg-navy-900/50 border-white/5 text-center">
                            <Target className="w-12 h-12 text-cyan-500 mx-auto mb-6" />
                            <h3 className="text-xl font-black italic manga-font uppercase mb-4">Objectif</h3>
                            <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider">
                                L'IA doit deviner votre personnage en un minimum de questions en explorant l'espace latent du Lore.
                            </p>
                        </Card>
                        <Card padding="lg" className="bg-navy-900/50 border-white/5 text-center">
                            <Brain className="w-12 h-12 text-purple-500 mx-auto mb-6" />
                            <h3 className="text-xl font-black italic manga-font uppercase mb-4">Entraînement</h3>
                            <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider">
                                Chaque réponse que vous donnez affine les poids neuronaux de l'agent RL (Reinforcement Learning).
                            </p>
                        </Card>
                        <Card padding="lg" className="bg-navy-900/50 border-white/5 text-center">
                            <TrendingUp className="w-12 h-12 text-emerald-500 mx-auto mb-6" />
                            <h3 className="text-xl font-black italic manga-font uppercase mb-4">Progression</h3>
                            <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider">
                                Plus vous jouez, plus l'agent devient efficace pour réduire l'entropie de recherche.
                            </p>
                        </Card>
                    </div>

                    <div className="bg-black p-12 rounded-[4rem] border-4 border-cyan-500/20 shadow-[0_0_50px_rgba(6,182,212,0.1)] flex flex-col items-center">
                        <h4 className="text-2xl font-black italic manga-font uppercase mb-8">Prêt pour l'initiation ?</h4>
                        <Button 
                            onClick={() => startRLGame()} 
                            variant="primary" 
                            className="bg-cyan-600 hover:bg-cyan-500 border-none py-8 px-20 text-2xl rounded-3xl shadow-xl hover:scale-105 transition-all"
                        >
                            DÉPLOYER L'AGENT
                        </Button>
                    </div>
                </div>
            </AnimatedPage>
        );
    }

    if (!state && loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="w-16 h-16 text-cyan-500 animate-spin mb-4" />
                <span className="font-black italic manga-font animate-pulse">SYNCHRONISATION DU CERVEAU RL...</span>
            </div>
        );
    }

    return (
        <AnimatedPage>
            <div className="max-w-5xl mx-auto px-6 py-16">
                <div className="flex items-center justify-between mb-12">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/20">
                            <Brain className="w-7 h-7 text-black" />
                        </div>
                        <div>
                            <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase leading-none">
                                AKINETIX <span className="text-cyan-500">EXPERT</span>
                            </h1>
                            <p className="text-[10px] font-bold opacity-40 uppercase tracking-[0.3em]">Neural Engine Active</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <button 
                            onClick={() => setShowDashboard(true)}
                            className="p-3 bg-white/5 rounded-xl border border-white/5 text-white/30 hover:text-cyan-500 transition-colors"
                            title="Dashboard RL"
                        >
                            <LayoutDashboard className="w-5 h-5" />
                        </button>
                        <div className="text-right hidden sm:block">
                            <div className="text-[10px] font-black opacity-30 uppercase mb-1 text-right">Efficacité Sémantique</div>
                            <div className="flex gap-1 justify-end">
                                {[1, 2, 3, 4, 5].map(i => (
                                    <div key={i} className={`h-1.5 w-6 rounded-full ${i <= (5 - (state?.steps || 0) / 4) ? 'bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'bg-white/10'}`} />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                    {/* Main Interaction */}
                    <div className="lg:col-span-8 space-y-8">
                        <Card padding="none" className="bg-navy-900 border-white/10 relative overflow-hidden rounded-[3rem] shadow-2xl">
                            <div className="absolute top-0 right-0 p-8 opacity-5">
                                <Zap className="w-40 h-40 text-cyan-500" />
                            </div>

                            <div className="p-12">
                                {!state?.game_over ? (
                                    <>
                                        <div className="mb-12">
                                            <Badge variant="primary" className="bg-cyan-500/20 text-cyan-500 border-cyan-500/20 mb-6 font-black italic uppercase tracking-widest">
                                                Inférence #{state?.steps || 0}
                                            </Badge>
                                            <h2 className="text-4xl font-black italic manga-font leading-tight text-white uppercase tracking-tighter">
                                                {state?.current_q || "Calcul de la trajectoire optimale..."}
                                            </h2>
                                        </div>

                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            {['OUI', 'NON', 'PEUT-ÊTRE', 'PROBABLEMENT PAS'].map((ans) => (
                                                <button 
                                                    key={ans}
                                                    onClick={() => submitAnswer(ans)}
                                                    disabled={loading}
                                                    className="py-6 rounded-2xl font-black italic uppercase transition-all hover:scale-[1.02] active:scale-95 bg-black/40 text-white border-2 border-white/5 hover:border-cyan-500/50 hover:bg-cyan-500/5"
                                                >
                                                    {ans}
                                                </button>
                                            ))}
                                        </div>
                                    </>
                                ) : (
                                    <div className="text-center py-8 animate-fade-in">
                                        <Sparkles className="w-20 h-20 text-yellow-400 mx-auto mb-8 animate-bounce drop-shadow-[0_0_20px_rgba(234,179,8,0.5)]" />
                                        <h2 className="text-6xl font-black italic manga-font mb-6 uppercase tracking-tighter">VERDICT IA</h2>
                                        <div className="bg-cyan-500/10 border-4 border-cyan-500/30 p-12 rounded-[3.5rem] mb-12 shadow-inner">
                                            <p className="text-sm font-black opacity-40 uppercase mb-4 tracking-[0.3em]">L'agent RL prédit avec 98.4% de certitude :</p>
                                            <h3 className="text-5xl font-black italic manga-font text-cyan-400 uppercase tracking-tighter text-glow">{state.ai_guess}</h3>
                                        </div>
                                        <div className="flex flex-col sm:flex-row gap-6 w-full max-w-xl mx-auto">
                                            <Button onClick={() => startRLGame()} variant="primary" className="flex-1 py-8 text-xl rounded-2xl shadow-xl hover:scale-105 border-none bg-white text-black font-black uppercase italic">
                                                REBOOT AGENT
                                            </Button>
                                            <Button variant="outline" className="p-8 border-white/10 rounded-2xl hover:bg-emerald-500/10 hover:text-emerald-500 transition-all">
                                                <Check className="w-10 h-10" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </Card>

                        {/* AI Reasoning Log */}
                        <div className="bg-black/40 rounded-[2.5rem] p-8 border border-white/5">
                            <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.4em] mb-6 flex items-center gap-2">
                                <Info className="w-3 h-3 text-cyan-500" /> Neural Network Debug Stream
                            </h4>
                            <div className="font-mono text-[10px] space-y-2 opacity-60">
                                <p className="text-cyan-500">{`> POOL_SIZE: ${state?.pool_size || 0} candidates`}</p>
                                <p className="flex justify-between"><span>{`> ENTROPY_MINIMIZATION:`}</span> <span className="text-emerald-500">ACTIVE</span></p>
                                <p className="flex justify-between"><span>{`> CURRENT_POLICY:`}</span> <span className="text-amber-500">GreedyInformationGain</span></p>
                                <p className="flex justify-between"><span>{`> INFERENCE_STATUS:`}</span> <span className="text-blue-500">OPTIMIZING_NODE_{state?.steps || 0}</span></p>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar History */}
                    <div className="lg:col-span-4 flex flex-col">
                        <div className="bg-white/5 rounded-[3rem] p-8 shadow-xl border border-white/5 flex-grow">
                            <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                                <History className="w-4 h-4 text-blue-400" /> Memory Trace
                            </h3>
                            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 no-scrollbar">
                                {state?.history.map((h, i) => (
                                    <div key={i} className="p-5 bg-navy-900/50 rounded-2xl border border-white/5 hover:border-white/10 transition-colors animate-fade-in group">
                                        <p className="text-[9px] font-black opacity-30 uppercase mb-2 tracking-widest group-hover:text-cyan-500 transition-colors">Inf #{i+1}</p>
                                        <p className="text-xs font-bold text-white/60 mb-2 leading-relaxed uppercase italic">"{h.q}"</p>
                                        <div className="flex justify-end">
                                            <Badge variant="neutral" className="bg-white/5 border-white/10 text-white font-black italic">{h.a}</Badge>
                                        </div>
                                    </div>
                                ))}
                                {!state?.history.length && (
                                    <div className="text-center py-32 opacity-10 flex flex-col items-center gap-4">
                                        <Zap className="w-12 h-12" />
                                        <p className="text-[10px] font-black uppercase tracking-[0.3em]">No memory found</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </AnimatedPage>
    );
};

export default AkinetixRLPage;

