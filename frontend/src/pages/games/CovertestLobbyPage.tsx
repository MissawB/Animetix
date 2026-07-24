import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DifficultySelector } from './components/DifficultySelector';
import { useTranslation } from 'react-i18next';
import { BookImage, Layers, Image as ImageIcon, Play, Hash, Check, PenTool } from 'lucide-react';

type Mode = 'session' | 'single';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Tryhard';

const LENGTHS = [5, 10, 20, 50];

type Origin = '' | 'ja' | 'fr';

const ACTIVE_SEL = 'border-[#FDB913] bg-[#FDB913]/10';
const IDLE_SEL = 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50';
const ACTIVE_DIFF = 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]';

const CovertestLobbyPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const DIFFICULTIES: {
    key: Difficulty;
    label: string;
    sub: string;
    tries: number;
    active: string;
  }[] = useMemo(
    () => [
      {
        key: 'Easy',
        label: t('games.covertest.lobby.difficulty_easy', 'Facile'),
        sub: t('games.covertest.lobby.tries_count', { defaultValue: '{{count}} essais', count: 6 }),
        tries: 6,
        active: ACTIVE_DIFF,
      },
      {
        key: 'Normal',
        label: t('games.covertest.lobby.difficulty_normal', 'Normal'),
        sub: t('games.covertest.lobby.tries_count', { defaultValue: '{{count}} essais', count: 4 }),
        tries: 4,
        active: ACTIVE_DIFF,
      },
      {
        key: 'Hard',
        label: t('games.covertest.lobby.difficulty_hard', 'Difficile'),
        sub: t('games.covertest.lobby.tries_count', { defaultValue: '{{count}} essais', count: 3 }),
        tries: 3,
        active: ACTIVE_DIFF,
      },
      {
        key: 'Impossible',
        label: t('games.covertest.lobby.difficulty_impossible', 'Impossible'),
        sub: t('games.covertest.lobby.tries_count', { defaultValue: '{{count}} essais', count: 2 }),
        tries: 2,
        active: ACTIVE_DIFF,
      },
      {
        key: 'Tryhard',
        label: t('games.covertest.lobby.difficulty_tryhard', 'Tryhard'),
        sub: t('games.covertest.lobby.distortions', 'Distorsions'),
        tries: 3,
        active: 'border-[#E8442B] bg-[#E8442B]/10 text-[#E8442B]',
      },
    ],
    [t],
  );

  const ORIGINS: { key: Origin; label: string; sub: string }[] = useMemo(
    () => [
      {
        key: '',
        label: t('games.covertest.lobby.origin_auto', 'Auto'),
        sub: t('games.covertest.lobby.origin_auto_sub', 'Toutes origines'),
      },
      {
        key: 'ja',
        label: t('games.covertest.lobby.origin_ja', '🇯🇵 Japon'),
        sub: t('games.covertest.lobby.origin_ja_sub', 'Couvertures JP'),
      },
      {
        key: 'fr',
        label: t('games.covertest.lobby.origin_fr', '🇫🇷 France'),
        sub: t('games.covertest.lobby.origin_fr_sub', 'Éditions FR'),
      },
    ],
    [t],
  );
  const [mode, setMode] = useState<Mode>('session');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [length, setLength] = useState(10);
  const [guessVolume, setGuessVolume] = useState(false);
  const [guessAuthor, setGuessAuthor] = useState(false);
  const [origin, setOrigin] = useState<Origin>('');

  const launch = () =>
    navigate('/covertest/play/', {
      state: {
        mode,
        difficulty,
        length: mode === 'session' ? length : 1,
        guessVolume,
        guessAuthor,
        origin: origin || undefined,
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
              隠
            </span>
            <span className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              <BookImage className="w-3.5 h-3.5" /> Cover Quest
            </span>
          </div>
          <h1 className="font-manga relative text-5xl md:text-6xl font-black italic tracking-tighter uppercase text-[#F4F1E8] leading-none">
            {t('games.covertest.lobby.title_part1', 'DEVINE')}{' '}
            <span className="text-[#E8442B]">
              {t('games.covertest.lobby.title_part2', 'LE MANGA')}
            </span>
          </h1>
          <p className="relative mt-4 text-base font-medium text-[#8F94A5]">
            {t(
              'games.covertest.lobby.subtitle',
              'Une couverture floutée se précise à chaque essai. Reconnais-la avant la fin.',
            )}
          </p>
        </header>

        <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-10 space-y-10">
          {/* Mode */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-4">
              {t('games.covertest.lobby.mode_label', 'Mode de jeu')}
            </p>
            <div className="grid grid-cols-2 gap-4">
              {[
                {
                  key: 'session' as Mode,
                  icon: Layers,
                  title: t('games.covertest.lobby.mode_session', 'Session'),
                  sub: t(
                    'games.covertest.lobby.mode_session_sub',
                    'Enchaîne plusieurs couvertures',
                  ),
                },
                {
                  key: 'single' as Mode,
                  icon: ImageIcon,
                  title: t('games.covertest.lobby.mode_single', 'Une couverture'),
                  sub: t('games.covertest.lobby.mode_single_sub', 'Une seule manche'),
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
                {t('games.covertest.lobby.length_label', 'Durée de la session')}
              </p>
              <div className="grid grid-cols-4 gap-2">
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

          {/* Difficulté */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-1">
              {t('games.covertest.lobby.difficulty_label', 'Difficulté')}
            </p>
            <p className="text-[11px] text-[#8F94A5] mb-4">
              {t(
                'games.covertest.lobby.difficulty_hint_part1',
                "Nombre d'essais et vitesse de révélation.",
              )}{' '}
              <span className="text-[#E8442B] font-bold">
                {t('games.covertest.lobby.difficulty_tryhard', 'Tryhard')}
              </span>{' '}
              {t(
                'games.covertest.lobby.difficulty_hint_part2',
                'ajoute des distorsions aléatoires (bruit, N&B, couleurs inversées…) en plus du flou.',
              )}
            </p>
            <DifficultySelector
              options={DIFFICULTIES}
              value={difficulty}
              onChange={setDifficulty}
              gridClassName="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3"
              hoverClassName="hover:border-[#FDB913]/50"
            />
          </div>

          {/* Origine des couvertures */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-1">
              {t('games.covertest.lobby.origin_label', 'Origine des couvertures')}
            </p>
            <p className="text-[11px] text-[#8F94A5] mb-4">
              {t('games.covertest.lobby.origin_hint_part1', "Choisis l'édition à deviner.")}{' '}
              <span className="font-bold text-[#F4F1E8]">
                {t('games.covertest.lobby.origin_auto', 'Auto')}
              </span>{' '}
              {t(
                'games.covertest.lobby.origin_hint_part2',
                'pioche parmi toutes les origines disponibles.',
              )}
            </p>
            <div className="grid grid-cols-3 gap-3">
              {ORIGINS.map((o) => (
                <button
                  key={o.key || 'auto'}
                  onClick={() => setOrigin(o.key)}
                  aria-pressed={origin === o.key}
                  className={`flex flex-col items-center gap-1 py-4 rounded-2xl border-2 transition-colors ${
                    origin === o.key
                      ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]'
                      : 'border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#FDB913]/50'
                  }`}
                >
                  <span className="font-black italic uppercase tracking-wide text-sm">
                    {o.label}
                  </span>
                  <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">
                    {o.sub}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Objectifs bonus */}
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-1">
              {t('games.covertest.lobby.bonus_label', 'Objectifs bonus')}
            </p>
            <p className="text-[11px] text-[#8F94A5] mb-4">
              {t(
                'games.covertest.lobby.bonus_hint',
                'Une fois le manga trouvé, gagne des points en plus.',
              )}
            </p>
            <div className="space-y-3">
              {[
                {
                  on: guessVolume,
                  set: setGuessVolume,
                  icon: Hash,
                  title: t('games.covertest.lobby.bonus_volume', 'Deviner le tome'),
                  sub: t(
                    'games.covertest.lobby.bonus_volume_sub',
                    'Le numéro de volume de la couverture · +30 pts',
                  ),
                },
                {
                  on: guessAuthor,
                  set: setGuessAuthor,
                  icon: PenTool,
                  title: t('games.covertest.lobby.bonus_author', 'Deviner le mangaka'),
                  sub: t('games.covertest.lobby.bonus_author_sub', "L'auteur de l'œuvre · +30 pts"),
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
              ? t('games.covertest.lobby.launch_session', {
                  defaultValue: 'Lancer la session ({{length}})',
                  length,
                })
              : t('games.covertest.lobby.launch_single', 'Lancer Cover Quest')}
          </button>
        </section>
      </div>
    </div>
  );
};

export default CovertestLobbyPage;
