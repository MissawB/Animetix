import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DifficultySelector } from './components/DifficultySelector';
import { useTranslation } from 'react-i18next';
import { Brain, Play, Clapperboard, BookOpen, Users, Bot, Sparkles, ScanFace } from 'lucide-react';

type Universe = 'Anime' | 'Manga' | 'Character';
type Mode = 'classique' | 'animinator' | 'quiz-who';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const Section: React.FC<{ step: number; title: string; children: React.ReactNode }> = ({
  step,
  title,
  children,
}) => (
  <div>
    <div className="flex items-baseline gap-3 mb-4">
      <span className="shrink-0 w-6 h-6 rounded-md bg-[#E8442B]/12 text-[#E8442B] grid place-items-center font-black text-xs">
        {step}
      </span>
      <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">{title}</h2>
    </div>
    {children}
  </div>
);

const AkinetixLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('classique');
  const [universe, setUniverse] = useState<Universe>('Anime');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');

  const DIFFICULTIES: { key: Difficulty; label: string; sub: string; active: string }[] = [
    {
      key: 'Easy',
      label: t('games.akinetix.lobby.diff_easy', 'Facile'),
      sub: t('games.akinetix.lobby.diff_easy_sub', 'Très connus'),
      active: 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]',
    },
    {
      key: 'Normal',
      label: t('games.akinetix.lobby.diff_normal', 'Normal'),
      sub: t('games.akinetix.lobby.diff_normal_sub', 'Grand public'),
      active: 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]',
    },
    {
      key: 'Hard',
      label: t('games.akinetix.lobby.diff_hard', 'Difficile'),
      sub: t('games.akinetix.lobby.diff_hard_sub', 'Connaisseurs'),
      active: 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]',
    },
    {
      key: 'Impossible',
      label: t('games.akinetix.lobby.diff_impossible', 'Impossible'),
      sub: t('games.akinetix.lobby.diff_impossible_sub', 'Pépites obscures'),
      active: 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]',
    },
  ];

  const MODES: {
    key: Mode;
    label: string;
    sub: string;
    desc: string;
    icon: React.ElementType;
    route: string;
  }[] = [
    {
      key: 'classique',
      label: t('games.akinetix.lobby.mode_classic_label', 'Akinetix Classique'),
      sub: t('games.akinetix.lobby.mode_classic_sub', "L'IA devine"),
      desc: t(
        'games.akinetix.lobby.mode_classic_desc',
        "L'IA te pose des questions (oui / non / probablement…) et tente de deviner à quoi tu penses.",
      ),
      icon: Brain,
      route: '/akinetix/play/',
    },
    {
      key: 'animinator',
      label: 'Animinator',
      sub: t('games.akinetix.lobby.mode_animinator_sub', 'Tu interroges le génie'),
      desc: t(
        'games.akinetix.lobby.mode_animinator_desc',
        'Le génie a une œuvre en tête : pose-lui tes questions librement pour la démasquer.',
      ),
      icon: Bot,
      route: '/animinator/',
    },
    {
      key: 'quiz-who',
      label: t('games.akinetix.lobby.mode_quiz_who_label', 'Qui est-ce ?'),
      sub: t('games.akinetix.lobby.mode_quiz_who_sub', 'Plateau à éliminer'),
      desc: t(
        'games.akinetix.lobby.mode_quiz_who_desc',
        'Un plateau de portraits, un secret caché : pose des questions pour éliminer les têtes et démasquer la bonne.',
      ),
      icon: ScanFace,
      route: '/quiz-who/',
    },
  ];

  const UNIVERSES: { key: Universe; label: string; sub: string; icon: React.ElementType }[] = [
    {
      key: 'Anime',
      label: 'Anime',
      sub: t('games.akinetix.lobby.universe_anime_sub', 'Séries animées'),
      icon: Clapperboard,
    },
    {
      key: 'Manga',
      label: 'Manga',
      sub: t('games.akinetix.lobby.universe_manga_sub', 'Œuvres papier'),
      icon: BookOpen,
    },
    {
      key: 'Character',
      label: t('games.akinetix.lobby.universe_characters', 'Personnages'),
      sub: t('games.akinetix.lobby.universe_characters_sub', 'Héros & figures'),
      icon: Users,
    },
  ];

  const launch = () => {
    const target = MODES.find((m) => m.key === mode);
    if (target) navigate(target.route, { state: { mediaType: universe, difficulty } });
  };

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
              読
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.akinetix.lobby.kicker', 'Lecture de pensées')}
            </span>
          </div>
          <h1 className="font-manga relative mt-4 text-5xl md:text-6xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
            AKI<span className="text-[#E8442B]">NETIX</span>
          </h1>
          <p className="relative mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">
            {t(
              'games.akinetix.lobby.subtitle',
              'Choisis ton mode et ton univers, puis laisse la magie opérer.',
            )}
          </p>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8 md:p-9 space-y-10">
          {/* Mode */}
          <Section step={1} title={t('games.akinetix.lobby.step_mode', 'Mode de jeu')}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {MODES.map(({ key, label, sub, desc, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setMode(key)}
                  aria-pressed={mode === key}
                  className={`flex flex-col items-start gap-3 p-5 rounded-2xl border-2 text-left transition-colors ${
                    mode === key
                      ? 'border-[#FDB913] bg-[#FDB913]/10'
                      : 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-8 h-8 ${mode === key ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                    />
                    <div>
                      <span className="block font-manga text-lg text-[#F4F1E8] leading-none">
                        {label}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
                        {sub}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs font-medium text-[#8F94A5] leading-relaxed">{desc}</p>
                </button>
              ))}
            </div>
          </Section>

          {/* Univers */}
          <Section step={2} title={t('games.akinetix.lobby.step_universe', 'Univers')}>
            <div className="grid grid-cols-3 gap-3 sm:gap-4">
              {UNIVERSES.map(({ key, label, sub, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setUniverse(key)}
                  aria-pressed={universe === key}
                  className={`flex flex-col items-center gap-3 p-5 sm:p-6 rounded-2xl border-2 transition-colors ${
                    universe === key
                      ? 'border-[#FDB913] bg-[#FDB913]/10'
                      : 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50'
                  }`}
                >
                  <Icon
                    className={`w-8 h-8 sm:w-9 sm:h-9 ${universe === key ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                  />
                  <span className="font-manga text-base sm:text-lg text-[#F4F1E8] text-center leading-none">
                    {label}
                  </span>
                  <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] text-center">
                    {sub}
                  </span>
                </button>
              ))}
            </div>
          </Section>

          {/* Difficulté */}
          <Section step={3} title={t('games.akinetix.lobby.step_difficulty', 'Difficulté')}>
            <DifficultySelector
              options={DIFFICULTIES}
              value={difficulty}
              onChange={setDifficulty}
              hoverClassName="hover:border-[#FDB913]/40"
            />
          </Section>

          {/* Launch */}
          <button
            onClick={launch}
            className="w-full flex items-center justify-center gap-3 bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest text-lg py-5 rounded-xl transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <Play className="w-6 h-6 fill-current" />{' '}
            {t('games.akinetix.lobby.launch', 'Lancer la partie')}
          </button>
          <p className="-mt-4 text-center text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] flex items-center justify-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#FDB913]" />
            {MODES.find((m) => m.key === mode)?.label} ·{' '}
            {UNIVERSES.find((u) => u.key === universe)?.label} ·{' '}
            {DIFFICULTIES.find((d) => d.key === difficulty)?.label}
          </p>
        </div>
      </div>
    </div>
  );
};

export default AkinetixLobbyPage;
