import React, { useState } from 'react';
import { Swords, Trophy, Loader2, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { runVsBattle, VsBattleResult } from '../../api';

const VsBattlePage: React.FC = () => {
  const { t } = useTranslation();
  
  const [charA, setCharA] = useState('');
  const [franchiseA, setFranchiseA] = useState('');
  const [charB, setCharB] = useState('');
  const [franchiseB, setFranchiseB] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VsBattleResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFight = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!charA || !charB) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await runVsBattle({
        char_a: charA,
        char_b: charB,
        char_a_franchise: franchiseA,
        char_b_franchise: franchiseB,
      });
      setResult(data);
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
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
            VERSUS <span className="text-red-500">BATTLE</span>
          </h1>
          <p className="text-xl font-bold opacity-50 uppercase tracking-widest">
            The Ultimate AI Deathbattle Arena
          </p>
        </div>

        {!result ? (
          <form onSubmit={handleFight} className="space-y-12">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 relative">
              {/* VS Badge */}
              <div className="hidden md:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-20 h-20 bg-brand-primary rounded-full items-center justify-center border-4 border-surface shadow-2xl">
                <span className="text-3xl font-black italic">VS</span>
              </div>

              {/* Fighter A */}
              <Card padding="xl" className="border-2 border-red-500/20 bg-red-500/5 relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-transparent" />
                <h2 className="text-3xl font-black uppercase italic mb-8 text-red-500">Fighter 1</h2>
                <div className="space-y-6">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Character Name</label>
                    <Input 
                      value={charA} 
                      onChange={e => setCharA(e.target.value)} 
                      placeholder="e.g. Levi Ackerman" 
                      required 
                      className="text-lg bg-surface border-red-500/30 focus:border-red-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Franchise (Optional)</label>
                    <Input 
                      value={franchiseA} 
                      onChange={e => setFranchiseA(e.target.value)} 
                      placeholder="e.g. Attack on Titan" 
                      className="bg-surface border-red-500/30 focus:border-red-500"
                    />
                  </div>
                </div>
              </Card>

              {/* Fighter B */}
              <Card padding="xl" className="border-2 border-blue-500/20 bg-blue-500/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-full h-1 bg-gradient-to-l from-blue-500 to-transparent" />
                <h2 className="text-3xl font-black uppercase italic mb-8 text-blue-500 text-right">Fighter 2</h2>
                <div className="space-y-6">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Character Name</label>
                    <Input 
                      value={charB} 
                      onChange={e => setCharB(e.target.value)} 
                      placeholder="e.g. Thorfinn" 
                      required 
                      className="text-lg bg-surface border-blue-500/30 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Franchise (Optional)</label>
                    <Input 
                      value={franchiseB} 
                      onChange={e => setFranchiseB(e.target.value)} 
                      placeholder="e.g. Vinland Saga" 
                      className="bg-surface border-blue-500/30 focus:border-blue-500"
                    />
                  </div>
                </div>
              </Card>
            </div>

            {error && (
              <div className="bg-red-500/20 text-red-400 p-4 rounded-xl flex items-center justify-center gap-3 font-bold">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            <div className="text-center pt-8">
              <Button 
                type="submit" 
                size="lg" 
                disabled={isLoading}
                className="bg-brand-accent text-black font-black text-3xl italic uppercase px-16 py-8 rounded-[2rem] hover:scale-105 transition-transform"
              >
                {isLoading ? (
                  <span className="flex items-center gap-4"><Loader2 className="w-8 h-8 animate-spin" /> SIMULATING...</span>
                ) : (
                  <span className="flex items-center gap-4"><Swords className="w-8 h-8" /> ENGAGE BATTLE</span>
                )}
              </Button>
            </div>
          </form>
        ) : (
          /* Battle Results */
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
            {/* Header Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
                <div className="w-24 h-24 bg-brand-primary rounded-full flex flex-col items-center justify-center border-4 border-surface shadow-[0_0_50px_rgba(var(--color-primary),0.5)]">
                  <Swords className="w-10 h-10 mb-1" />
                </div>
              </div>

              {[result.character_a, result.character_b].map((char, idx) => (
                <Card key={idx} className={`relative overflow-hidden ${idx === 0 ? 'border-red-500/30' : 'border-blue-500/30'}`}>
                  {char.image_url && (
                    <div className="absolute inset-0 opacity-10 bg-cover bg-center" style={{ backgroundImage: `url(${char.image_url})`}} />
                  )}
                  <div className="relative z-10 p-8 flex flex-col h-full justify-center">
                    <h3 className="text-3xl font-black uppercase italic mb-2">{char.name}</h3>
                    <p className="text-sm font-bold opacity-60 uppercase tracking-widest mb-6">{char.franchise || 'Unknown Franchise'}</p>
                    
                    <div className="space-y-4">
                      <div>
                        <span className="text-xs uppercase opacity-50 block mb-1">Power Tier</span>
                        <span className={`text-xl font-bold ${getTierColor(char.stats.tier_value)}`}>{char.stats.tier} (Score: {char.stats.tier_value})</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-xs uppercase opacity-50 block mb-1">Speed</span>
                          <span className="text-sm font-bold truncate block" title={char.stats.speed}>{char.stats.speed}</span>
                        </div>
                        <div>
                          <span className="text-xs uppercase opacity-50 block mb-1">Durability</span>
                          <span className="text-sm font-bold truncate block" title={char.stats.durability}>{char.stats.durability}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Verdict */}
            <Card padding="xl" className="border-4 border-brand-accent/50 bg-gradient-to-br from-surface to-brand-accent/10">
              <div className="text-center mb-8">
                <Trophy className="w-16 h-16 text-brand-accent mx-auto mb-4" />
                <h2 className="text-xs font-black uppercase tracking-[0.4em] opacity-50 mb-2">Verdict Final</h2>
                <div className="text-5xl font-black italic uppercase text-brand-accent">{result.winner}</div>
              </div>
              <p className="text-lg leading-relaxed text-surface-text font-medium text-center max-w-4xl mx-auto">
                {result.verdict_summary}
              </p>
            </Card>

            {/* Debate History */}
            <div className="space-y-6 max-w-4xl mx-auto">
              <h3 className="text-2xl font-black italic uppercase text-center mb-8">Debate Logs</h3>
              {result.debate_history.map((turn, i) => {
                const isA = turn.agent === 'Advocate_A';
                const isB = turn.agent === 'Advocate_B';
                const isJudge = turn.agent === 'Judge';
                
                return (
                  <div key={i} className={`flex flex-col ${isB ? 'items-end' : 'items-start'}`}>
                    <span className={`text-xs font-bold uppercase tracking-widest mb-2 opacity-50 ${isA ? 'text-red-500' : isB ? 'text-blue-500' : 'text-brand-accent'}`}>
                      {turn.agent}
                    </span>
                    <Card className={`max-w-[85%] p-6 ${isA ? 'bg-red-500/10 border-red-500/20' : isB ? 'bg-blue-500/10 border-blue-500/20' : 'bg-surface border-brand-accent/30'}`}>
                      <p className="whitespace-pre-wrap leading-relaxed text-sm">{turn.content}</p>
                    </Card>
                  </div>
                );
              })}
            </div>

            <div className="text-center pt-12 pb-24">
              <Button size="lg" variant="outline" onClick={() => setResult(null)}>
                NEW BATTLE
              </Button>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default VsBattlePage;
