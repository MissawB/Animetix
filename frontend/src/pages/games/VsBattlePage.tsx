import React, { useMemo, useState } from 'react';
import { Swords, Trophy, Loader2, AlertCircle, Heart, History, Flame, Search, X } from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { useQuery, useMutation } from '@tanstack/react-query';
import { vsBattleService } from '../../features/games/services/vsBattleService';
import { queryClient } from "../../utils/queryClient";

import { VsBattleArenaEntry, ArenaCharacter } from '../../types';
import { VsBattleResult } from '../../api';

const norm = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
type Slot = 'A' | 'B';

const slotTheme = (slot: Slot) => (slot === 'A'
  ? { ring: 'border-red-500', soft: 'border-red-500/20 bg-red-500/5', text: 'text-red-500', dot: 'bg-red-500' }
  : { ring: 'border-blue-500', soft: 'border-blue-500/20 bg-blue-500/5', text: 'text-blue-500', dot: 'bg-blue-500' });

const FighterSlot: React.FC<{
  slot: Slot;
  char: ArenaCharacter | null;
  active: boolean;
  onActivate: () => void;
  onClear: () => void;
}> = ({ slot, char, active, onActivate, onClear }) => {
  const t = slotTheme(slot);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onActivate}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onActivate(); } }}
      className={`relative w-full text-left rounded-[2rem] border-2 overflow-hidden transition-all aspect-[3/4] cursor-pointer ${
        active ? `${t.ring} shadow-2xl scale-[1.02]` : t.soft
      }`}
    >
      {char ? (
        <>
          <img src={char.image} alt={char.name} className="absolute inset-0 w-full h-full object-cover" loading="lazy" />
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="absolute top-3 right-3 z-10 w-8 h-8 grid place-items-center rounded-full bg-black/60 text-white hover:bg-red-600 transition-colors"
            aria-label="Retirer le combattant"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
            <p className="font-black italic manga-font uppercase text-white leading-tight text-base sm:text-lg break-words">{char.name}</p>
            <p className="text-[10px] font-black uppercase tracking-widest text-white/60 leading-snug break-words mt-1">{char.franchise}</p>
          </div>
        </>
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4 text-center">
          <div className={`w-14 h-14 rounded-2xl grid place-items-center ${t.soft} border-2 ${active ? t.ring : ''}`}>
            <Swords className={`w-7 h-7 ${t.text}`} />
          </div>
          <p className={`font-black italic uppercase ${t.text}`}>Challenger {slot}</p>
          <p className="text-[10px] font-bold uppercase tracking-widest opacity-40">
            {active ? 'Choisis ci-dessous' : 'Touche pour sélectionner'}
          </p>
        </div>
      )}
    </div>
  );
};

const VsBattlePage: React.FC = () => {
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
    queryFn: vsBattleService.getArenaFeed
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
    !!selectedA && !!selectedB &&
    selectedA.name === selectedB.name && selectedA.franchise === selectedB.franchise;

  const handleFight = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedA || !selectedB) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await vsBattleService.runBattle(selectedA.name, selectedB.name, selectedA.franchise, selectedB.franchise);
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['vs-arena-feed'] });
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'An error occurred during the battle.');
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
      <div className="max-w-5xl mx-auto px-6 py-16">
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

        <div className="space-y-16">

          {/* Selection / Result (centered) */}
          <div className="space-y-10">
            {!result ? (
              <form onSubmit={handleFight} className="space-y-10 animate-fade-in">
                {/* Fighter slots */}
                <div className="max-w-xl mx-auto">
                  <div className="grid grid-cols-2 gap-5 sm:gap-8 relative">
                    <div className={`hidden sm:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 w-14 h-14 rounded-full items-center justify-center border-4 border-black shadow-[0_0_30px_rgba(239,68,68,0.4)] ${isMirror ? 'bg-fuchsia-600' : 'bg-red-600'}`}>
                      <span className="text-xl font-black italic">VS</span>
                    </div>
                    <FighterSlot slot="A" char={selectedA} active={activeSlot === 'A'} onActivate={() => setActiveSlot('A')} onClear={() => { setSelectedA(null); setActiveSlot('A'); }} />
                    <FighterSlot slot="B" char={selectedB} active={activeSlot === 'B'} onActivate={() => setActiveSlot('B')} onClear={() => { setSelectedB(null); setActiveSlot('B'); }} />
                  </div>
                  {isMirror && (
                    <div className="mt-4 flex justify-center">
                      <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-fuchsia-500/15 border border-fuchsia-500/40 text-fuchsia-400 text-[10px] font-black uppercase tracking-[0.25em]">
                        <Swords className="w-3.5 h-3.5" /> Match miroir
                      </span>
                    </div>
                  )}
                </div>

                {/* Roster picker */}
                <div className="rounded-[2rem] border-2 border-white/5 bg-navy-900/40 p-5 md:p-6">
                  <div className="relative mb-4">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 pointer-events-none" />
                    <input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Rechercher un personnage ou une franchise…"
                      aria-label="Rechercher un personnage ou une franchise"
                      className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-black border-2 border-white/5 focus:border-red-500 outline-none font-bold transition-all placeholder:opacity-30"
                    />
                  </div>

                  {isCharsLoading ? (
                    <div className="flex items-center gap-3 justify-center py-10 opacity-50 font-black uppercase tracking-widest text-sm">
                      <Loader2 className="w-5 h-5 animate-spin" /> Chargement du roster…
                    </div>
                  ) : filtered.length === 0 ? (
                    <p className="text-center py-10 opacity-30 font-black italic uppercase">Aucun personnage trouvé</p>
                  ) : (
                    <div className="flex items-start gap-3 overflow-x-auto pb-3 -mx-1 px-1 snap-x [&::-webkit-scrollbar]:h-2.5 [&::-webkit-scrollbar-track]:bg-white/5 [&::-webkit-scrollbar-track]:rounded-full [&::-webkit-scrollbar-thumb]:bg-red-600/70 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-red-500 [scrollbar-width:thin] [scrollbar-color:rgb(220_38_38_/_0.7)_rgba(255,255,255,0.05)]">
                      {filtered.map((c) => {
                        const isA = selectedA?.name === c.name && selectedA?.franchise === c.franchise;
                        const isB = selectedB?.name === c.name && selectedB?.franchise === c.franchise;
                        const both = isA && isB;
                        return (
                          <button
                            type="button"
                            key={`${c.name}|${c.franchise}`}
                            onClick={() => pick(c)}
                            title={`${c.name} — ${c.franchise}`}
                            className={`group shrink-0 w-32 snap-start rounded-2xl overflow-hidden border-2 transition-all hover:scale-[1.03] bg-black/30 ${
                              both ? 'border-fuchsia-500 shadow-lg shadow-fuchsia-500/20'
                                : isA ? 'border-red-500 shadow-lg shadow-red-500/20'
                                : isB ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                                : 'border-white/5 hover:border-white/20'
                            }`}
                          >
                            <div className="relative aspect-[3/4] bg-navy-900">
                              <img src={c.image} alt={c.name} className="w-full h-full object-cover" loading="lazy" decoding="async" />
                              {c.source === 'synthetic' && (
                                <span className="absolute bottom-1.5 left-1.5 text-[8px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/70 text-white/70" title="Fiche générée par l'IA (pas de page VS Battles Wiki)">IA</span>
                              )}
                              {(isA || isB) && (
                                <div className="absolute top-1.5 right-1.5 flex gap-1">
                                  {isA && <span className="w-6 h-6 grid place-items-center rounded-full text-white text-[10px] font-black bg-red-600">A</span>}
                                  {isB && <span className="w-6 h-6 grid place-items-center rounded-full text-white text-[10px] font-black bg-blue-600">B</span>}
                                </div>
                              )}
                            </div>
                            <div className="p-2.5">
                              <p className="text-[11px] font-black italic uppercase leading-tight break-words text-white">{c.name}</p>
                              <p className="text-[8px] font-bold uppercase tracking-wider opacity-40 leading-snug break-words mt-1">{c.franchise}</p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  <p className="text-[10px] font-black uppercase tracking-widest opacity-30 mt-2 text-center">
                    {query ? `${filtered.length} résultat${filtered.length > 1 ? 's' : ''}` : 'Fais défiler le roster ou filtre par nom / franchise'}
                  </p>
                </div>

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
                        <div className="absolute inset-0 opacity-20 bg-cover bg-center grayscale group-hover:grayscale-0 transition-all duration-700" style={{ backgroundImage: `url(${char.image_url})` }} />
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

                <Card padding="lg" className="border-4 border-red-600/50 bg-navy-900 rounded-[4rem] relative overflow-hidden">
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

          {/* Arène Publique */}
          <section>
            <div className="flex items-center justify-center gap-3 mb-6">
              <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                <History className="w-4 h-4" /> Arène Publique
              </h3>
              <Badge variant="neutral" className="bg-red-500/10 text-red-500 border-red-500/20 text-[8px]">LIVE FEED</Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {isFeedLoading ? (
                [...Array(3)].map((_, i) => <CardSkeleton key={i} />)
              ) : arenaFeed?.map((battle: VsBattleArenaEntry) => (
                <Card key={battle.id} padding="md" className="bg-navy-900/50 border-white/5 hover:border-white/10 transition-all group">
                  <div className="flex justify-between items-start mb-4">
                    <div className="text-[10px] font-black uppercase opacity-30 italic">{new Date(battle.created_at).toLocaleDateString()}</div>
                    <button
                      type="button"
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
          </section>

          {/* Explication — comment fonctionne l'Arène */}
          <section className="rounded-[2.5rem] border-2 border-red-600/30 bg-gradient-to-br from-red-950/40 via-navy-900 to-navy-900 p-8 md:p-12">
            <div className="text-center mb-10">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-red-600/20 text-red-500 mb-4">
                <Flame className="w-7 h-7" />
              </div>
              <h2 className="text-2xl md:text-3xl font-black italic manga-font uppercase text-white">Comment fonctionne l'Arène</h2>
              <p className="text-sm font-bold opacity-50 uppercase tracking-[0.25em] mt-2">Un arbitre IA tranche n'importe quel duel</p>
            </div>

            <ol className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-3xl mx-auto">
              {[
                { t: 'Choisis ton premier combattant', d: 'Sélectionne un personnage dans le roster : il prend la place A.' },
                { t: 'Désigne l’adversaire', d: 'Filtre le roster par nom de personnage ou par franchise, puis remplis la place B.' },
                { t: 'Engage le duel', d: 'L’IA confronte le lore, les pouvoirs et les hauts faits des deux camps.' },
                { t: 'Découvre le verdict', d: 'Le vainqueur et son résumé s’affichent, puis le combat rejoint l’arène publique.' },
              ].map((step, i) => (
                <li key={step.t} className="flex gap-4 p-4 rounded-2xl bg-black/30 border border-white/5">
                  <span className="shrink-0 w-9 h-9 rounded-xl bg-red-600 text-white grid place-items-center font-black italic">{i + 1}</span>
                  <div>
                    <p className="font-black uppercase italic text-sm text-white leading-tight">{step.t}</p>
                    <p className="text-xs font-medium opacity-55 leading-snug mt-1">{step.d}</p>
                  </div>
                </li>
              ))}
            </ol>

            <p className="text-center text-[11px] font-black uppercase tracking-widest text-fuchsia-400/80 mt-8 flex items-center justify-center gap-2">
              <Swords className="w-3.5 h-3.5" /> Astuce : tu peux opposer un personnage à lui-même — c'est un match miroir.
            </p>
          </section>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VsBattlePage;
