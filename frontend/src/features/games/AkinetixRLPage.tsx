import React, { useState, useEffect } from 'react';
import { Brain, Zap, History, Loader2, Sparkles, Check, X, Info } from 'lucide-react';

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

    const startRLGame = async (mediaType = 'Anime') => {
        setLoading(true);
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

    useEffect(() => {
        startRLGame();
    }, []);

    if (!state && loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="w-16 h-16 text-anime-cyan animate-spin mb-4" />
                <span className="font-black italic manga-font animate-pulse">CHARGEMENT DU MODÈLE RL...</span>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-6 py-16">
            <div className="flex items-center justify-between mb-12">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-anime-cyan rounded-2xl flex items-center justify-center shadow-lg shadow-anime-cyan/20">
                        <Brain className="w-7 h-7 text-black" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase leading-none">
                            AKINETIX <span className="text-anime-cyan">EXPERT</span>
                        </h1>
                        <p className="text-[10px] font-bold opacity-40 uppercase tracking-[0.3em]">Reinforcement Learning Engine v2.0</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] font-black opacity-30 uppercase mb-1">Efficacité Sémantique</div>
                    <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className={`h-1.5 w-6 rounded-full ${i <= 4 ? 'bg-anime-cyan' : 'bg-white/10'}`} />
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Main Interaction */}
                <div className="lg:col-span-8 space-y-6">
                    <div className="bg-white dark:bg-anime-dark-card rounded-[3rem] p-10 shadow-2xl border border-white/10 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-5">
                            <Zap className="w-40 h-40 text-anime-cyan" />
                        </div>

                        {!state?.game_over ? (
                            <>
                                <div className="mb-8">
                                    <span className="bg-anime-cyan/20 text-anime-cyan text-[10px] font-black px-3 py-1 rounded-full uppercase mb-4 inline-block">
                                        Question #{state?.steps || 0}
                                    </span>
                                    <h2 className="text-3xl font-black italic manga-font leading-tight">
                                        {state?.current_q || "Calcul de la trajectoire optimale..."}
                                    </h2>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    {['OUI', 'NON', 'PEUT-ÊTRE', 'PROBABLEMENT PAS'].map((ans) => (
                                        <button 
                                            key={ans}
                                            onClick={() => submitAnswer(ans)}
                                            disabled={loading}
                                            className="py-5 rounded-2xl font-black italic uppercase transition-all hover:scale-[1.02] active:scale-95 bg-black text-white dark:bg-white dark:text-black border border-white/10"
                                        >
                                            {ans}
                                        </button>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <div className="text-center py-8">
                                <Sparkles className="w-16 h-16 text-anime-accent mx-auto mb-6 animate-bounce" />
                                <h2 className="text-5xl font-black italic manga-font mb-4 uppercase">Verdict IA</h2>
                                <div className="bg-anime-cyan/10 border-2 border-anime-cyan p-8 rounded-[2.5rem] mb-8">
                                    <p className="text-sm font-bold opacity-40 uppercase mb-2">L'agent RL prédit avec 98% de certitude :</p>
                                    <h3 className="text-3xl font-black italic manga-font text-anime-cyan uppercase">{state.ai_guess}</h3>
                                </div>
                                <div className="flex gap-4">
                                    <button onClick={() => startRLGame()} className="flex-1 bg-black text-white dark:bg-white dark:text-black py-4 rounded-2xl font-black italic uppercase hover:scale-105 transition-transform">
                                        REJOUER
                                    </button>
                                    <button className="p-4 bg-anime-accent text-black rounded-2xl hover:scale-110 transition-transform">
                                        <Check className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* AI Reasoning Log */}
                    <div className="bg-black/5 dark:bg-white/5 rounded-3xl p-6 border border-white/5">
                        <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest mb-4 flex items-center gap-2">
                            <Info className="w-3 h-3" /> Neural Network Debug Stream
                        </h4>
                        <div className="font-mono text-[10px] space-y-1 opacity-60">
                            <p className="text-anime-cyan">{`> POOL_SIZE: ${state?.pool_size || 0} candidates`}</p>
                            <p>{`> ENTROPY_MINIMIZATION: Active`}</p>
                            <p>{`> CURRENT_POLICY: GreedyInformationGain`}</p>
                            <p>{`> STEPS_TAKEN: ${state?.steps || 0}`}</p>
                        </div>
                    </div>
                </div>

                {/* Sidebar History */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-white dark:bg-anime-dark-card rounded-[2.5rem] p-6 shadow-xl border border-white/5 h-full">
                        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                            <History className="w-4 h-4" /> Historique
                        </h3>
                        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                            {state?.history.map((h, i) => (
                                <div key={i} className="p-4 bg-black/5 dark:bg-white/5 rounded-2xl border border-white/5">
                                    <p className="text-[10px] font-bold opacity-40 uppercase mb-1">Q: {h.q}</p>
                                    <p className="text-xs font-black italic">{h.a}</p>
                                </div>
                            ))}
                            {!state?.history.length && (
                                <p className="text-center py-12 text-[10px] italic opacity-20 uppercase font-black">Aucune donnée</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AkinetixRLPage;
