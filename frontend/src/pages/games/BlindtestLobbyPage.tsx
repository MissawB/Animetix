import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Disc3, ListMusic, Music2, Play, Sparkles, EyeOff, Mic2, Hash, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';

type Mode = 'session' | 'single';
type Format = 'OP' | 'ED';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const LENGTHS = [5, 10, 30, 50, 100];

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
    { key: 'OP', title: t('games.blindtest.lobby.formats.op.title', 'Opening'), sub: t('games.blindtest.lobby.formats.op.sub', 'Génériques de début') },
    { key: 'ED', title: t('games.blindtest.lobby.formats.ed.title', 'Ending'), sub: t('games.blindtest.lobby.formats.ed.sub', 'Génériques de fin') },
  ];

  const DIFFICULTIES: { key: Difficulty; label: string; active: string }[] = [
    { key: 'Easy', label: t('games.blindtest.lobby.difficulties.easy', 'Facile'), active: 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' },
    { key: 'Normal', label: t('games.blindtest.lobby.difficulties.normal', 'Normal'), active: 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400' },
    { key: 'Hard', label: t('games.blindtest.lobby.difficulties.hard', 'Difficile'), active: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400' },
    { key: 'Impossible', label: t('games.blindtest.lobby.difficulties.impossible', 'Impossible'), active: 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400' },
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
    <div className="max-w-3xl mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <Music2 className="w-3.5 h-3.5" /> {t('games.blindtest.lobby.badge', 'Blind Test')}
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          {t('games.blindtest.lobby.title_part1', 'DEVINE')} <span className="text-yellow-400">{t('games.blindtest.lobby.title_part2', "L'ANIMÉ")}</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          {t('games.blindtest.lobby.subtitle', 'Configure ta partie, puis lance le disque.')}
        </p>
      </div>

      <Card padding="lg" className="space-y-10">
        {/* Mode */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('games.blindtest.lobby.section_mode', 'Mode de jeu')}</p>
          <div className="grid grid-cols-2 gap-4">
            {([
              { key: 'session' as Mode, icon: ListMusic, title: t('games.blindtest.lobby.modes.session.title', 'Session'), sub: t('games.blindtest.lobby.modes.session.sub', 'Enchaîne plusieurs génériques') },
              { key: 'single' as Mode, icon: Disc3, title: t('games.blindtest.lobby.modes.single.title', 'Un générique'), sub: t('games.blindtest.lobby.modes.single.sub', 'Une seule manche') },
            ]).map(({ key, icon: Icon, title, sub }) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                aria-pressed={mode === key}
                className={`flex flex-col items-center gap-3 p-6 rounded-3xl border-2 transition-all ${
                  mode === key ? 'border-yellow-400 bg-yellow-400/10 shadow-lg' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-9 h-9 ${mode === key ? 'text-yellow-500' : 'text-gray-400'}`} />
                <span className="manga-font text-lg text-black dark:text-white">{title}</span>
                <span className="text-[11px] font-bold uppercase tracking-widest text-gray-400 text-center">{sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Session length */}
        {mode === 'session' && (
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('games.blindtest.lobby.section_length', 'Durée de la session')}</p>
            <div className="grid grid-cols-5 gap-2">
              {LENGTHS.map((n) => (
                <button
                  key={n}
                  onClick={() => setLength(n)}
                  aria-pressed={length === n}
                  className={`py-3 rounded-2xl border-2 font-black italic text-sm transition-all ${
                    length === n
                      ? 'border-yellow-400 bg-yellow-400 text-black shadow-md'
                      : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-yellow-400/50'
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
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('games.blindtest.lobby.section_format', 'Format')}</p>
          <div className="grid grid-cols-2 gap-4">
            {FORMATS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFormat(f.key)}
                aria-pressed={format === f.key}
                className={`group flex flex-col items-center gap-3 p-6 rounded-3xl border-2 transition-all ${
                  format === f.key ? 'border-yellow-400 bg-yellow-400/10 shadow-lg' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Disc3 className={`w-10 h-10 transition-transform group-hover:rotate-180 duration-700 ${format === f.key ? 'text-yellow-500' : 'text-gray-400'}`} />
                <span className="manga-font text-xl text-black dark:text-white">{f.title}</span>
                <span className="text-[11px] font-bold uppercase tracking-widest text-gray-400">{f.sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Difficulté */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-1">{t('games.blindtest.lobby.section_difficulty', 'Difficulté')}</p>
          <p className="text-[11px] text-gray-400 mb-4">{t('games.blindtest.lobby.section_difficulty_hint', "Détermine le nombre d'essais par manche.")}</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.key}
                onClick={() => setDifficulty(d.key)}
                aria-pressed={difficulty === d.key}
                className={`py-3 rounded-2xl border-2 font-black italic uppercase tracking-widest text-xs transition-all ${
                  difficulty === d.key ? d.active : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-yellow-400/50'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Indices */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">{t('games.blindtest.lobby.section_hints', 'Indices visuels')}</p>
          <div className="grid grid-cols-2 gap-4">
            {([
              { on: true, icon: Sparkles, title: t('games.blindtest.lobby.hints_on.title', 'Avec indices'), sub: t('games.blindtest.lobby.hints_on.sub', 'Le visuel apparaît, déformé') },
              { on: false, icon: EyeOff, title: t('games.blindtest.lobby.hints_off.title', 'Sans indices'), sub: t('games.blindtest.lobby.hints_off.sub', 'Audio uniquement') },
            ]).map(({ on, icon: Icon, title, sub }) => (
              <button
                key={String(on)}
                onClick={() => setHints(on)}
                aria-pressed={hints === on}
                className={`flex items-center gap-3 p-4 rounded-2xl border-2 text-left transition-all ${
                  hints === on ? 'border-yellow-400 bg-yellow-400/10 shadow-md' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-6 h-6 shrink-0 ${hints === on ? 'text-yellow-500' : 'text-gray-400'}`} />
                <div>
                  <p className="manga-font text-sm text-black dark:text-white m-0">{title}</p>
                  <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 m-0">{sub}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Objectifs bonus */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-1">{t('games.blindtest.lobby.section_bonus', 'Objectifs bonus')}</p>
          <p className="text-[11px] text-gray-400 mb-4">{t('games.blindtest.lobby.section_bonus_hint', "Une fois l'animé trouvé, gagne des points en plus.")}</p>
          <div className="space-y-3">
            {([
              { on: guessArtist, set: setGuessArtist, icon: Mic2, title: t('games.blindtest.lobby.bonus_singer.title', 'Deviner le/les chanteur(s)'), sub: t('games.blindtest.lobby.bonus_singer.sub', "L'interprète du générique · +25 pts") },
              { on: guessSequence, set: setGuessSequence, icon: Hash, title: t('games.blindtest.lobby.bonus_number.title', "Deviner le numéro d'opening"), sub: t('games.blindtest.lobby.bonus_number.sub', 'Le n° du générique (OP/ED) · +25 pts') },
            ]).map(({ on, set, icon: Icon, title, sub }) => (
              <button
                key={title}
                type="button"
                onClick={() => set((v) => !v)}
                role="switch"
                aria-checked={on}
                className={`w-full flex items-center gap-3 p-4 rounded-2xl border-2 text-left transition-all ${
                  on ? 'border-yellow-400 bg-yellow-400/10' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${on ? 'text-yellow-500' : 'text-gray-400'}`} />
                <div className="flex-grow">
                  <p className="font-black text-sm leading-tight text-black dark:text-white">{title}</p>
                  <p className="text-[11px] font-medium opacity-50">{sub}</p>
                </div>
                <span className={`shrink-0 w-11 h-6 rounded-full p-0.5 transition-colors ${on ? 'bg-yellow-400' : 'bg-black/15 dark:bg-white/15'}`}>
                  <span className={`grid place-items-center w-5 h-5 rounded-full bg-white shadow transition-transform ${on ? 'translate-x-5' : 'translate-x-0'}`}>
                    {on && <Check className="w-3 h-3 text-yellow-500" />}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Launch */}
        <button
          onClick={launch}
          className="w-full flex items-center justify-center gap-3 bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl border-2 border-black/10 shadow-xl hover:scale-[1.02] active:scale-95 transition-all"
        >
          <Play className="w-6 h-6 fill-current" />
          {mode === 'session' ? t('games.blindtest.lobby.launch_session', { defaultValue: 'Lancer la session ({{length}})', length }) : t('games.blindtest.lobby.launch_single', 'Lancer le Blind Test')}
        </button>
      </Card>
    </div>
  );
};

export default BlindtestLobbyPage;
