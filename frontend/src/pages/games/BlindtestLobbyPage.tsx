import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Disc3, ListMusic, Music2, Play, Sparkles, EyeOff, Mic2, Hash, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';

type Mode = 'session' | 'single';
type Format = 'OP' | 'ED';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const LENGTHS = [5, 10, 30, 50, 100];

const ACTIVE_SEL = 'border-[#FDB913] bg-[#FDB913]/10';
const IDLE_SEL = 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50';

const BlindtestLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [mode, setMode] = useState<Mode>('session');
  const [format, setFormat] = useState<Format>('OP');
  const [length, setLength] = useState(10);
  const [hints, setHints] = useState(true);
  const [guessArtist, setGuessArtist] = useState(false);
  const [guessSequence, setGuessSequence] = useState(false);

  const FORMATS: { key: Format; title: string; sub: string }[] = [
    {
      key: 'OP',
      title: t('games.blindtest.lobby.formats.op.title', 'Opening'),
      sub: t('games.blindtest.lobby.formats.op.sub', 'Génériques de début'),
    },
    {
      key: 'ED',
      title: t('games.blindtest.lobby.formats.ed.title', 'Ending'),
      sub: t('games.blindtest.lobby.formats.ed.sub', 'Génériques de fin'),
    },
  ];

  const DIFFICULTIES: { key: Difficulty; label: string }[] = [
    { key: 'Easy', label: t('games.blindtest.lobby.difficulties.easy', 'Facile') },
    { key: 'Normal', label: t('games.blindtest.lobby.difficulties.normal', 'Normal') },
    { key: 'Hard', label: t('games.blindtest.lobby.difficulties.hard', 'Difficile') },
    { key: 'Impossible', label: t('games.blindtest.lobby.difficulties.impossible', 'Impossible') },
  ];

  const launch = () =>
    navigate('/blindtest/play/', {
      state: {
        mode,
        type: format,
        difficulty,
        length: mode === 'session' ? length : 1,
        hints,
        guessArtist,
        guessSequence,
      },
    });

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <header className="relative mb-12 text-center">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-40"
            aria-hidden
          />
          <div className="relative inline-flex items-center gap-3 mb-6">
            <span className="explore-stamp -rotate-2" aria-hidden>
              歌
            </span>
            <span className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              <Music2 className="w-3.5 h-3.5" /> {t('games.blindtest.lobby.badge', 'Blind Test')}
            </span>
          </div>
          <h1 className="font-manga relative text-5xl md:text-6xl font-black italic tracking-tighter uppercase text-[#F4F1E8] leading-none">
            {t('games.blindtest.lobby.title_part1', 'DEVINE')}{' '}
            <span className="text-[#E8442B]">
              {t('games.blindtest.lobby.title_part2', "L'ANIMÉ")}
            </span>
          </h1>
          <p className="relative mt-4 text-base font-medium text-[#8F94A5]">
            {t('games.blindtest.lobby.subtitle', 'Configure ta partie, puis lance le disque.')}
          </p>
        </header>

        <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-10 space-y-10">
          {/* Mode */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-4">
              {t('games.blindtest.lobby.section_mode', 'Mode de jeu')}
            </p>
            <div className="grid grid-cols-2 gap-4">
              {[
                {
                  key: 'session' as Mode,
                  icon: ListMusic,
                  title: t('games.blindtest.lobby.modes.session.title', 'Session'),
                  sub: t(
                    'games.blindtest.lobby.modes.session.sub',
                    'Enchaîne plusieurs génériques',
                  ),
                },
                {
                  key: 'single' as Mode,
                  icon: Disc3,
                  title: t('games.blindtest.lobby.modes.single.title', 'Un générique'),
                  sub: t('games.blindtest.lobby.modes.single.sub', 'Une seule manche'),
                },
              ].map(({ key, icon: Icon, title, sub }) => (
                <button
                  key={key}
                  onClick={() => setMode(key)}
                  aria-pressed={mode === key}
                  className={`flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-colors ${
                    mode === key ? ACTIVE_SEL : IDLE_SEL
                  }`}
                >
                  <Icon
                    className={`w-9 h-9 ${mode === key ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                  />
                  <span className="font-manga font-black italic uppercase text-lg text-[#F4F1E8]">
                    {title}
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] text-center">
                    {sub}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Session length */}
          {mode === 'session' && (
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-4">
                {t('games.blindtest.lobby.section_length', 'Durée de la session')}
              </p>
              <div className="grid grid-cols-5 gap-2">
                {LENGTHS.map((n) => (
                  <button
                    key={n}
                    onClick={() => setLength(n)}
                    aria-pressed={length === n}
                    className={`py-3 rounded-xl border-2 font-black italic text-sm transition-colors ${
                      length === n
                        ? 'border-[#FDB913] bg-[#FDB913] text-[#0B0C10]'
                        : 'border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#FDB913]/50'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Format */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-4">
              {t('games.blindtest.lobby.section_format', 'Format')}
            </p>
            <div className="grid grid-cols-2 gap-4">
              {FORMATS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFormat(f.key)}
                  aria-pressed={format === f.key}
                  className={`group flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-colors ${
                    format === f.key ? ACTIVE_SEL : IDLE_SEL
                  }`}
                >
                  <Disc3
                    className={`w-10 h-10 transition-transform group-hover:rotate-180 duration-700 ${format === f.key ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                  />
                  <span className="font-manga font-black italic uppercase text-xl text-[#F4F1E8]">
                    {f.title}
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-widest text-[#8F94A5]">
                    {f.sub}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulté */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-1">
              {t('games.blindtest.lobby.section_difficulty', 'Difficulté')}
            </p>
            <p className="text-[11px] text-[#8F94A5] mb-4">
              {t(
                'games.blindtest.lobby.section_difficulty_hint',
                "Détermine le nombre d'essais par manche.",
              )}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.key}
                  onClick={() => setDifficulty(d.key)}
                  aria-pressed={difficulty === d.key}
                  className={`py-3 rounded-xl border-2 font-black italic uppercase tracking-widest text-xs transition-colors ${
                    difficulty === d.key
                      ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]'
                      : 'border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#FDB913]/50'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Indices */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-4">
              {t('games.blindtest.lobby.section_hints', 'Indices visuels')}
            </p>
            <div className="grid grid-cols-2 gap-4">
              {[
                {
                  on: true,
                  icon: Sparkles,
                  title: t('games.blindtest.lobby.hints_on.title', 'Avec indices'),
                  sub: t('games.blindtest.lobby.hints_on.sub', 'Le visuel apparaît, déformé'),
                },
                {
                  on: false,
                  icon: EyeOff,
                  title: t('games.blindtest.lobby.hints_off.title', 'Sans indices'),
                  sub: t('games.blindtest.lobby.hints_off.sub', 'Audio uniquement'),
                },
              ].map(({ on, icon: Icon, title, sub }) => (
                <button
                  key={String(on)}
                  onClick={() => setHints(on)}
                  aria-pressed={hints === on}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-colors ${
                    hints === on ? ACTIVE_SEL : IDLE_SEL
                  }`}
                >
                  <Icon
                    className={`w-6 h-6 shrink-0 ${hints === on ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                  />
                  <div>
                    <p className="font-manga font-black italic uppercase text-sm text-[#F4F1E8] m-0">
                      {title}
                    </p>
                    <p className="text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] m-0">
                      {sub}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Objectifs bonus */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-1">
              {t('games.blindtest.lobby.section_bonus', 'Objectifs bonus')}
            </p>
            <p className="text-[11px] text-[#8F94A5] mb-4">
              {t(
                'games.blindtest.lobby.section_bonus_hint',
                "Une fois l'animé trouvé, gagne des points en plus.",
              )}
            </p>
            <div className="space-y-3">
              {[
                {
                  on: guessArtist,
                  set: setGuessArtist,
                  icon: Mic2,
                  title: t(
                    'games.blindtest.lobby.bonus_singer.title',
                    'Deviner le/les chanteur(s)',
                  ),
                  sub: t(
                    'games.blindtest.lobby.bonus_singer.sub',
                    "L'interprète du générique · +25 pts",
                  ),
                },
                {
                  on: guessSequence,
                  set: setGuessSequence,
                  icon: Hash,
                  title: t(
                    'games.blindtest.lobby.bonus_number.title',
                    "Deviner le numéro d'opening",
                  ),
                  sub: t(
                    'games.blindtest.lobby.bonus_number.sub',
                    'Le n° du générique (OP/ED) · +25 pts',
                  ),
                },
              ].map(({ on, set, icon: Icon, title, sub }) => (
                <button
                  key={title}
                  type="button"
                  onClick={() => set((v) => !v)}
                  role="switch"
                  aria-checked={on}
                  className={`w-full flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-colors ${
                    on ? ACTIVE_SEL : IDLE_SEL
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 shrink-0 ${on ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
                  />
                  <div className="flex-grow">
                    <p className="font-black text-sm leading-tight text-[#F4F1E8]">{title}</p>
                    <p className="text-[11px] font-medium text-[#8F94A5]">{sub}</p>
                  </div>
                  <span
                    className={`shrink-0 w-11 h-6 rounded-full p-0.5 transition-colors ${on ? 'bg-[#FDB913]' : 'bg-[#F4F1E8]/15'}`}
                  >
                    <span
                      className={`grid place-items-center w-5 h-5 rounded-full bg-[#0B0C10] shadow transition-transform ${on ? 'translate-x-5' : 'translate-x-0'}`}
                    >
                      {on && <Check className="w-3 h-3 text-[#FDB913]" />}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Launch */}
          <button
            onClick={launch}
            className="w-full flex items-center justify-center gap-3 bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest text-lg py-5 rounded-xl transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <Play className="w-6 h-6 fill-current" />
            {mode === 'session'
              ? t('games.blindtest.lobby.launch_session', {
                  defaultValue: 'Lancer la session ({{length}})',
                  length,
                })
              : t('games.blindtest.lobby.launch_single', 'Lancer le Blind Test')}
          </button>
        </section>
      </div>
    </div>
  );
};

export default BlindtestLobbyPage;
