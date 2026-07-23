import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { normalizeText as norm } from '../../utils/normalizeText';
import { Swords, Loader2, AlertCircle, CircleHelp, X } from 'lucide-react';
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
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    if (!showHelp) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowHelp(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [showHelp]);

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
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16">
          <header className="relative mb-16">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-44"
              aria-hidden
            />
            <div className="relative flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                闘
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                {t('games.vs_battle.tagline', "Défis Trans-Dimensionnels arbitrés par l'IA")}
              </span>
              <button
                type="button"
                onClick={() => setShowHelp(true)}
                className="ml-auto inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] bg-transparent cursor-pointer"
              >
                <CircleHelp className="h-4 w-4" aria-hidden="true" />
                {t('games.vs_battle.help_button', 'Comment ça marche')}
              </button>
            </div>
            <h1 className="font-manga relative mt-4 text-5xl md:text-8xl font-black italic tracking-tighter uppercase leading-none">
              ARENA{' '}
              <span className="bg-gradient-to-br from-[#FDB913] to-[#E8442B] bg-clip-text text-transparent">
                ULTIMATUM
              </span>
            </h1>
            <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
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
                        className={`hidden sm:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 h-14 w-14 -rotate-3 items-center justify-center rounded-[4px] border-2 bg-[#0B0C10] shadow-[0_0_30px_rgba(232,68,43,0.35)] ${
                          isMirror
                            ? 'border-[#FDB913] text-[#FDB913]'
                            : 'border-[#E8442B] text-[#E8442B]'
                        }`}
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
                        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FDB913]/10 border border-[#FDB913]/40 text-[#FDB913] text-[10px] font-black uppercase tracking-[0.25em]">
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
                    <div className="bg-[#E8442B]/10 text-[#E8442B] p-6 rounded-xl flex items-center justify-center gap-3 font-black uppercase italic border border-[#E8442B]/25">
                      <AlertCircle className="w-6 h-6" />
                      {error}
                    </div>
                  )}

                  <div className="flex justify-center">
                    <Button
                      type="submit"
                      size="lg"
                      disabled={isLoading || !selectedA || !selectedB}
                      className="!bg-gradient-to-br !from-[#FDB913] !to-[#E8442B] text-[#0B0C10] font-black text-2xl md:text-3xl italic uppercase px-12 md:px-16 py-8 md:py-10 rounded-2xl shadow-2xl shadow-[#E8442B]/20 hover:scale-105 transition-all border-none disabled:opacity-40 disabled:hover:scale-100"
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
          </div>
        </div>

        {/* Guide de l'arène : ouvert via le bouton "Comment ça marche" */}
        {showHelp && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t('games.vs_battle.how_title', "Comment fonctionne l'Arène")}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
          >
            <div className="relative w-full max-w-3xl max-h-[85vh] overflow-y-auto">
              <button
                type="button"
                onClick={() => setShowHelp(false)}
                aria-label={t('games.vs_battle.close_help', "Fermer l'aide")}
                className="absolute right-4 top-4 z-10 rounded-full p-2 text-white transition-colors hover:bg-white/10 bg-transparent border-none cursor-pointer"
              >
                <X className="h-6 w-6" />
              </button>
              <VsHowItWorks />
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default VsBattlePage;
