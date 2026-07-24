import React from 'react';
import { useTranslation } from 'react-i18next';
import { Target, Check } from 'lucide-react';
import type { ClassicGuess, ClassicReason } from '../../../types';

export interface HeatConfig {
  label: string;
  bar: string;
  chip: string;
  glow: string;
}

interface Props {
  guesses: ClassicGuess[];
  heatOf: (g: ClassicGuess) => HeatConfig;
}

export const ClassicGuessTrail: React.FC<Props> = ({ guesses, heatOf }) => {
  const { t } = useTranslation();
  const guessCount = guesses.length;

  return (
    <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 md:p-7">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-[11px] font-black uppercase tracking-widest text-[#8F94A5]">
          {t('games.classic.game.your_attempts', 'Vos tentatives')}
        </h3>
        {guessCount > 0 && (
          <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]/70">
            {t('games.classic.game.closest_first', 'les plus proches en tête')}
          </span>
        )}
      </div>

      {guessCount === 0 ? (
        <div className="text-center py-12">
          <Target className="w-12 h-12 mx-auto mb-4 text-[#8F94A5]/30" />
          <p className="font-manga font-black italic uppercase text-[#F4F1E8]/50 text-sm">
            {t('games.classic.game.no_lead_title', "Aucune piste pour l'instant")}
          </p>
          <p className="text-xs font-bold text-[#8F94A5]/70 mt-1">
            {t(
              'games.classic.game.no_lead_desc',
              "Lancez une première tentative pour ouvrir l'enquête.",
            )}
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {guesses.map((g, i) => {
            const heat = heatOf(g);
            const score = Math.round(g.score ?? 0);
            return (
              <li
                key={`${g.title}-${i}`}
                className={`rounded-2xl border p-4 animate-fade-in ${
                  g.is_correct
                    ? 'border-[#FDB913] bg-[#FDB913]/[0.08]'
                    : `border-[#F4F1E8]/5 bg-[#F4F1E8]/[0.02] ${heat.glow}`
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2.5">
                  <div className="min-w-0">
                    <p className="font-black truncate leading-tight text-[#F4F1E8]">{g.title}</p>
                    {g.title_english && g.title_english !== g.title && (
                      <p className="text-[11px] font-bold text-[#8F94A5] truncate">
                        {g.title_english}
                      </p>
                    )}
                  </div>
                  {g.is_correct ? (
                    <span className="shrink-0 inline-flex items-center gap-1.5 text-xs font-black uppercase px-3 py-1.5 rounded-full bg-[#FDB913] text-[#0B0C10]">
                      <Check className="w-3.5 h-3.5" /> {t('games.classic.game.found', 'Trouvé')}
                    </span>
                  ) : (
                    <div className="shrink-0 flex items-center gap-2">
                      <span
                        className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full ${heat.chip}`}
                      >
                        {heat.label}
                      </span>
                      <span className="text-lg font-black tabular-nums w-12 text-right text-[#F4F1E8]">
                        {score}%
                      </span>
                    </div>
                  )}
                </div>
                {!g.is_correct && (
                  <div className="h-2 rounded-full bg-[#F4F1E8]/5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${heat.bar} transition-all duration-700`}
                      style={{ width: `${Math.max(4, score)}%` }}
                    />
                  </div>
                )}
                {(g.reasons ?? []).length > 0 && (
                  <ul className="mt-2 space-y-1 pl-1">
                    {(g.reasons ?? []).map((reason: ClassicReason) => (
                      <li key={reason.kind} className="text-xs text-[#8F94A5]">
                        <span className="font-semibold text-[#F4F1E8]/80">{reason.label}</span>
                        {reason.detail.length > 0 && (
                          <span className="text-[#8F94A5]"> — {reason.detail.join(' · ')}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};
