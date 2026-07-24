import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DifficultySelector } from './components/DifficultySelector';
import { Target, Play, Sparkles, Loader2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { classicGameService } from '../../features/games/services/classicService';
import { CLASSIC_STATE_QUERY_KEY } from '../../features/games/hooks/useClassicGame';
import { useToastStore } from '../../store/toastStore';
import type { ClassicHintKey } from '../../types';
import { ClassicUniverseSelector, type Universe } from './components/ClassicUniverseSelector';
import { ClassicHintConfigSection, type HintMode } from './components/ClassicHintConfigSection';

type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const CLASSIC_PRESET: ClassicHintKey[] = ['year', 'studio', 'tags', 'desc'];
const UNLOCK_STEP = 5;

const Section: React.FC<{
  step: number;
  title: string;
  hint?: string;
  children: React.ReactNode;
}> = ({ step, title, hint, children }) => (
  <div>
    <div className="flex items-baseline gap-3 mb-4">
      <span className="shrink-0 w-6 h-6 rounded-lg bg-blue-500/10 text-blue-500 grid place-items-center font-black text-xs">
        {step}
      </span>
      <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">
        {title}
      </h2>
      {hint && <span className="text-[11px] font-bold text-gray-400/80">{hint}</span>}
    </div>
    {children}
  </div>
);

const ClassicLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);

  const DIFFICULTIES: { key: Difficulty; label: string; sub: string; active: string }[] = [
    {
      key: 'Easy',
      label: t('games.classic.lobby.difficulties.easy.label', 'Facile'),
      sub: t('games.classic.lobby.difficulties.easy.sub', 'Titres très connus'),
      active: 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400',
    },
    {
      key: 'Normal',
      label: t('games.classic.lobby.difficulties.normal.label', 'Normal'),
      sub: t('games.classic.lobby.difficulties.normal.sub', 'Grand public'),
      active: 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400',
    },
    {
      key: 'Hard',
      label: t('games.classic.lobby.difficulties.hard.label', 'Difficile'),
      sub: t('games.classic.lobby.difficulties.hard.sub', 'Pour connaisseurs'),
      active: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400',
    },
    {
      key: 'Impossible',
      label: t('games.classic.lobby.difficulties.impossible.label', 'Impossible'),
      sub: t('games.classic.lobby.difficulties.impossible.sub', 'Pépites obscures'),
      active: 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400',
    },
  ];

  const [universe, setUniverse] = useState<Universe>('Anime');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [hintMode, setHintMode] = useState<HintMode>('classic');
  const [hintOrder, setHintOrder] = useState<ClassicHintKey[]>([
    'year',
    'origin',
    'tags',
    'genres',
    'studio',
    'letter',
    'words',
    'desc',
  ]);
  const [enabled, setEnabled] = useState<Record<ClassicHintKey, boolean>>({
    year: true,
    tags: true,
    genres: true,
    studio: true,
    desc: true,
    origin: false,
    letter: false,
    words: false,
  });
  const [launching, setLaunching] = useState(false);

  const customConfig = hintOrder.filter((k) => enabled[k]);
  const config =
    hintMode === 'classic' ? CLASSIC_PRESET : hintMode === 'tryhard' ? [] : customConfig;

  const move = (index: number, dir: -1 | 1) => {
    const target = index + dir;
    if (target < 0 || target >= hintOrder.length) return;
    setHintOrder((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const toggle = (key: ClassicHintKey) => setEnabled((prev) => ({ ...prev, [key]: !prev[key] }));

  const launch = async () => {
    if (launching) return;
    setLaunching(true);
    try {
      const state = await classicGameService.start(universe, difficulty, config);
      queryClient.setQueryData(CLASSIC_STATE_QUERY_KEY, state);
      navigate('/game/classic/play/');
    } catch {
      addToast(
        t('games.classic.lobby.toast_launch_failed', 'Impossible de lancer la partie. Réessayez.'),
        'error',
      );
      setLaunching(false);
    }
  };

  const unlockAt = (key: ClassicHintKey) => (config.indexOf(key) + 1) * UNLOCK_STEP;

  const hintCountLabel = (count: number) =>
    count === 0
      ? t('games.classic.lobby.no_hints', 'aucun indice')
      : t('games.classic.lobby.hint_count', {
          defaultValue: '{{count}} indice{{plural}}',
          count,
          plural: count > 1 ? 's' : '',
        });

  const universeLabel =
    universe === 'Anime' ? 'Anime' : universe === 'Manga' ? 'Manga' : 'Personnages';

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <Target className="w-3.5 h-3.5" /> {t('games.classic.lobby.badge', 'Déduction')}
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          ANIMETIX{' '}
          <span className="text-blue-500">
            {t('games.classic.lobby.title_highlight', 'CLASSIQUE')}
          </span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          {t(
            'games.classic.lobby.subtitle',
            "Configure ta traque, puis pars démasquer l'œuvre mystère.",
          )}
        </p>
      </div>

      <div className="rounded-[2.5rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-7 md:p-9 shadow-token-card space-y-10">
        {/* Univers */}
        <Section step={1} title={t('games.classic.lobby.section_universe', 'Univers')}>
          <ClassicUniverseSelector universe={universe} setUniverse={setUniverse} />
        </Section>

        {/* Difficulté */}
        <Section
          step={2}
          title={t('games.classic.lobby.section_difficulty', 'Difficulté')}
          hint={t('games.classic.lobby.section_difficulty_hint', "Rareté de l'œuvre à trouver")}
        >
          <DifficultySelector options={DIFFICULTIES} value={difficulty} onChange={setDifficulty} />
        </Section>

        {/* Indices */}
        <Section
          step={3}
          title={t('games.classic.lobby.section_hints', 'Indices')}
          hint={hintCountLabel(config.length)}
        >
          <ClassicHintConfigSection
            hintMode={hintMode}
            setHintMode={setHintMode}
            hintOrder={hintOrder}
            enabled={enabled}
            move={move}
            toggle={toggle}
            unlockAt={unlockAt}
            classicPreset={CLASSIC_PRESET}
            unlockStep={UNLOCK_STEP}
          />
        </Section>

        {/* Launch */}
        <button
          onClick={launch}
          disabled={launching}
          className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl shadow-xl shadow-blue-600/20 hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60 disabled:hover:scale-100"
        >
          {launching ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />{' '}
              {t('games.classic.lobby.launching', 'Préparation…')}
            </>
          ) : (
            <>
              <Play className="w-6 h-6 fill-current" />{' '}
              {t('games.classic.lobby.launch', 'Lancer la partie')}
            </>
          )}
        </button>
        <p className="-mt-4 text-center text-[11px] font-bold uppercase tracking-widest text-gray-400 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          {universeLabel} · {DIFFICULTIES.find((d) => d.key === difficulty)?.label} ·{' '}
          {hintMode === 'classic'
            ? t('games.classic.lobby.modes.classic.label', 'Classique')
            : hintMode === 'tryhard'
              ? t('games.classic.lobby.modes.tryhard.label', 'Tryhard')
              : t('games.classic.lobby.modes.custom.label', 'Personnalisé')}{' '}
          (
          {t('games.classic.lobby.hint_count', {
            defaultValue: '{{count}} indice{{plural}}',
            count: config.length,
            plural: config.length > 1 ? 's' : '',
          })}
          )
        </p>
      </div>
    </div>
  );
};

export default ClassicLobbyPage;
