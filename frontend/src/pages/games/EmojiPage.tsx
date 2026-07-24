import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Trophy,
  Sparkles,
  Search,
  Flag,
  RotateCcw,
  Play,
  Clapperboard,
  BookOpen,
  Users,
  Gauge,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useEmoji } from '../../features/games/hooks/useEmoji';
import { emojiService, EmojiSuggestion } from '../../features/games/services/emojiService';
import { CardSkeleton } from '../../components/ui/Skeleton';

import { EmojiState } from '../../types';

const ACTIVE_SEL = 'border-[#FDB913] bg-[#FDB913]/10';
const IDLE_SEL = 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50';
const SHU_CTA =
  'inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-8 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';

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
    {
      key: 'Easy',
      label: t('games.emoji.difficulties.easy.label', 'Facile'),
      hint: t('games.emoji.difficulties.easy.hint', 'Œuvres très connues'),
    },
    {
      key: 'Normal',
      label: t('games.emoji.difficulties.normal.label', 'Normal'),
      hint: t('games.emoji.difficulties.normal.hint', 'Un bon mix'),
    },
    {
      key: 'Hard',
      label: t('games.emoji.difficulties.hard.label', 'Difficile'),
      hint: t('games.emoji.difficulties.hard.hint', 'Titres plus pointus'),
    },
    {
      key: 'Impossible',
      label: t('games.emoji.difficulties.impossible.label', 'Extrême'),
      hint: t('games.emoji.difficulties.impossible.hint', 'Pépites obscures'),
    },
  ] as const;

  useEffect(
    () => () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    },
    [],
  );

  const onChange = (val: string) => {
    setGuess(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = val.trim();
    if (q.length < 2) {
      setSuggestions([]);
      setShowSug(false);
      return;
    }
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
  if (starting && !gameState)
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-12 px-6">
        <CardSkeleton />
      </div>
    );

  // ── Écran de choix : type d'œuvre + difficulté ─────────────────────────
  if (!gameState) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-3xl mx-auto p-6 py-16 text-center">
          <div className="relative inline-flex items-center gap-3 mb-6">
            <span className="explore-stamp -rotate-2" aria-hidden>
              符
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              Emoji Decode
            </span>
          </div>
          <h2 className="font-manga text-5xl font-black italic uppercase mb-3 tracking-tighter text-[#F4F1E8]">
            {t('games.emoji.title_part1', 'EMOJI')}{' '}
            <span className="text-[#E8442B]">{t('games.emoji.title_part2', 'DECODE')}</span>
          </h2>
          <p className="text-sm font-bold text-[#8F94A5] mb-12">
            {t(
              'games.emoji.subtitle',
              "Devine l'œuvre cachée derrière une suite d'emojis, du plus vague au plus évident.",
            )}
          </p>

          <div className="text-left mb-10">
            <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] text-[#8F94A5] mb-4">
              <Sparkles className="w-3.5 h-3.5" />{' '}
              {t('games.emoji.section_media', "1 · Type d'œuvre")}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {MEDIA_OPTS.map(({ key, label, icon: Icon }) => {
                const active = mediaType === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setMediaType(key)}
                    className={`flex flex-col items-center gap-2 rounded-2xl border-2 p-5 font-manga font-black uppercase italic transition-colors ${
                      active ? `${ACTIVE_SEL} text-[#FDB913]` : `${IDLE_SEL} text-[#F4F1E8]`
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
            <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] text-[#8F94A5] mb-4">
              <Gauge className="w-3.5 h-3.5" />{' '}
              {t('games.emoji.section_difficulty', '2 · Difficulté')}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {DIFF_OPTS.map(({ key, label, hint }) => {
                const active = difficulty === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setDifficulty(key)}
                    className={`rounded-2xl border-2 p-4 text-center transition-colors ${
                      active ? ACTIVE_SEL : IDLE_SEL
                    }`}
                  >
                    <div
                      className={`font-manga font-black uppercase italic ${active ? 'text-[#FDB913]' : 'text-[#F4F1E8]'}`}
                    >
                      {label}
                    </div>
                    <div className="text-[10px] font-bold text-[#8F94A5] mt-1 leading-tight">
                      {hint}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="button"
            onClick={() => start(mediaType, difficulty)}
            className={`${SHU_CTA} px-16`}
          >
            <Play className="w-5 h-5" /> {t('games.emoji.start', 'COMMENCER')}
          </button>
        </div>
      </div>
    );
  }

  // Défensif : d'anciennes sessions renvoyaient `emojis` en chaîne (non-array).
  const revealed: string[] = Array.isArray(gameState.emojis) ? gameState.emojis : [];
  const totalEmojis = gameState.total_emojis || revealed.length;
  // Victoire = au moins une tentative correcte ; sinon la partie a été abandonnée.
  const won = (gameState.guesses || []).some((g) => g.is_correct);
  const replay = () => {
    start(gameState.media_type, gameState.difficulty);
    setGuess('');
  };

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-4xl mx-auto p-6 text-center py-16">
        <h2 className="font-manga text-5xl font-black italic uppercase mb-12 tracking-tighter text-[#F4F1E8] flex items-center justify-center gap-3">
          <span className="explore-stamp -rotate-2" aria-hidden>
            符
          </span>
          {t('games.emoji.title_part1', 'EMOJI')}{' '}
          <span className="text-[#E8442B]">{t('games.emoji.title_part2', 'DECODE')}</span>
        </h2>

        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-10 mb-12 relative overflow-hidden">
          <div className="text-6xl md:text-8xl tracking-[0.3em] mb-6 flex flex-wrap justify-center items-center gap-2 min-h-[6rem]">
            {revealed.map((e, i) => (
              <span key={i} className="animate-in fade-in zoom-in duration-500">
                {e}
              </span>
            ))}
            {Array.from({ length: Math.max(0, totalEmojis - revealed.length) }).map((_, i) => (
              <span key={`h-${i}`} className="opacity-20 select-none">
                ◻️
              </span>
            ))}
          </div>
          <p className="font-black italic text-sm uppercase tracking-widest text-[#8F94A5] flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-[#FDB913]" />{' '}
            {t(
              'games.emoji.hint_progression',
              'Du plus vague au plus évident — un nouvel indice à chaque essai raté.',
            )}
          </p>
          {totalEmojis > 0 && (
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FDB913] mt-3">
              {t('games.emoji.hint_counter', {
                defaultValue: 'Indice {{current}} / {{total}}',
                current: Math.min(revealed.length, totalEmojis),
                total: totalEmojis,
              })}
            </p>
          )}
        </div>

        {!gameState.game_over ? (
          <div className="max-w-md mx-auto space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8F94A5]/50 pointer-events-none" />
              <input
                ref={inputRef}
                type="text"
                value={guess}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    onSubmit();
                  }
                  if (e.key === 'Escape') setShowSug(false);
                }}
                onFocus={() => {
                  if (suggestions.length) setShowSug(true);
                }}
                onBlur={() => setTimeout(() => setShowSug(false), 150)}
                placeholder={t('games.emoji.input_placeholder', 'Cherchez un titre…')}
                aria-label={t('games.emoji.input_aria', 'Rechercher un titre')}
                autoComplete="off"
                className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0F1016] py-3.5 pl-12 pr-4 text-center font-bold text-[#F4F1E8] outline-none focus:border-[#FDB913] transition-colors placeholder:text-[#8F94A5]/60"
              />
            </div>

            {/* Liste en flux normal : elle repousse le bouton vers le bas au lieu
                de le recouvrir (plus de chevauchement avec DEVINER). */}
            {showSug && suggestions.length > 0 && (
              <ul className="max-h-80 overflow-y-auto rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] shadow-xl text-left divide-y divide-[#F4F1E8]/5">
                {suggestions.map((s, i) => (
                  <li key={`${s.title}-${i}`}>
                    <button
                      type="button"
                      onMouseDown={(e) => {
                        e.preventDefault();
                        onSubmit(s.title);
                      }}
                      className="flex w-full items-center gap-3 px-3 py-2.5 hover:bg-[#FDB913]/10 transition-colors"
                    >
                      {s.image ? (
                        <img
                          src={s.image}
                          alt=""
                          loading="lazy"
                          decoding="async"
                          className="h-14 w-10 flex-shrink-0 rounded-lg object-cover shadow-sm"
                        />
                      ) : (
                        <div className="h-14 w-10 flex-shrink-0 rounded-lg bg-[#F4F1E8]/5" />
                      )}
                      <div className="min-w-0 flex-grow">
                        <div className="truncate font-manga font-black italic uppercase leading-tight text-[#F4F1E8]">
                          {s.title_english || s.title}
                        </div>
                        {s.title_native && (
                          <div className="truncate text-xs text-[#8F94A5]/70">{s.title_native}</div>
                        )}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <button type="button" onClick={() => onSubmit()} className={`${SHU_CTA} flex-1`}>
                <Send className="w-5 h-5" /> {t('games.emoji.guess', 'DEVINER')}
              </button>
              <button
                type="button"
                onClick={() => giveUp()}
                className="flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-black uppercase tracking-wide text-sm text-[#E8442B] border border-[#E8442B]/30 bg-[#E8442B]/5 hover:bg-[#E8442B]/15 hover:border-[#E8442B]/60 transition-colors whitespace-nowrap"
              >
                <Flag className="w-4 h-4" /> {t('games.emoji.give_up', 'Abandonner')}
              </button>
            </div>
          </div>
        ) : (
          <div
            className={`mb-12 rounded-2xl p-8 md:p-10 relative overflow-hidden border-2 bg-[#0F1016] ${won ? 'border-[#FDB913]/40' : 'border-[#E8442B]/40'}`}
          >
            <div className="absolute -top-8 -right-8 opacity-[0.06]">
              {won ? (
                <Trophy className="w-40 h-40 text-[#FDB913]" />
              ) : (
                <Flag className="w-40 h-40 text-[#E8442B]" />
              )}
            </div>
            <div className="relative">
              {won ? (
                <Trophy className="w-14 h-14 mx-auto mb-3 text-[#FDB913]" />
              ) : (
                <Flag className="w-14 h-14 mx-auto mb-3 text-[#E8442B]" />
              )}
              <h3
                className={`font-manga text-4xl md:text-5xl font-black italic uppercase mb-3 tracking-tighter ${won ? 'text-[#FDB913]' : 'text-[#E8442B]'}`}
              >
                {won
                  ? t('games.emoji.victory', 'VICTOIRE !')
                  : t('games.emoji.abandoned', 'Partie abandonnée')}
              </h3>
              <p className="text-lg md:text-xl font-bold text-[#F4F1E8]/85">
                {t('games.emoji.answer_was', 'La réponse était')}{' '}
                <span className="text-[#FDB913]">{gameState.secret_title}</span>
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
                <button type="button" onClick={replay} className={SHU_CTA}>
                  <RotateCcw className="w-5 h-5" /> {t('games.emoji.replay', 'REJOUER')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    reset();
                    setGuess('');
                  }}
                  className="rounded-xl px-8 py-3 font-black uppercase tracking-wide text-sm text-[#8F94A5] border border-[#F4F1E8]/15 hover:border-[#FDB913] hover:text-[#F4F1E8] transition-colors"
                >
                  {t('games.emoji.change_mode', 'Changer de mode')}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-3 mt-12">
          {gameState.guesses.length > 0 && (
            <h4 className="text-[10px] font-black uppercase text-[#8F94A5]/60 tracking-[0.3em] mb-6">
              {t('games.emoji.your_attempts', 'Tes tentatives')}
            </h4>
          )}
          {gameState.guesses.map(
            (
              g: { title: string; title_en?: string; image: string; is_correct: boolean },
              i: number,
            ) => (
              <div
                key={i}
                className={`flex items-center gap-4 rounded-2xl p-3 border-l-4 bg-[#0F1016] transition-all hover:translate-x-1 ${
                  g.is_correct ? 'border-[#FDB913]' : 'border-[#E8442B]/70'
                }`}
              >
                <img
                  src={g.image}
                  className="w-12 h-16 object-cover rounded-xl shadow-md flex-shrink-0"
                  alt=""
                  loading="lazy"
                  decoding="async"
                />
                <div className="flex-grow text-left min-w-0">
                  <div className="font-manga font-black text-base truncate uppercase italic leading-tight mb-1.5 text-[#F4F1E8]">
                    {g.title_en || g.title}
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase inline-flex items-center gap-1 border ${g.is_correct ? 'bg-[#FDB913]/10 text-[#FDB913] border-[#FDB913]/20' : 'bg-[#E8442B]/10 text-[#E8442B] border-[#E8442B]/20'}`}
                  >
                    {g.is_correct
                      ? t('games.emoji.result_found', 'TROUVÉ')
                      : t('games.emoji.result_failed', 'ÉCHEC')}
                  </span>
                </div>
                <div className="text-2xl px-2 flex-shrink-0">{g.is_correct ? '✅' : '❌'}</div>
              </div>
            ),
          )}
        </div>
      </div>
    </div>
  );
};

export default EmojiPage;
