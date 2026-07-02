import React, { useState, useRef, useEffect } from 'react';
import { Send, Trophy, Sparkles, Search, Flag, RotateCcw } from 'lucide-react';
import { useEmoji } from '../../features/games/hooks/useEmoji';
import { emojiService, EmojiSuggestion } from '../../features/games/services/emojiService';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";


import { EmojiState } from "../../types";

const EmojiPage: React.FC = () => {
  const { gameState, loading, handleGuess, giveUp, restart } = useEmoji() as unknown as {
    gameState: EmojiState | undefined;
    loading: boolean;
    handleGuess: (arg: { guess: string }) => Promise<void>;
    giveUp: () => void;
    restart: () => void;
  };
  const [guess, setGuess] = useState<string>('');
  const [suggestions, setSuggestions] = useState<EmojiSuggestion[]>([]);
  const [showSug, setShowSug] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reqIdRef = useRef(0);

  useEffect(() => () => { if (debounceRef.current) clearTimeout(debounceRef.current); }, []);

  const onChange = (val: string) => {
    setGuess(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = val.trim();
    if (q.length < 2) { setSuggestions([]); setShowSug(false); return; }
    debounceRef.current = setTimeout(async () => {
      const rid = ++reqIdRef.current;
      const res = await emojiService.suggest(q).catch(() => [] as EmojiSuggestion[]);
      if (rid !== reqIdRef.current) return; // ignore stale responses
      setSuggestions(res);
      setShowSug(res.length > 0);
    }, 90);
  };

  const onSubmit = async (value?: string) => {
    const g = (value ?? guess).trim();
    if (!g) return;
    setShowSug(false);
    setSuggestions([]);
    setGuess('');
    try {
      await handleGuess({ guess: g });
    } catch {
      // titre hors catalogue → déjà signalé par un toast
    }
    inputRef.current?.focus();
  };

  if (loading) return (
    <div className="flex justify-center items-center py-12 px-6">
      <CardSkeleton />
    </div>
  );
  
  if (!gameState) return null;

  // Défensif : d'anciennes sessions renvoyaient `emojis` en chaîne (non-array).
  const revealed: string[] = Array.isArray(gameState.emojis) ? gameState.emojis : [];
  const totalEmojis = gameState.total_emojis || revealed.length;
  // Victoire = au moins une tentative correcte ; sinon la partie a été abandonnée.
  const won = (gameState.guesses || []).some((g) => g.is_correct);

  return (
    
      <div className="max-w-4xl mx-auto p-6 text-center py-16">
        <h2 className="text-5xl font-black italic manga-font mb-12 tracking-tighter uppercase">
          EMOJI <span className="text-orange-500">DECODE</span>
        </h2>
        
        <Card padding="lg" className="bg-gradient-to-r from-orange-500 to-red-600 mb-12 text-white border-none relative overflow-hidden group">
          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          <div className="text-6xl md:text-8xl tracking-[0.3em] mb-6 flex flex-wrap justify-center items-center gap-2 drop-shadow-lg min-h-[6rem]">
              {revealed.map((e, i) => (
                <span key={i} className="animate-in fade-in zoom-in duration-500">{e}</span>
              ))}
              {Array.from({ length: Math.max(0, totalEmojis - revealed.length) }).map((_, i) => (
                <span key={`h-${i}`} className="opacity-25 select-none">◻️</span>
              ))}
          </div>
          <p className="font-black italic text-sm uppercase tracking-widest opacity-80 flex items-center justify-center gap-2">
              <Sparkles className="w-4 h-4" /> Du plus vague au plus évident — un nouvel indice à chaque essai raté.
          </p>
          {totalEmojis > 0 && (
            <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-60 mt-3">
              Indice {Math.min(revealed.length, totalEmojis)} / {totalEmojis}
            </p>
          )}
        </Card>

        {!gameState.game_over ? (
          <div className="max-w-md mx-auto space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 pointer-events-none" />
              <input
                ref={inputRef}
                type="text"
                value={guess}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); onSubmit(); } if (e.key === 'Escape') setShowSug(false); }}
                onFocus={() => { if (suggestions.length) setShowSug(true); }}
                onBlur={() => setTimeout(() => setShowSug(false), 150)}
                placeholder="Cherchez un titre…"
                aria-label="Rechercher un titre"
                autoComplete="off"
                className="w-full rounded-2xl border border-black/10 dark:border-white/10 bg-surface-card py-3.5 pl-12 pr-4 text-center font-bold outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/30 transition-all"
              />
            </div>

            {/* Liste en flux normal : elle repousse le bouton vers le bas au lieu
                de le recouvrir (plus de chevauchement avec DEVINER). */}
            {showSug && suggestions.length > 0 && (
              <ul className="max-h-80 overflow-y-auto rounded-2xl border border-black/10 dark:border-white/10 bg-surface-card shadow-xl text-left divide-y divide-black/5 dark:divide-white/5">
                {suggestions.map((s, i) => (
                  <li key={`${s.title}-${i}`}>
                    <button
                      type="button"
                      onMouseDown={(e) => { e.preventDefault(); onSubmit(s.title); }}
                      className="flex w-full items-center gap-3 px-3 py-2.5 hover:bg-orange-500/10 transition-colors"
                    >
                      {s.image ? (
                        <img src={s.image} alt="" loading="lazy" decoding="async"
                          className="h-14 w-10 flex-shrink-0 rounded-lg object-cover shadow-sm" />
                      ) : (
                        <div className="h-14 w-10 flex-shrink-0 rounded-lg bg-black/5 dark:bg-white/5" />
                      )}
                      <div className="min-w-0 flex-grow">
                        <div className="truncate font-black italic manga-font leading-tight">
                          {s.title_english || s.title}
                        </div>
                        {s.title_native && (
                          <div className="truncate text-xs text-surface-text/45">{s.title_native}</div>
                        )}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <Button variant="primary" size="lg" fullWidth onClick={() => onSubmit()} className="bg-black text-white hover:bg-gray-900 border-none">
                <Send className="w-5 h-5" /> DEVINER
              </Button>
              <button
                type="button"
                onClick={() => giveUp()}
                className="flex items-center justify-center gap-2 rounded-2xl px-6 py-3 font-black uppercase tracking-wide text-sm text-red-500 border border-red-500/30 bg-red-500/5 hover:bg-red-500/15 hover:border-red-500/60 transition-colors whitespace-nowrap"
              >
                <Flag className="w-4 h-4" /> Abandonner
              </button>
            </div>
          </div>
        ) : (
          <div className={`mb-12 rounded-3xl p-8 md:p-10 text-white shadow-2xl relative overflow-hidden bg-gradient-to-br ${won ? 'from-emerald-500 to-green-600' : 'from-slate-700 to-slate-900'}`}>
            <div className="absolute -top-8 -right-8 opacity-10">
              {won ? <Trophy className="w-40 h-40" /> : <Flag className="w-40 h-40" />}
            </div>
            <div className="relative">
              {won ? <Trophy className="w-14 h-14 mx-auto mb-3" /> : <Flag className="w-14 h-14 mx-auto mb-3" />}
              <h3 className="text-4xl md:text-5xl font-black italic manga-font mb-3 uppercase tracking-tighter">
                {won ? 'VICTOIRE !' : 'Partie abandonnée'}
              </h3>
              <p className="text-lg md:text-xl font-bold opacity-90">
                La réponse était <span className="text-yellow-300">{gameState.secret_title}</span>
              </p>
              <Button
                variant="ghost"
                className="mt-8 bg-white/95 text-slate-900 hover:bg-white border-none px-10 font-black"
                onClick={() => { restart(); setGuess(''); }}
              >
                <RotateCcw className="w-5 h-5" /> REJOUER
              </Button>
            </div>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-3 mt-12">
          {gameState.guesses.length > 0 && (
            <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em] mb-6">Tes tentatives</h4>
          )}
          {gameState.guesses.map((g: { title: string; title_en?: string; image: string; is_correct: boolean }, i: number) => (
            <div
              key={i}
              className={`flex items-center gap-4 rounded-2xl p-3 border-l-4 transition-all hover:translate-x-1 ${
                g.is_correct
                  ? 'border-green-500 bg-green-500/10'
                  : 'border-red-500/60 bg-red-500/5'
              }`}
            >
              <img src={g.image} className="w-12 h-16 object-cover rounded-xl shadow-md flex-shrink-0" alt="" loading="lazy" decoding="async" />
              <div className="flex-grow text-left min-w-0">
                <div className="font-black text-base truncate uppercase italic manga-font leading-tight mb-1.5">{g.title_en || g.title}</div>
                <Badge variant={g.is_correct ? 'success' : 'danger'}>
                    {g.is_correct ? 'TROUVÉ' : 'ÉCHEC'}
                </Badge>
              </div>
              <div className="text-2xl px-2 flex-shrink-0">{g.is_correct ? '✅' : '❌'}</div>
            </div>
          ))}
        </div>
      </div>
    
  );
};

export default EmojiPage;


