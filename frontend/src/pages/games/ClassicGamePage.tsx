import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { normalizeText as norm } from '../../utils/normalizeText';
import {
  Search,
  Trophy,
  RotateCcw,
  Lock,
  Flame,
  Target,
  Gauge,
  Globe,
  Tags,
  Clapperboard,
  ScrollText,
  Calendar,
  Shapes,
  Hash,
  CaseSensitive,
  Check,
  Sparkles,
  ChevronRight,
  SlidersHorizontal,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useClassicGame } from '../../features/games/hooks/useClassicGame';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { classicGameService } from '../../features/games/services/classicService';
import type { ClassicGuess, ClassicHintKey, ClassicReason } from '../../types';

const HINT_META: Record<ClassicHintKey, { icon: React.ElementType; tone: string }> = {
  year: { icon: Calendar, tone: 'text-blue-500' },
  origin: { icon: Globe, tone: 'text-teal-500' },
  tags: { icon: Tags, tone: 'text-yellow-500' },
  genres: { icon: Shapes, tone: 'text-orange-500' },
  studio: { icon: Clapperboard, tone: 'text-purple-500' },
  letter: { icon: CaseSensitive, tone: 'text-pink-500' },
  words: { icon: Hash, tone: 'text-cyan-500' },
  desc: { icon: ScrollText, tone: 'text-green-500' },
};

const ClassicGamePage: React.FC = () => {
  const { t } = useTranslation();
  const {
    gameState,
    loading,
    handleGuess,
    isGuessing,
    revealHint,
    revealingHint,
    startGame,
    starting,
  } = useClassicGame();
  const navigate = useNavigate();
  const [guess, setGuess] = useState('');
  const [titles, setTitles] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSug, setShowSug] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Le backend renvoie un palier de couleur par tentative selon la proximité
  // (danger = brûlant … secondary = glacial). On le traduit en « chaleur ».
  const HEAT: Record<string, { label: string; bar: string; chip: string; glow: string }> = {
    danger: {
      label: t('games.classic.game.heat.danger', 'Brûlant'),
      bar: 'bg-red-500',
      chip: 'text-red-500 bg-red-500/10',
      glow: 'shadow-[0_0_26px_-8px_rgba(239,68,68,0.8)]',
    },
    warning: {
      label: t('games.classic.game.heat.warning', 'Chaud'),
      bar: 'bg-amber-500',
      chip: 'text-amber-600 dark:text-amber-400 bg-amber-500/10',
      glow: '',
    },
    primary: {
      label: t('games.classic.game.heat.primary', 'Tiède'),
      bar: 'bg-blue-500',
      chip: 'text-blue-500 bg-blue-500/10',
      glow: '',
    },
    secondary: {
      label: t('games.classic.game.heat.secondary', 'Glacial'),
      bar: 'bg-slate-400',
      chip: 'text-slate-500 bg-slate-400/10',
      glow: '',
    },
  };
  const heatOf = (g: ClassicGuess) => HEAT[g.color ?? 'secondary'] ?? HEAT.secondary;

  const HOW_TO = [
    {
      t: t('games.classic.game.how_to.step1.title', 'Devinez une œuvre'),
      d: t(
        'games.classic.game.how_to.step1.desc',
        "Tapez le titre d'un anime ou manga. L'autocomplétion vous aide à viser un titre valide du catalogue.",
      ),
    },
    {
      t: t('games.classic.game.how_to.step2.title', 'Lisez la chaleur'),
      d: t(
        'games.classic.game.how_to.step2.desc',
        'Chaque tentative révèle sa proximité avec l’œuvre mystère : plus c’est chaud, plus vous brûlez.',
      ),
    },
    {
      t: t('games.classic.game.how_to.step3.title', 'Débloquez des indices'),
      d: t(
        'games.classic.game.how_to.step3.desc',
        'Les indices que vous avez choisis se débloquent au fil de vos essais quand la piste se refroidit.',
      ),
    },
    {
      t: t('games.classic.game.how_to.step4.title', "Démasquez l'œuvre"),
      d: t(
        'games.classic.game.how_to.step4.desc',
        'Trouvez le titre exact pour remporter la manche et empocher l’XP.',
      ),
    },
  ];

  const HEAT_LEGEND: Array<{ key: keyof typeof HEAT; range: string }> = [
    { key: 'secondary', range: '0–40' },
    { key: 'primary', range: '40–70' },
    { key: 'warning', range: '70–90' },
    { key: 'danger', range: '90+' },
  ];

  // Catalogue des titres pour l'autocomplete (chargé une fois).
  useEffect(() => {
    let active = true;
    classicGameService
      .getTitles()
      .then((t) => {
        if (active) setTitles(t);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const onChange = (val: string) => {
    setGuess(val);
    const q = norm(val.trim());
    if (q.length < 2) {
      setSuggestions([]);
      setShowSug(false);
      return;
    }
    const starts: string[] = [];
    const incl: string[] = [];
    for (const t of titles) {
      const n = norm(t);
      if (n.startsWith(q)) starts.push(t);
      else if (n.includes(q)) incl.push(t);
      if (starts.length >= 8) break;
    }
    const sug = [...starts, ...incl].slice(0, 8);
    setSuggestions(sug);
    setShowSug(sug.length > 0);
  };

  const submit = async (value?: string) => {
    const g = (value ?? guess).trim();
    if (!g || isGuessing) return;
    setShowSug(false);
    setGuess('');
    setSuggestions([]);
    try {
      await handleGuess({ guess: g });
    } catch {
      // L'erreur (ex. titre hors catalogue) est déjà signalée par un toast.
    }
    inputRef.current?.focus();
  };

  const guessCount = gameState?.guesses?.length ?? 0;
  const hints = gameState?.hints;
  // The player picks which hints and in what order in the lobby; the backend
  // returns them already ordered, so we follow the object's key order.
  const hintKeys = (hints ? Object.keys(hints) : []) as ClassicHintKey[];
  const unlockedHints = hintKeys.filter((k) => hints?.[k]?.can_reveal).length;

  const replay = () =>
    startGame({
      mediaType: gameState?.mediaType,
      difficulty: gameState?.difficulty,
      // Pass the exact set (even empty, for Tryhard) so replays keep the config.
      hintConfig: hintKeys,
    });

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16">
        <CardSkeleton />
      </div>
    );
  }
  if (!gameState) return null;

  const over = gameState.gameOver;

  return (
    <AnimatedPage>
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* ── Header ───────────────────────────────────────────── */}
        <header className="mb-10">
          <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.3em] text-blue-500 mb-3">
            <Target className="w-3.5 h-3.5" />{' '}
            {t('games.classic.game.badge', 'Déduction · Mode Classique')}
          </div>
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div>
              <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase leading-none">
                {t('games.classic.game.title_part1', 'CLASSIC')}{' '}
                <span className="text-blue-500">
                  {t('games.classic.game.title_part2', 'QUEST')}
                </span>
              </h1>
              <p className="mt-3 text-sm md:text-base font-bold opacity-60 max-w-xl">
                {t(
                  'games.classic.game.subtitle_prefix',
                  "Traquez l'œuvre mystère. Chaque tentative vous dit à quel point vous",
                )}{' '}
                <span className="text-red-500">
                  {t('games.classic.game.subtitle_highlight', 'brûlez')}
                </span>
                .
              </p>
            </div>
            {/* Status strip */}
            <div className="flex flex-wrap gap-2.5">
              <StatusPill
                icon={Gauge}
                label={t('games.classic.game.status_difficulty', 'Difficulté')}
                value={gameState.difficulty ?? 'Normal'}
              />
              <StatusPill
                icon={Search}
                label={t('games.classic.game.status_attempts', 'Tentatives')}
                value={String(guessCount)}
              />
              <StatusPill
                icon={Sparkles}
                label={t('games.classic.game.status_hints', 'Indices')}
                value={`${unlockedHints}/${hintKeys.length}`}
              />
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ── Colonne jeu ────────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-6">
            {!over ? (
              <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-7 md:p-8 shadow-token-card">
                <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest opacity-40 mb-5">
                  <Flame className="w-4 h-4 text-yellow-500" />{' '}
                  {t('games.classic.game.launch_attempt', 'Lancez une tentative')}
                </div>
                <div className="relative">
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 pointer-events-none" />
                  <input
                    ref={inputRef}
                    type="text"
                    value={guess}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        submit();
                      }
                    }}
                    onFocus={() => {
                      if (suggestions.length) setShowSug(true);
                    }}
                    onBlur={() => setTimeout(() => setShowSug(false), 150)}
                    placeholder={t('games.classic.game.input_placeholder', 'Entrez un titre…')}
                    aria-label={t('games.classic.game.input_aria', "Titre de l'œuvre à deviner")}
                    autoComplete="off"
                    disabled={isGuessing}
                    className="w-full pl-14 pr-4 py-4 md:py-5 rounded-2xl bg-black/[0.03] dark:bg-navy-900 border-2 border-transparent focus:border-blue-500 focus:ring-4 focus:ring-blue-500/15 outline-none font-bold text-base md:text-lg transition-all placeholder:opacity-30 disabled:opacity-50"
                  />
                  {showSug && suggestions.length > 0 && (
                    <ul className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-[#0f0f1a] rounded-2xl border border-black/10 dark:border-white/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
                      {suggestions.map((tt) => (
                        <li key={tt}>
                          <button
                            type="button"
                            onMouseDown={(e) => {
                              e.preventDefault();
                              submit(tt);
                            }}
                            className="w-full text-left px-5 py-3 hover:bg-blue-500/10 font-bold text-sm truncate transition-colors flex items-center gap-2"
                          >
                            <ChevronRight className="w-3.5 h-3.5 opacity-40 shrink-0" />
                            {tt}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => submit()}
                  disabled={!guess.trim() || isGuessing}
                  className="mt-4 w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black italic manga-font tracking-wide shadow-xl shadow-blue-600/20 transition-all hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center gap-2"
                >
                  <Search className="w-5 h-5" />{' '}
                  {isGuessing
                    ? t('games.classic.game.submitting', 'ANALYSE…')
                    : t('games.classic.game.submit', 'ENVOYER')}
                </button>
              </div>
            ) : (
              <div className="rounded-[2rem] border-2 border-green-500 bg-green-500/[0.07] p-10 text-center shadow-token-card">
                <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-green-500 flex items-center justify-center shadow-lg shadow-green-500/30">
                  <Trophy className="w-11 h-11 text-white" />
                </div>
                <h2 className="text-3xl font-black italic manga-font uppercase text-green-600 dark:text-green-400">
                  {t('games.classic.game.win_title', 'Œuvre démasquée')}
                </h2>
                <p className="mt-3 text-lg font-bold">
                  {t('games.classic.game.win_it_was', "C'était")}{' '}
                  <span className="text-green-600 dark:text-green-400">
                    {gameState.secret_title}
                  </span>
                </p>
                <p className="mt-1 text-xs font-black uppercase tracking-widest opacity-40">
                  {t('games.classic.game.win_solved_in', {
                    defaultValue: 'Résolu en {{count}} tentative{{plural}}',
                    count: guessCount,
                    plural: guessCount > 1 ? 's' : '',
                  })}
                </p>
                <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => replay()}
                    disabled={starting}
                    className="inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-green-600 hover:bg-green-500 text-white font-black italic manga-font tracking-wide shadow-xl shadow-green-600/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-60 disabled:hover:scale-100"
                  >
                    <RotateCcw className="w-5 h-5" />{' '}
                    {starting
                      ? t('games.classic.game.replay_loading', 'Nouvelle œuvre…')
                      : t('games.classic.game.replay', 'Rejouer')}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/game/classic/')}
                    className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl border-2 border-black/10 dark:border-white/15 font-black italic manga-font tracking-wide hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-all"
                  >
                    <SlidersHorizontal className="w-5 h-5" />{' '}
                    {t('games.classic.game.settings', 'Réglages')}
                  </button>
                </div>
              </div>
            )}

            {/* ── La piste (tentatives) ────────────────────────── */}
            <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-6 md:p-7 shadow-token-card">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-[11px] font-black uppercase tracking-widest opacity-40">
                  {t('games.classic.game.your_attempts', 'Vos tentatives')}
                </h3>
                {guessCount > 0 && (
                  <span className="text-[10px] font-black uppercase tracking-widest opacity-30">
                    {t('games.classic.game.closest_first', 'les plus proches en tête')}
                  </span>
                )}
              </div>

              {guessCount === 0 ? (
                <div className="text-center py-12">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-15" />
                  <p className="font-black italic uppercase opacity-30 text-sm">
                    {t('games.classic.game.no_lead_title', "Aucune piste pour l'instant")}
                  </p>
                  <p className="text-xs font-bold opacity-25 mt-1">
                    {t(
                      'games.classic.game.no_lead_desc',
                      "Lancez une première tentative pour ouvrir l'enquête.",
                    )}
                  </p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {gameState.guesses.map((g, i) => {
                    const heat = heatOf(g);
                    const score = Math.round(g.score ?? 0);
                    return (
                      <li
                        key={`${g.title}-${i}`}
                        className={`rounded-2xl border p-4 animate-fade-in ${
                          g.is_correct
                            ? 'border-green-500 bg-green-500/[0.08]'
                            : `border-black/5 dark:border-white/5 bg-black/[0.02] dark:bg-white/[0.02] ${heat.glow}`
                        }`}
                      >
                        <div className="flex items-center justify-between gap-3 mb-2.5">
                          <div className="min-w-0">
                            <p className="font-black truncate leading-tight">{g.title}</p>
                            {g.title_english && g.title_english !== g.title && (
                              <p className="text-[11px] font-bold opacity-40 truncate">
                                {g.title_english}
                              </p>
                            )}
                          </div>
                          {g.is_correct ? (
                            <span className="shrink-0 inline-flex items-center gap-1.5 text-xs font-black uppercase px-3 py-1.5 rounded-full bg-green-500 text-white">
                              <Check className="w-3.5 h-3.5" />{' '}
                              {t('games.classic.game.found', 'Trouvé')}
                            </span>
                          ) : (
                            <div className="shrink-0 flex items-center gap-2">
                              <span
                                className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full ${heat.chip}`}
                              >
                                {heat.label}
                              </span>
                              <span className="text-lg font-black tabular-nums w-12 text-right">
                                {score}%
                              </span>
                            </div>
                          )}
                        </div>
                        {!g.is_correct && (
                          <div className="h-2 rounded-full bg-black/5 dark:bg-white/5 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${heat.bar} transition-all duration-700`}
                              style={{ width: `${Math.max(4, score)}%` }}
                            />
                          </div>
                        )}
                        {(g.reasons ?? []).length > 0 && (
                          <ul className="mt-2 space-y-1 pl-1">
                            {(g.reasons ?? []).map((reason: ClassicReason) => (
                              <li
                                key={reason.kind}
                                className="text-xs text-gray-600 dark:text-gray-400"
                              >
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                  {reason.label}
                                </span>
                                {reason.detail.length > 0 && (
                                  <span className="text-gray-500 dark:text-gray-500">
                                    {' '}
                                    — {reason.detail.join(' · ')}
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* ── Colonne latérale ───────────────────────────────── */}
          <div className="space-y-6">
            {/* Indices */}
            <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-6 shadow-token-card">
              <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest opacity-40 mb-5">
                <Sparkles className="w-4 h-4 text-yellow-500" />{' '}
                {t('games.classic.game.hints_title', 'Indices')}
              </div>
              <div className="space-y-3">
                {hintKeys.length === 0 && (
                  <p className="text-xs font-bold opacity-30 text-center py-4">
                    {t('games.classic.game.no_hints', 'Aucun indice pour cette partie.')}
                  </p>
                )}
                {hintKeys.map((key) => {
                  const h = hints?.[key];
                  const meta = HINT_META[key];
                  const Icon = meta.icon;
                  const label = h?.label ?? key;
                  const unlockAt = h?.unlocks_at ?? 0;
                  const canReveal = h?.can_reveal ?? false;
                  const revealed = h?.revealed ?? false;
                  const progress = unlockAt > 0 ? Math.min(1, guessCount / unlockAt) : 1;

                  return (
                    <div
                      key={key}
                      className={`rounded-2xl border p-3.5 transition-all ${
                        revealed
                          ? 'border-yellow-500/40 bg-yellow-500/[0.06]'
                          : 'border-black/5 dark:border-white/5 bg-black/[0.02] dark:bg-white/[0.02]'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="flex items-center gap-2 text-xs font-black uppercase tracking-wide">
                          <Icon className={`w-4 h-4 ${revealed ? meta.tone : 'opacity-30'}`} />
                          {label}
                        </span>
                        {revealed ? (
                          <Check className="w-4 h-4 text-yellow-500" />
                        ) : canReveal ? (
                          <button
                            type="button"
                            onClick={() => revealHint(key)}
                            disabled={revealingHint}
                            className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-yellow-500 text-black hover:scale-105 active:scale-95 transition-transform disabled:opacity-50"
                          >
                            {t('games.classic.game.reveal', 'Révéler')}
                          </button>
                        ) : (
                          <span className="flex items-center gap-1 text-[10px] font-black uppercase tracking-wider opacity-40">
                            <Lock className="w-3 h-3" />{' '}
                            {t('games.classic.game.unlock_at', {
                              defaultValue: '{{count}} essais',
                              count: unlockAt,
                            })}
                          </span>
                        )}
                      </div>

                      {revealed && h?.value && (
                        <p className="mt-2 text-sm font-semibold leading-snug text-yellow-700 dark:text-yellow-200/90">
                          {h.value}
                        </p>
                      )}
                      {!revealed && !canReveal && (
                        <div className="mt-2.5 h-1 rounded-full bg-black/5 dark:bg-white/10 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-yellow-500/60 transition-all duration-500"
                            style={{ width: `${progress * 100}%` }}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Comment jouer */}
            <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-6 shadow-token-card">
              <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest opacity-40 mb-5">
                <Target className="w-4 h-4 text-blue-500" />{' '}
                {t('games.classic.game.how_to_title', 'Comment jouer')}
              </div>
              <ol className="space-y-4">
                {HOW_TO.map((s, i) => (
                  <li key={s.t} className="flex gap-3.5">
                    <span className="shrink-0 w-7 h-7 rounded-xl bg-blue-500/10 text-blue-500 grid place-items-center font-black text-sm">
                      {i + 1}
                    </span>
                    <div>
                      <p className="font-black text-sm leading-tight">{s.t}</p>
                      <p className="text-xs font-medium opacity-55 leading-snug mt-0.5">{s.d}</p>
                    </div>
                  </li>
                ))}
              </ol>

              <div className="mt-6 pt-5 border-t border-black/5 dark:border-white/10">
                <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-3">
                  {t('games.classic.game.heat_scale', 'Échelle de chaleur')}
                </p>
                <div className="grid grid-cols-4 gap-2">
                  {HEAT_LEGEND.map(({ key, range }) => (
                    <div key={key} className="text-center">
                      <div className={`h-1.5 rounded-full ${HEAT[key].bar} mb-1.5`} />
                      <p className="text-[10px] font-black uppercase leading-none">
                        {HEAT[key].label}
                      </p>
                      <p className="text-[9px] font-bold opacity-40 tabular-nums mt-0.5">{range}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

const StatusPill: React.FC<{ icon: React.ElementType; label: string; value: string }> = ({
  icon: Icon,
  label,
  value,
}) => (
  <div className="flex items-center gap-2.5 rounded-2xl border border-black/5 dark:border-white/10 bg-surface-card px-4 py-2.5 shadow-sm">
    <Icon className="w-4 h-4 opacity-40" />
    <div className="leading-none">
      <p className="text-[9px] font-black uppercase tracking-widest opacity-40">{label}</p>
      <p className="text-sm font-black mt-0.5">{value}</p>
    </div>
  </div>
);

export default ClassicGamePage;
