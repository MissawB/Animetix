import React, { useState, useRef, useEffect } from 'react';
import { Send, Trophy, Sparkles, Search, Flag, RotateCcw, Play, Clapperboard, BookOpen, Users, Gauge } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useEmoji } from '../../features/games/hooks/useEmoji';
import { emojiService, EmojiSuggestion } from '../../features/games/services/emojiService';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";


import { EmojiState } from "../../types";

const EmojiPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, starting, handleGuess, giveUp, start, reset } = useEmoji() as unknown as {
    gameState: EmojiState | undefined;
    starting: boolean;
    handleGuess: (arg: { guess: string }) => Promise<void>;
    giveUp: () => void;
    start: (mediaType?: string, difficulty?: string) => void;
    reset: () => void;
  };
  const [guess, setGuess] = useState<string>('');
  const [suggestions, setSuggestions] = useState<EmojiSuggestion[]>([]);
  const [showSug, setShowSug] = useState(false);
  const [mediaType, setMediaType] = useState<string>('Anime');
  const [difficulty, setDifficulty] = useState<string>('Normal');
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reqIdRef = useRef(0);

  const MEDIA_OPTS = [
    { key: 'Anime', label: t('games.emoji.media.anime', 'Animés'), icon: Clapperboard },
    { key: 'Manga', label: t('games.emoji.media.manga', 'Mangas'), icon: BookOpen },
    { key: 'Character', label: t('games.emoji.media.character', 'Personnages'), icon: Users },
  ] as const;

  const DIFF_OPTS = [
    { key: 'Easy', label: t('games.emoji.difficulties.easy.label', 'Facile'), hint: t('games.emoji.difficulties.easy.hint', 'Œuvres très connues') },
    { key: 'Normal', label: t('games.emoji.difficulties.normal.label', 'Normal'), hint: t('games.emoji.difficulties.normal.hint', 'Un bon mix') },
    { key: 'Hard', label: t('games.emoji.difficulties.hard.label', 'Difficile'), hint: t('games.emoji.difficulties.hard.hint', 'Titres plus pointus') },
    { key: 'Impossible', label: t('games.emoji.difficulties.impossible.label', 'Extrême'), hint: t('games.emoji.difficulties.impossible.hint', 'Pépites obscures') },
  ] as const;

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

  // ── Écran de chargement (partie en cours de création) ──────────────────
  if (starting && !gameState) return (
    <div className="flex justify-center items-center py-12 px-6">
      <CardSkeleton />
    </div>
  );

  // ── Écran de choix : type d'œuvre + difficulté ─────────────────────────
  if (!gameState) {
    return (
      <div className="max-w-3xl mx-auto p-6 py-16 text-center">
        <h2 className="text-5xl font-black italic manga-font mb-3 tracking-tighter uppercase">
          {t('games.emoji.title_part1', 'EMOJI')} <span className="text-orange-500">{t('games.emoji.title_part2', 'DECODE')}</span>
        </h2>
        <p className="text-sm font-bold opacity-50 mb-12">{t('games.emoji.subtitle', "Devine l'œuvre cachée derrière une suite d'emojis, du plus vague au plus évident.")}</p>

        <div className="text-left mb-10">
          <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] opacity-40 mb-4">
            <Sparkles className="w-3.5 h-3.5" /> {t('games.emoji.section_media', "1 · Type d'œuvre")}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {MEDIA_OPTS.map(({ key, label, icon: Icon }) => {
              const active = mediaType === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setMediaType(key)}
                  className={`flex flex-col items-center gap-2 rounded-2xl border-2 p-5 font-black uppercase italic manga-font transition-all ${
                    active
                      ? 'border-orange-500 bg-orange-500/10 text-orange-500 scale-[1.02]'
                      : 'border-black/10 dark:border-white/10 hover:border-orange-500/40'
                  }`}
                >
                  <Icon className="w-7 h-7" />
                  <span className="text-lg">{label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="text-left mb-12">
          <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] opacity-40 mb-4">
            <Gauge className="w-3.5 h-3.5" /> {t('games.emoji.section_difficulty', '2 · Difficulté')}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DIFF_OPTS.map(({ key, label, hint }) => {
              const active = difficulty === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setDifficulty(key)}
                  className={`rounded-2xl border-2 p-4 text-center transition-all ${
                    active
                      ? 'border-orange-500 bg-orange-500/10 scale-[1.02]'
                      : 'border-black/10 dark:border-white/10 hover:border-orange-500/40'
                  }`}
                >
                  <div className={`font-black uppercase italic manga-font ${active ? 'text-orange-500' : ''}`}>{label}</div>
                  <div className="text-[10px] font-bold opacity-40 mt-1 leading-tight">{hint}</div>
                </button>
              );
            })}
          </div>
        </div>

        <Button
          variant="primary"
          size="lg"
          onClick={() => start(mediaType, difficulty)}
          className="bg-black text-white hover:bg-gray-900 border-none px-16"
        >
          <Play className="w-5 h-5" /> {t('games.emoji.start', 'COMMENCER')}
        </Button>
      </div>
    );
  }

  // Défensif : d'anciennes sessions renvoyaient `emojis` en chaîne (non-array).
  const revealed: string[] = Array.isArray(gameState.emojis) ? gameState.emojis : [];
  const totalEmojis = gameState.total_emojis || revealed.length;
  // Victoire = au moins une tentative correcte ; sinon la partie a été abandonnée.
  const won = (gameState.guesses || []).some((g) => g.is_correct);
  const replay = () => { start(gameState.media_type, gameState.difficulty); setGuess(''); };

  return (

      <div className="max-w-4xl mx-auto p-6 text-center py-16">
        <h2 className="text-5xl font-black italic manga-font mb-12 tracking-tighter uppercase">
          {t('games.emoji.title_part1', 'EMOJI')} <span className="text-orange-500">{t('games.emoji.title_part2', 'DECODE')}</span>
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
              <Sparkles className="w-4 h-4" /> {t('games.emoji.hint_progression', 'Du plus vague au plus évident — un nouvel indice à chaque essai raté.')}
          </p>
          {totalEmojis > 0 && (
            <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-60 mt-3">
              {t('games.emoji.hint_counter', { defaultValue: 'Indice {{current}} / {{total}}', current: Math.min(revealed.length, totalEmojis), total: totalEmojis })}
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
                placeholder={t('games.emoji.input_placeholder', 'Cherchez un titre…')}
                aria-label={t('games.emoji.input_aria', 'Rechercher un titre')}
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
                <Send className="w-5 h-5" /> {t('games.emoji.guess', 'DEVINER')}
              </Button>
              <button
                type="button"
                onClick={() => giveUp()}
                className="flex items-center justify-center gap-2 rounded-2xl px-6 py-3 font-black uppercase tracking-wide text-sm text-red-500 border border-red-500/30 bg-red-500/5 hover:bg-red-500/15 hover:border-red-500/60 transition-colors whitespace-nowrap"
              >
                <Flag className="w-4 h-4" /> {t('games.emoji.give_up', 'Abandonner')}
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
                {won ? t('games.emoji.victory', 'VICTOIRE !') : t('games.emoji.abandoned', 'Partie abandonnée')}
              </h3>
              <p className="text-lg md:text-xl font-bold opacity-90">
                {t('games.emoji.answer_was', 'La réponse était')} <span className="text-yellow-300">{gameState.secret_title}</span>
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  variant="ghost"
                  className="bg-white/95 text-slate-900 hover:bg-white border-none px-10 font-black"
                  onClick={replay}
                >
                  <RotateCcw className="w-5 h-5" /> {t('games.emoji.replay', 'REJOUER')}
                </Button>
                <button
                  type="button"
                  onClick={() => { reset(); setGuess(''); }}
                  className="rounded-2xl px-8 py-3 font-black uppercase tracking-wide text-sm text-white/90 border border-white/30 hover:bg-white/10 transition-colors"
                >
                  {t('games.emoji.change_mode', 'Changer de mode')}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-3 mt-12">
          {gameState.guesses.length > 0 && (
            <h4 className="text-[10px] font-black uppercase opacity-30 tracking-[0.3em] mb-6">{t('games.emoji.your_attempts', 'Tes tentatives')}</h4>
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
                    {g.is_correct ? t('games.emoji.result_found', 'TROUVÉ') : t('games.emoji.result_failed', 'ÉCHEC')}
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
