import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sparkles,
  Check,
  Lock,
  Calendar,
  Globe,
  Tags,
  Shapes,
  Clapperboard,
  CaseSensitive,
  Hash,
  ScrollText,
} from 'lucide-react';
import type { ClassicHintKey, ClassicHints } from '../../../types';

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

interface Props {
  hintKeys: ClassicHintKey[];
  hints: ClassicHints | undefined;
  guessCount: number;
  onReveal: (key: ClassicHintKey) => void;
  revealing: boolean;
}

export const ClassicHintsPanel: React.FC<Props> = ({
  hintKeys,
  hints,
  guessCount,
  onReveal,
  revealing,
}) => {
  const { t } = useTranslation();
  return (
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
                    onClick={() => onReveal(key)}
                    disabled={revealing}
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
  );
};
