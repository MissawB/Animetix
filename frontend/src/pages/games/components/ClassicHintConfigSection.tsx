import React from 'react';
import {
  Trophy,
  SlidersHorizontal,
  Skull,
  Calendar,
  Globe,
  Tags,
  Shapes,
  Clapperboard,
  CaseSensitive,
  Hash,
  ScrollText,
  ArrowUp,
  ArrowDown,
  Check,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ClassicHintKey } from '../../../types';

export type HintMode = 'classic' | 'custom' | 'tryhard';

interface ClassicHintConfigSectionProps {
  hintMode: HintMode;
  setHintMode: (mode: HintMode) => void;
  hintOrder: ClassicHintKey[];
  enabled: Record<ClassicHintKey, boolean>;
  move: (index: number, dir: -1 | 1) => void;
  toggle: (key: ClassicHintKey) => void;
  unlockAt: (key: ClassicHintKey) => number;
  classicPreset: ClassicHintKey[];
  unlockStep: number;
}

export const ClassicHintConfigSection: React.FC<ClassicHintConfigSectionProps> = ({
  hintMode,
  setHintMode,
  hintOrder,
  enabled,
  move,
  toggle,
  unlockAt,
  classicPreset,
  unlockStep,
}) => {
  const { t } = useTranslation();

  const HINT_MODES: { key: HintMode; label: string; sub: string; icon: React.ElementType }[] = [
    {
      key: 'classic',
      label: t('games.classic.lobby.modes.classic.label', 'Classique'),
      sub: t('games.classic.lobby.modes.classic.sub', '4 indices clés'),
      icon: Trophy,
    },
    {
      key: 'custom',
      label: t('games.classic.lobby.modes.custom.label', 'Personnalisé'),
      sub: t('games.classic.lobby.modes.custom.sub', 'À ta façon'),
      icon: SlidersHorizontal,
    },
    {
      key: 'tryhard',
      label: t('games.classic.lobby.modes.tryhard.label', 'Tryhard'),
      sub: t('games.classic.lobby.modes.tryhard.sub', 'Aucun indice'),
      icon: Skull,
    },
  ];

  const HINT_DEFS: Record<
    ClassicHintKey,
    { label: string; desc: string; icon: React.ElementType; tone: string }
  > = {
    year: {
      label: t('games.classic.lobby.hints.year.label', 'Année de sortie'),
      desc: t('games.classic.lobby.hints.year.desc', 'Année de parution'),
      icon: Calendar,
      tone: 'text-blue-500',
    },
    origin: {
      label: t('games.classic.lobby.hints.origin.label', 'Origine'),
      desc: t('games.classic.lobby.hints.origin.desc', "Œuvre / pays d'origine"),
      icon: Globe,
      tone: 'text-teal-500',
    },
    tags: {
      label: t('games.classic.lobby.hints.tags.label', 'Tags'),
      desc: t('games.classic.lobby.hints.tags.desc', 'Principaux thèmes'),
      icon: Tags,
      tone: 'text-yellow-500',
    },
    genres: {
      label: t('games.classic.lobby.hints.genres.label', 'Genres'),
      desc: t('games.classic.lobby.hints.genres.desc', 'Catégories principales'),
      icon: Shapes,
      tone: 'text-orange-500',
    },
    studio: {
      label: t('games.classic.lobby.hints.studio.label', 'Studio'),
      desc: t('games.classic.lobby.hints.studio.desc', "Studio d'animation / éditeur"),
      icon: Clapperboard,
      tone: 'text-purple-500',
    },
    letter: {
      label: t('games.classic.lobby.hints.letter.label', 'Première lettre'),
      desc: t('games.classic.lobby.hints.letter.desc', 'La lettre initiale du titre'),
      icon: CaseSensitive,
      tone: 'text-pink-500',
    },
    words: {
      label: t('games.classic.lobby.hints.words.label', 'Nombre de mots'),
      desc: t('games.classic.lobby.hints.words.desc', 'Combien de mots dans le titre'),
      icon: Hash,
      tone: 'text-cyan-500',
    },
    desc: {
      label: t('games.classic.lobby.hints.desc.label', 'Description'),
      desc: t('games.classic.lobby.hints.desc.desc', 'Extrait du synopsis'),
      icon: ScrollText,
      tone: 'text-green-500',
    },
  };

  return (
    <>
      <div className="grid grid-cols-3 gap-3 mb-5">
        {HINT_MODES.map(({ key, label, sub, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setHintMode(key)}
            aria-pressed={hintMode === key}
            className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${
              hintMode === key
                ? 'border-blue-500 bg-blue-500/10 shadow-lg'
                : 'border-black/5 dark:border-white/10 hover:border-blue-500/50'
            }`}
          >
            <Icon className={`w-6 h-6 ${hintMode === key ? 'text-blue-500' : 'text-gray-400'}`} />
            <span className="manga-font text-sm text-black dark:text-white leading-none">
              {label}
            </span>
            <span className="text-[9px] font-bold uppercase tracking-widest text-gray-400 text-center">
              {sub}
            </span>
          </button>
        ))}
      </div>

      {hintMode === 'classic' && (
        <ul className="space-y-2.5">
          {classicPreset.map((key, i) => {
            const def = HINT_DEFS[key];
            const Icon = def.icon;
            return (
              <li
                key={key}
                className="flex items-center gap-3 rounded-2xl border-2 border-blue-500/30 bg-blue-500/[0.05] p-3"
              >
                <Icon className={`w-5 h-5 shrink-0 ${def.tone}`} />
                <div className="min-w-0 flex-grow">
                  <p className="font-black text-sm leading-tight truncate">{def.label}</p>
                  <p className="text-[11px] font-medium opacity-50 truncate">{def.desc}</p>
                </div>
                <span className="shrink-0 text-[10px] font-black uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2.5 py-1 rounded-full tabular-nums">
                  {t('games.classic.lobby.tries_count', {
                    defaultValue: '{{count}} essais',
                    count: (i + 1) * unlockStep,
                  })}
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {hintMode === 'tryhard' && (
        <div className="rounded-2xl border-2 border-red-500/30 bg-red-500/[0.06] p-6 text-center">
          <Skull className="w-9 h-9 text-red-500 mx-auto mb-3" />
          <p className="font-black italic uppercase text-red-500">
            {t('games.classic.lobby.tryhard_title', 'Aucun indice')}
          </p>
          <p className="text-xs font-bold opacity-50 mt-1">
            {t(
              'games.classic.lobby.tryhard_desc',
              'Juste toi, ton instinct et la chaleur des tentatives. Pour les vrais.',
            )}
          </p>
        </div>
      )}

      {hintMode === 'custom' && (
        <>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-4">
            {t('games.classic.lobby.custom_help', {
              defaultValue:
                'Active les indices voulus et range-les : ils se débloqueront dans cet ordre, un toutes les {{step}} tentatives.',
              step: unlockStep,
            })}
          </p>
          <ul className="space-y-2.5">
            {hintOrder.map((key, i) => {
              const def = HINT_DEFS[key];
              const Icon = def.icon;
              const on = enabled[key];
              return (
                <li
                  key={key}
                  className={`flex items-center gap-3 rounded-2xl border-2 p-3 transition-all ${
                    on
                      ? 'border-blue-500/40 bg-blue-500/[0.05]'
                      : 'border-black/5 dark:border-white/10 opacity-60'
                  }`}
                >
                  <div className="flex flex-col">
                    <button
                      onClick={() => move(i, -1)}
                      disabled={i === 0}
                      aria-label={t('games.classic.lobby.aria_move_up', {
                        defaultValue: 'Monter {{label}}',
                        label: def.label,
                      })}
                      className="p-0.5 rounded text-gray-400 hover:text-blue-500 disabled:opacity-20 disabled:hover:text-gray-400 transition-colors"
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => move(i, 1)}
                      disabled={i === hintOrder.length - 1}
                      aria-label={t('games.classic.lobby.aria_move_down', {
                        defaultValue: 'Descendre {{label}}',
                        label: def.label,
                      })}
                      className="p-0.5 rounded text-gray-400 hover:text-blue-500 disabled:opacity-20 disabled:hover:text-gray-400 transition-colors"
                    >
                      <ArrowDown className="w-4 h-4" />
                    </button>
                  </div>

                  <Icon className={`w-5 h-5 shrink-0 ${on ? def.tone : 'text-gray-400'}`} />

                  <div className="min-w-0 flex-grow">
                    <p className="font-black text-sm leading-tight truncate">{def.label}</p>
                    <p className="text-[11px] font-medium opacity-50 truncate">{def.desc}</p>
                  </div>

                  {on && (
                    <span className="shrink-0 text-[10px] font-black uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2.5 py-1 rounded-full tabular-nums">
                      {t('games.classic.lobby.tries_count', {
                        defaultValue: '{{count}} essais',
                        count: unlockAt(key),
                      })}
                    </span>
                  )}

                  <button
                    onClick={() => toggle(key)}
                    role="switch"
                    aria-checked={on}
                    aria-label={`${on ? t('games.classic.lobby.aria_disable', 'Désactiver') : t('games.classic.lobby.aria_enable', 'Activer')} ${def.label}`}
                    className={`shrink-0 w-11 h-6 rounded-full p-0.5 transition-colors ${on ? 'bg-blue-500' : 'bg-black/15 dark:bg-white/15'}`}
                  >
                    <span
                      className={`grid place-items-center w-5 h-5 rounded-full bg-white shadow transition-transform ${on ? 'translate-x-5' : 'translate-x-0'}`}
                    >
                      {on && <Check className="w-3 h-3 text-blue-500" />}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </>
  );
};
