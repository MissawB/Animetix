import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import { Skull, Zap, Info, Target, Trophy } from 'lucide-react';
import { apiClient } from '../../utils/apiClient';

const WorldBossPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [guess, setGuess] = React.useState('');
  const [feedback, setFeedback] = React.useState<{ is_correct: boolean; damage: number } | null>(null);

  const { data: boss, isLoading, error } = useQuery({
    queryKey: ['world-boss', 'active'],
    queryFn: async () => {
      return apiClient('/api/v1/game/world-boss/active/');
    },
    refetchInterval: 10000, // Refresh every 10s to see global progress
  });

  const { data: leaderboard } = useQuery({
    queryKey: ['world-boss', 'leaderboard', boss?.id],
    queryFn: async () => {
      const res = await apiClient('/api/v1/game/world-boss/leaderboard/', { skipToast: true });
      return (res.leaderboard ?? []) as Array<{ id: number; username: string; points_contributed: number }>;
    },
    enabled: !!boss?.id,
    refetchInterval: 10000,
  });

  const attackMutation = useMutation({
    mutationFn: async (guess: string) => {
        return apiClient('/api/v1/game/world-boss/attack/', {
            method: 'POST',
            body: JSON.stringify({ boss_id: boss?.id, guess })
        });
    },
    onSuccess: (data) => {
        setFeedback({ is_correct: data.is_correct, damage: data.damage_dealt });
        setGuess('');
        queryClient.invalidateQueries({ queryKey: ['world-boss', 'active'] });
        queryClient.invalidateQueries({ queryKey: ['world-boss', 'leaderboard'] });
        setTimeout(() => setFeedback(null), 3000);
    }
  });

  const handleAttack = (e: React.FormEvent) => {
    e.preventDefault();
    if (!guess.trim() || attackMutation.isPending) return;
    attackMutation.mutate(guess);
  };

  if (isLoading) return (
    <div className="min-h-screen bg-black flex items-center justify-center" aria-label="Loading Raid">
        <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full"
        />
    </div>
  );

  if (error || !boss) return (
    <AnimatedPage>
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center">
            <Skull size={80} className="text-gray-800 mb-6" />
            <h2 className="text-4xl font-black uppercase italic mb-4">No Active Boss</h2>
            <p className="text-gray-500 max-w-md">
                The world is currently safe... or the next threat is still gathering its strength. 
                Come back later for the next global raid!
            </p>
        </div>
    </AnimatedPage>
  );

  const hpPercent = (boss.current_hp / boss.total_hp) * 100;

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12 text-white">
        <header className="text-center mb-16 relative">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="inline-block px-4 py-1 bg-red-600/20 border border-red-500/50 rounded-full text-red-500 text-xs font-bold tracking-widest uppercase mb-4"
            >
                Global Event Active
            </motion.div>
            <motion.h1 
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-7xl md:text-8xl font-black italic uppercase text-white drop-shadow-[0_0_30px_rgba(239,68,68,0.4)] mb-2"
            >
                {boss.title}
            </motion.h1>
            <div className="flex items-center justify-center gap-6 text-gray-400 font-bold uppercase tracking-widest text-sm">
                <span className="flex items-center gap-2">
                    <Target size={16} className="text-red-500" />
                    Phase {boss.current_phase}
                </span>
                <span className="w-1 h-1 bg-gray-700 rounded-full" />
                <span>{boss.media_type} Type</span>
                <span className="w-1 h-1 bg-gray-700 rounded-full" />
                <span className="flex items-center gap-2">
                    <Trophy size={16} className="text-yellow-500" />
                    {boss.reward_xp} XP REWARD
                </span>
            </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
                {/* Boss Battle Visualizer */}
                <div className="relative aspect-video bg-gradient-to-b from-red-950/20 to-black rounded-3xl border border-red-900/30 flex items-center justify-center overflow-hidden group">
                    <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20" />
                    
                    {/* Boss Spirit Placeholder */}
                    <motion.div 
                        animate={{ 
                            y: [0, -10, 0],
                            scale: [1, 1.02, 1]
                        }}
                        transition={{ duration: 4, repeat: Infinity }}
                        className="relative z-10 text-9xl text-red-600/20 select-none font-black"
                    >
                        <Skull size={200} strokeWidth={1} />
                    </motion.div>

                    {/* Damage Feedback Overlay */}
                    <AnimatePresence>
                        {feedback && (
                            <motion.div 
                                initial={{ opacity: 0, scale: 0.5, y: 0 }}
                                animate={{ opacity: 1, scale: 1.5, y: -50 }}
                                exit={{ opacity: 0 }}
                                className={`absolute z-20 font-black text-4xl ${feedback.is_correct ? 'text-yellow-400' : 'text-gray-500'}`}
                            >
                                {feedback.is_correct ? `-${feedback.damage} HP!` : 'MISSED'}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* HP Overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black to-transparent">
                        <div className="flex justify-between items-end mb-4">
                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-red-500 font-black text-xs tracking-tighter uppercase">
                                    <Zap size={14} fill="currentColor" />
                                    World Integrity
                                </div>
                                <div className="text-4xl font-mono font-black tracking-tighter italic">
                                    {boss.current_hp.toLocaleString()} <span className="text-gray-600 text-xl font-normal">/ {boss.total_hp.toLocaleString()}</span>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-2xl font-black text-red-500 italic">{Math.round(hpPercent)}%</span>
                            </div>
                        </div>
                        
                        <div className="h-4 bg-gray-900 rounded-full overflow-hidden border border-white/5 p-1">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${hpPercent}%` }}
                                transition={{ duration: 1.5, ease: "circOut" }}
                                className={`h-full rounded-full shadow-[0_0_15px_rgba(239,68,68,0.5)] ${
                                    hpPercent < 20 ? 'bg-red-700' : 
                                    hpPercent < 50 ? 'bg-orange-600' : 
                                    'bg-red-500'
                                }`}
                            />
                        </div>
                    </div>
                </div>

                {/* Participation Form */}
                <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5">
                    <h3 className="text-xl font-black italic uppercase mb-6 flex items-center gap-3">
                        <Zap className="text-yellow-500" fill="currentColor" size={20} />
                        Communal Strike
                    </h3>
                    <form onSubmit={handleAttack} className="space-y-4">
                        <div className="relative group">
                            <input 
                                type="text" 
                                value={guess}
                                onChange={(e) => setGuess(e.target.value)}
                                placeholder="WHO IS THIS BOSS? ENTER THE TITLE..."
                                aria-label="Titre du boss à deviner"
                                className="w-full bg-black border-2 border-gray-800 rounded-2xl px-6 py-5 focus:border-red-600 outline-none transition-all font-bold tracking-widest uppercase placeholder:text-gray-700"
                            />
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2">
                                <button 
                                    type="submit"
                                    disabled={attackMutation.isPending || !guess.trim()}
                                    className="bg-red-600 hover:bg-red-500 disabled:opacity-20 px-8 py-3 rounded-xl font-black italic uppercase tracking-widest transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
                                >
                                    {attackMutation.isPending ? 'STRIKING...' : 'STRIKE'}
                                    <Zap size={16} fill="currentColor" />
                                </button>
                            </div>
                        </div>
                        <p className="text-gray-600 text-xs font-bold uppercase tracking-widest px-2">
                            Each correct guess damages the boss and reveals it to the world.
                        </p>
                    </form>
                </div>
            </div>

            <div className="space-y-8">
                {/* Hints Panel */}
                <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5">
                    <h3 className="text-xl font-black italic uppercase mb-6 flex items-center gap-3">
                        <Info className="text-blue-500" size={20} />
                        Deciphered Data
                    </h3>
                    <div className="space-y-4">
                        {boss.community_hints.length > 0 ? (
                            boss.community_hints.map((hint: string, i: number) => (
                                <motion.div 
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    key={i} 
                                    className="bg-black/40 p-4 rounded-xl text-gray-400 border-l-4 border-red-600 font-medium leading-relaxed"
                                >
                                    {hint}
                                </motion.div>
                            ))
                        ) : (
                            <div className="text-center py-12 text-gray-700 uppercase font-black italic tracking-widest">
                                No hints deciphered yet.
                            </div>
                        )}
                    </div>
                </div>

                {/* Contributors Leaderboard */}
                <div className="bg-gray-900/50 backdrop-blur-xl p-8 rounded-3xl border border-white/5">
                    <h3 className="text-xl font-black italic uppercase mb-6 flex items-center gap-3">
                        <Trophy className="text-yellow-500" size={20} />
                        Top Raiders
                    </h3>
                    <div className="space-y-2">
                        {leaderboard && leaderboard.length > 0 ? (
                            leaderboard.map((row, i) => (
                                <div
                                    key={row.id}
                                    className="flex items-center gap-3 bg-black/40 p-3 rounded-xl"
                                >
                                    <span className={`w-7 text-center font-black italic ${
                                        i === 0 ? 'text-yellow-400' :
                                        i === 1 ? 'text-gray-300' :
                                        i === 2 ? 'text-orange-500' : 'text-gray-600'
                                    }`}>
                                        {i + 1}
                                    </span>
                                    <span className="flex-1 font-bold text-white/90 truncate">{row.username}</span>
                                    <span className="font-mono font-black text-red-500 text-sm">
                                        {row.points_contributed.toLocaleString()}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-12 text-gray-700 uppercase font-black italic tracking-widest">
                                No raiders yet. Be the first!
                            </div>
                        )}
                    </div>
                </div>

                {/* Info Card */}
                <div className="bg-red-950/10 p-8 rounded-3xl border border-red-900/20">
                    <div className="flex items-center gap-3 text-red-500 mb-4">
                        <Skull size={20} />
                        <h4 className="font-black italic uppercase tracking-widest">Raid Protocol</h4>
                    </div>
                    <p className="text-gray-400 text-sm leading-relaxed">
                        The World Boss is a massive entity that requires community cooperation. 
                        As its HP drops, it will enter new, more dangerous phases, revealing more hints. 
                        Defeat it before the time expires to earn exclusive rewards.
                    </p>
                </div>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default WorldBossPage;


