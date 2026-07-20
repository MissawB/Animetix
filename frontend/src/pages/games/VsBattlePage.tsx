import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { normalizeText as norm } from '../../utils/normalizeText';
import { Swords, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useQuery, useMutation } from '@tanstack/react-query';
import { vsBattleService } from '../../features/games/services/vsBattleService';
import { queryClient } from '../../utils/queryClient';
import { VsBattleArenaEntry, ArenaCharacter, VsBattleResult } from '../../types';
import { FighterSlot, Slot } from './components/FighterSlot';
import { VsRosterPicker } from './components/VsRosterPicker';
import { VsBattleResult as VsBattleResultView } from './components/VsBattleResult';
import { VsArenaFeed } from './components/VsArenaFeed';
import { VsHowItWorks } from './components/VsHowItWorks';

const VsBattlePage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedA, setSelectedA] = useState<ArenaCharacter | null>(null);
  const [selectedB, setSelectedB] = useState<ArenaCharacter | null>(null);
  const [activeSlot, setActiveSlot] = useState<Slot>('A');
  const [query, setQuery] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VsBattleResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: characters = [], isLoading: isCharsLoading } = useQuery<ArenaCharacter[]>({
    queryKey: ['vs-characters'],
    queryFn: vsBattleService.getCharacters,
    staleTime: 10 * 60 * 1000,
  });

  const { data: arenaFeed, isLoading: isFeedLoading } = useQuery<VsBattleArenaEntry[]>({
    queryKey: ['vs-arena-feed'],
    queryFn: vsBattleService.getArenaFeed,
  });

  const likeMutation = useMutation({
    mutationFn: (id: number) => vsBattleService.likeBattle(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vs-arena-feed'] }),
  });

  // Filter by character name OR franchise (accent/case-insensitive).
  const filtered = useMemo(() => {
    const q = norm(query.trim());
    const list = q
      ? characters.filter((c) => norm(c.name).includes(q) || norm(c.franchise).includes(q))
      : characters;
    return list.slice(0, 120);
  }, [characters, query]);

  const pick = (c: ArenaCharacter) => {
    if (activeSlot === 'A') {
      setSelectedA(c);
      if (!selectedB) setActiveSlot('B');
    } else {
      setSelectedB(c);
      if (!selectedA) setActiveSlot('A');
    }
  };

  // Mirror match (same fighter on both sides) is allowed — just flag it visually.
  const isMirror =
    !!selectedA &&
    !!selectedB &&
    selectedA.name === selectedB.name &&
    selectedA.franchise === selectedB.franchise;

  const handleFight = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedA || !selectedB) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await vsBattleService.runBattle(
        selectedA.name,
        selectedB.name,
        selectedA.franchise,
        selectedB.franchise,
      );
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['vs-arena-feed'] });
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'An error occurred during the battle.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-5xl mx-auto px-6 py-16">
        <header className="text-center mb-16 relative">
          <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-10">
            <Swords className="w-40 h-40" />
          </div>
          <h1 className="text-5xl md:text-8xl font-black italic manga-font tracking-tighter uppercase mb-4 relative z-10">
            ARENA <span className="text-red-500 text-glow">ULTIMATUM</span>
          </h1>
          <p className="text-xl font-bold opacity-40 uppercase tracking-[0.4em] relative z-10">
            {t('games.vs_battle.tagline', "Défis Trans-Dimensionnels arbitrés par l'IA")}
          </p>
        </header>

        <div className="space-y-16">
          {/* Selection / Result (centered) */}
          <div className="space-y-10">
            {!result ? (
              <form onSubmit={handleFight} className="space-y-10 animate-fade-in">
                {/* Fighter slots */}
                <div className="max-w-xl mx-auto">
                  <div className="grid grid-cols-2 gap-5 sm:gap-8 relative">
                    <div
                      className={`hidden sm:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 w-14 h-14 rounded-full items-center justify-center border-4 border-black shadow-[0_0_30px_rgba(239,68,68,0.4)] ${isMirror ? 'bg-fuchsia-600' : 'bg-red-600'}`}
                    >
                      <span className="text-xl font-black italic">VS</span>
                    </div>
                    <FighterSlot
                      slot="A"
                      char={selectedA}
                      active={activeSlot === 'A'}
                      onActivate={() => setActiveSlot('A')}
                      onClear={() => {
                        setSelectedA(null);
                        setActiveSlot('A');
                      }}
                    />
                    <FighterSlot
                      slot="B"
                      char={selectedB}
                      active={activeSlot === 'B'}
                      onActivate={() => setActiveSlot('B')}
                      onClear={() => {
                        setSelectedB(null);
                        setActiveSlot('B');
                      }}
                    />
                  </div>
                  {isMirror && (
                    <div className="mt-4 flex justify-center">
                      <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-fuchsia-500/15 border border-fuchsia-500/40 text-fuchsia-400 text-[10px] font-black uppercase tracking-[0.25em]">
                        <Swords className="w-3.5 h-3.5" />{' '}
                        {t('games.vs_battle.mirror_match', 'Match miroir')}
                      </span>
                    </div>
                  )}
                </div>

                <VsRosterPicker
                  query={query}
                  onQueryChange={setQuery}
                  isLoading={isCharsLoading}
                  filtered={filtered}
                  selectedA={selectedA}
                  selectedB={selectedB}
                  onPick={pick}
                />

                {error && (
                  <div className="bg-red-500/10 text-red-500 p-6 rounded-2xl flex items-center justify-center gap-3 font-black uppercase italic border border-red-500/20">
                    <AlertCircle className="w-6 h-6" />
                    {error}
                  </div>
                )}

                <div className="text-center">
                  <Button
                    type="submit"
                    size="lg"
                    disabled={isLoading || !selectedA || !selectedB}
                    className="bg-red-600 hover:bg-red-500 text-white font-black text-2xl md:text-3xl italic uppercase px-12 md:px-16 py-8 md:py-10 rounded-[2.5rem] shadow-2xl hover:scale-105 transition-all border-none disabled:opacity-40 disabled:hover:scale-100"
                  >
                    {isLoading ? (
                      <span className="flex items-center gap-4">
                        <Loader2 className="w-8 h-8 animate-spin" />{' '}
                        {t('games.vs_battle.syncing_lore', 'SYNCHRONISATION DU LORE...')}
                      </span>
                    ) : (
                      <span className="flex items-center gap-4">
                        <Swords className="w-8 h-8" />{' '}
                        {t('games.vs_battle.engage', 'ENGAGER LE DUEL')}
                      </span>
                    )}
                  </Button>
                </div>
              </form>
            ) : (
              <VsBattleResultView result={result} onReset={() => setResult(null)} />
            )}
          </div>

          <VsArenaFeed
            feed={arenaFeed}
            isLoading={isFeedLoading}
            onLike={(id) => likeMutation.mutate(id)}
          />

          <VsHowItWorks />
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VsBattlePage;
