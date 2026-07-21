import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { normalizeText as norm } from '../../utils/normalizeText';
import {
  Search,
  Trophy,
  RotateCcw,
  Flame,
  Target,
  Gauge,
  Sparkles,
  ChevronRight,
  SlidersHorizontal,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useClassicGame } from '../../features/games/hooks/useClassicGame';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { classicGameService } from '../../features/games/services/classicService';
import type { ClassicGuess, ClassicHintKey } from '../../types';
import { StatusPill } from './components/StatusPill';
import { ClassicGuessTrail } from './components/ClassicGuessTrail';
import { ClassicHintsPanel } from './components/ClassicHintsPanel';
import { ClassicHowToPanel } from './components/ClassicHowToPanel';

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
            <ClassicGuessTrail guesses={gameState.guesses} heatOf={heatOf} />
          </div>

          {/* ── Colonne latérale ───────────────────────────────── */}
          <div className="space-y-6">
            {/* Indices */}
            <ClassicHintsPanel
              hintKeys={hintKeys}
              hints={hints}
              guessCount={guessCount}
              onReveal={revealHint}
              revealing={revealingHint}
            />

            {/* Comment jouer */}
            <ClassicHowToPanel howTo={HOW_TO} heat={HEAT} heatLegend={HEAT_LEGEND} />
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ClassicGamePage;
