import React, { useState } from 'react';
import { Swords, Trophy, Loader2, AlertCircle, Heart, Share2, TrendingUp, Clock, History, Flame } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useQuery, useMutation } from '@tanstack/react-query';
import { vsBattleService } from './services/vsBattleService';
import { queryClient } from '../../utils/queryClient';

const VsBattlePage: React.FC = () => {
  const { t } = useTranslation();
  
  const [charA, setCharA] = useState('');
  const [franchiseA, setFranchiseA] = useState('');
  const [charB, setCharB] = useState('');
  const [franchiseB, setFranchiseB] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: arenaFeed, isLoading: isFeedLoading } = useQuery({
    queryKey: ['vs-arena-feed'],
    queryFn: vsBattleService.getArenaFeed
  });

  const likeMutation = useMutation({
    mutationFn: (id: number) => vsBattleService.likeBattle(id),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['vs-arena-feed'] });
    }
  });

  const handleFight = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!charA || !charB) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await vsBattleService.runBattle(charA, charB, franchiseA, franchiseB);
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['vs-arena-feed'] });
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred during the battle.');
    } finally {
      setIsLoading(false);
    }
  };

  const getTierColor = (value: number) => {
    if (value >= 90) return 'text-red-500';
    if (value >= 70) return 'text-orange-500';
    if (value >= 50) return 'text-yellow-500';
    if (value >= 30) return 'text-green-500';
    return 'text-blue-500';
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="text-center mb-16 relative">
          <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-10">
              <Swords className="w-40 h-40" />
          </div>
          <h1 className="text-5xl md:text-8xl font-black italic manga-font tracking-tighter uppercase mb-4 relative z-10">
            ARENA <span className="text-red-500 text-glow">ULTIMATUM</span>
          </h1>
          <p className="text-xl font-bold opacity-40 uppercase tracking-[0.4em] relative z-10">
            Défis Trans-Dimensionnels arbitrés par l'IA
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
            
            {/* Left Column: Form & Result */}
            <div className="lg:col-span-8 space-y-12">
                {!result ? (
                    <form onSubmit={handleFight} className="space-y-12 animate-fade-in">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
                            {/* VS Badge */}
                            <div className="hidden md:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-16 h-16 bg-red-600 rounded-full items-center justify-center border-4 border-black shadow-[0_0_30px_rgba(239,68,68,0.4)]">
                                <span className="text-2xl font-black italic">VS</span>
                            </div>

                            {/* Fighter A */}
                            <Card padding="xl" className="border-2 border-red-500/10 bg-red-500/5 rounded-[3rem]">
                                <h2 className="text-2xl font-black uppercase italic mb-8 text-red-500">Challenger A</h2>
                                <div className="space-y-6">
                                    <Input 
                                        value={charA} 
                                        onChange={e => setCharA(e.target.value)} 
                                        placeholder="Nom du personnage" 
                                        required 
                                        className="text-lg bg-black border-red-500/20 focus:border-red-500 py-6"
                                    />
                                    <Input 
                                        value={franchiseA} 
                                        onChange={e => setFranchiseA(e.target.value)} 
                                        placeholder="Franchise (ex: Naruto)" 
                                        className="bg-black border-red-500/20 focus:border-red-500"
                                    />
                                </div>
                            </Card>

                            {/* Fighter B */}
                            <Card padding="xl" className="border-2 border-blue-500/10 bg-blue-500/5 rounded-[3rem]">
                                <h2 className="text-2xl font-black uppercase italic mb-8 text-blue-500 text-right">Challenger B</h2>
                                <div className="space-y-6">
                                    <Input 
                                        value={charB} 
                                        onChange={e => setCharB(e.target.value)} 
                                        placeholder="Nom du personnage" 
                                        required 
                                        className="text-lg bg-black border-blue-500/20 focus:border-blue-500 py-6 text-right"
                                    />
                                    <Input 
                                        value={franchiseB} 
                                        onChange={e => setFranchiseB(e.target.value)} 
                                        placeholder="Franchise (ex: Bleach)" 
                                        className="bg-black border-blue-500/20 focus:border-blue-500 text-right"
                                    />
                                </div>
                            </Card>
                        </div>

                        {error && (
                            <div className="bg-red-500/10 text-red-500 p-6 rounded-2xl flex items-center justify-center gap-3 font-black uppercase italic border border-red-500/20">
                                <AlertCircle className="w-6 h-6" />
                                {error}
                            </div>
                        )}

                        <div className="text-center pt-8">
                            <Button 
                                type="submit" 
                                size="lg" 
                                disabled={isLoading}
                                className="bg-red-600 hover:bg-red-500 text-white font-black text-3xl italic uppercase px-16 py-10 rounded-[2.5rem] shadow-2xl hover:scale-105 transition-all border-none"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-4"><Loader2 className="w-8 h-8 animate-spin" /> SYNCHRONISATION DU LORE...</span>
                                ) : (
                                    <span className="flex items-center gap-4"><Swords className="w-8 h-8" /> ENGAGER LE DUEL</span>
                                )}
                            </Button>
                        </div>
                    </form>
                ) : (
                    /* Battle Results */
                    <div className="space-y-12 animate-fade-in">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
                                <div className="w-20 h-20 bg-red-600 rounded-full flex items-center justify-center border-4 border-black shadow-[0_0_40px_rgba(220,38,38,0.5)]">
                                    <Swords className="w-10 h-10 text-white" />
                                </div>
                            </div>

                            {[result.character_a, result.character_b].map((char, idx) => (
                                <Card key={idx} className={`relative overflow-hidden rounded-[3rem] border-white/10 ${idx === 0 ? 'bg-red-950/20' : 'bg-blue-950/20'}`}>
                                    {char.image_url && (
                                        <div className="absolute inset-0 opacity-20 bg-cover bg-center grayscale group-hover:grayscale-0 transition-all duration-700" style={{ backgroundImage: `url(${char.image_url})`}} />
                                    )}
                                    <div className="relative z-10 p-10">
                                        <Badge variant="neutral" className="mb-4 bg-white/5 border-white/10 text-[8px] font-black tracking-widest">{char.franchise}</Badge>
                                        <h3 className="text-3xl font-black uppercase italic mb-6 manga-font">{char.name}</h3>
                                        
                                        <div className="space-y-6">
                                            <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                                                <span className="text-[10px] uppercase font-black opacity-30 block mb-1">Power Tier</span>
                                                <span className={`text-xl font-black italic ${getTierColor(char.stats.tier_value)}`}>{char.stats.tier}</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                                                    <span className="text-[10px] uppercase font-black opacity-30 block mb-1">Vitesse</span>
                                                    <span className="text-xs font-bold truncate block">{char.stats.speed}</span>
                                                </div>
                                                <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                                                    <span className="text-[10px] uppercase font-black opacity-30 block mb-1">Endurance</span>
                                                    <span className="text-xs font-bold truncate block">{char.stats.durability}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        {/* Verdict Final */}
                        <Card padding="xl" className="border-4 border-red-600/50 bg-navy-900 rounded-[4rem] relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-8 opacity-5">
                                <Trophy className="w-40 h-40" />
                            </div>
                            <div className="text-center relative z-10">
                                <h2 className="text-xs font-black uppercase tracking-[0.5em] opacity-40 mb-4">Verdict de l'Arbitre IA</h2>
                                <div className="text-6xl font-black italic uppercase text-red-500 manga-font mb-8 text-glow">{result.winner} GAGNE</div>
                                <p className="text-lg leading-relaxed text-white/80 font-medium italic max-w-3xl mx-auto">
                                    "{result.verdict_summary}"
                                </p>
                            </div>
                        </Card>

                        <div className="text-center pt-8">
                            <Button size="lg" variant="outline" onClick={() => setResult(null)} className="px-12 py-4 border-white/10 rounded-2xl uppercase font-black italic tracking-widest">
                                NOUVEAU CHALLENGE
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            {/* Right Column: Arena Feed */}
            <div className="lg:col-span-4 space-y-8">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                        <History className="w-4 h-4" /> Arène Publique
                    </h3>
                    <Badge variant="neutral" className="bg-red-500/10 text-red-500 border-red-500/20 text-[8px]">LIVE FEED</Badge>
                </div>

                <div className="space-y-4">
                    {isFeedLoading ? (
                        [...Array(3)].map((_, i) => <CardSkeleton key={i} />)
                    ) : arenaFeed?.map((battle: any) => (
                        <Card key={battle.id} padding="md" className="bg-navy-900/50 border-white/5 hover:border-white/10 transition-all group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="text-[10px] font-black uppercase opacity-30 italic">{new Date(battle.created_at).toLocaleDateString()}</div>
                                <button 
                                    onClick={() => likeMutation.mutate(battle.id)}
                                    className={`flex items-center gap-1 text-[10px] font-black transition-colors ${battle.is_liked ? 'text-red-500' : 'text-white/20 hover:text-red-400'}`}
                                >
                                    <Heart className={`w-3 h-3 ${battle.is_liked ? 'fill-current' : ''}`} /> {battle.likes_count}
                                </button>
                            </div>
                            <div className="flex items-center justify-between gap-4 mb-4">
                                <div className="flex-1 text-center">
                                    <p className="text-[10px] font-black italic manga-font truncate text-white">{battle.char_a_name}</p>
                                    <p className="text-[8px] opacity-30 uppercase truncate">{battle.char_a_franchise}</p>
                                </div>
                                <div className="text-red-500 font-black italic text-xs">VS</div>
                                <div className="flex-1 text-center">
                                    <p className="text-[10px] font-black italic manga-font truncate text-white">{battle.char_b_name}</p>
                                    <p className="text-[8px] opacity-30 uppercase truncate">{battle.char_b_franchise}</p>
                                </div>
                            </div>
                            <div className="bg-black/40 p-3 rounded-xl border border-white/5">
                                <p className="text-[9px] font-bold text-white/50 uppercase leading-tight line-clamp-2 italic">
                                    Winner: <span className="text-red-500">{battle.winner}</span> — "{battle.verdict_summary}"
                                </p>
                            </div>
                        </Card>
                    ))}
                </div>

                <Card padding="lg" className="bg-red-600 text-white border-none shadow-red-600/20">
                    <Flame className="w-10 h-10 mb-4 animate-pulse" />
                    <h4 className="text-xl font-black italic manga-font uppercase mb-2 text-white">Règles de l'Arène</h4>
                    <p className="text-[10px] font-bold opacity-80 leading-relaxed uppercase italic text-white">
                        Les duels sont générés en temps réel par le cluster de calcul. Les membres Premium peuvent forcer des combats impliquant des personnages non-indexés.
                    </p>
                </Card>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VsBattlePage;
