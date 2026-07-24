import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DifficultySelector } from './components/DifficultySelector';
import { Play, Sparkles, Loader2 } from 'lucide-react';
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
      <span className="shrink-0 w-6 h-6 rounded-md bg-[#E8442B]/12 text-[#E8442B] grid place-items-center font-black text-xs">
        {step}
      </span>
      <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">{title}</h2>
      {hint && <span className="text-[11px] font-bold text-[#8F94A5]/80">{hint}</span>}
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
      active: 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]',
    },
    {
      key: 'Normal',
      label: t('games.classic.lobby.difficulties.normal.label', 'Normal'),
      sub: t('games.classic.lobby.difficulties.normal.sub', 'Grand public'),
      active: 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]',
    },
    {
      key: 'Hard',
      label: t('games.classic.lobby.difficulties.hard.label', 'Difficile'),
      sub: t('games.classic.lobby.difficulties.hard.sub', 'Pour connaisseurs'),
      active: 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]',
    },
    {
      key: 'Impossible',
      label: t('games.classic.lobby.difficulties.impossible.label', 'Impossible'),
      sub: t('games.classic.lobby.difficulties.impossible.sub', 'Pépites obscures'),
      active: 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]',
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
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-3xl mx-auto px-6 py-14">
        {/* Header — plaque de protocole */}
        <header className="relative mb-12">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-40"
            aria-hidden
          />
          <div className="relative flex items-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              推
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.classic.lobby.badge', 'Déduction')}
            </span>
          </div>
          <h1 className="font-manga relative mt-4 text-5xl md:text-6xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
            ANIMETIX{' '}
            <span className="text-[#E8442B]">
              {t('games.classic.lobby.title_highlight', 'CLASSIQUE')}
            </span>
          </h1>
          <p className="relative mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">
            {t(
              'games.classic.lobby.subtitle',
              "Configure ta traque, puis pars démasquer l'œuvre mystère.",
            )}
          </p>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8 md:p-9 space-y-10">
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
            <DifficultySelector
              options={DIFFICULTIES}
              value={difficulty}
              onChange={setDifficulty}
              hoverClassName="hover:border-[#FDB913]/40"
            />
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
            className="w-full flex items-center justify-center gap-3 bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest text-lg py-5 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
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
          <p className="-mt-4 text-center text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] flex items-center justify-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#FDB913]" />
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
    </div>
  );
};

export default ClassicLobbyPage;
