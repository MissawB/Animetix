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
  year: { icon: Calendar, tone: 'text-[#FDB913]' },
  origin: { icon: Globe, tone: 'text-[#FDB913]' },
  tags: { icon: Tags, tone: 'text-[#FDB913]' },
  genres: { icon: Shapes, tone: 'text-[#FDB913]' },
  studio: { icon: Clapperboard, tone: 'text-[#FDB913]' },
  letter: { icon: CaseSensitive, tone: 'text-[#FDB913]' },
  words: { icon: Hash, tone: 'text-[#FDB913]' },
  desc: { icon: ScrollText, tone: 'text-[#FDB913]' },
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
    <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest text-[#8F94A5] mb-5">
        <Sparkles className="w-4 h-4 text-[#FDB913]" />{' '}
        {t('games.classic.game.hints_title', 'Indices')}
      </div>
      <div className="space-y-3">
        {hintKeys.length === 0 && (
          <p className="text-xs font-bold text-[#8F94A5]/70 text-center py-4">
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
              className={`rounded-2xl border p-3.5 transition-colors ${
                revealed
                  ? 'border-[#FDB913]/40 bg-[#FDB913]/[0.06]'
                  : 'border-[#F4F1E8]/5 bg-[#F4F1E8]/[0.02]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-[#F4F1E8]">
                  <Icon className={`w-4 h-4 ${revealed ? meta.tone : 'text-[#8F94A5]/50'}`} />
                  {label}
                </span>
                {revealed ? (
                  <Check className="w-4 h-4 text-[#FDB913]" />
                ) : canReveal ? (
                  <button
                    type="button"
                    onClick={() => onReveal(key)}
                    disabled={revealing}
                    className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-[#FDB913] text-[#0B0C10] hover:bg-[#e0a50f] active:scale-95 transition-colors disabled:opacity-50"
                  >
                    {t('games.classic.game.reveal', 'Révéler')}
                  </button>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]">
                    <Lock className="w-3 h-3" />{' '}
                    {t('games.classic.game.unlock_at', {
                      defaultValue: '{{count}} essais',
                      count: unlockAt,
                    })}
                  </span>
                )}
              </div>

              {revealed && h?.value && (
                <p className="mt-2 text-sm font-semibold leading-snug text-[#FDB913]">{h.value}</p>
              )}
              {!revealed && !canReveal && (
                <div className="mt-2.5 h-1 rounded-full bg-[#F4F1E8]/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[#FDB913]/60 transition-all duration-500"
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
