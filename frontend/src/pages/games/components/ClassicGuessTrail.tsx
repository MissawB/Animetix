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
    <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-6 md:p-7 shadow-token-card">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-[11px] font-black uppercase tracking-widest opacity-40">
          {t('games.classic.game.your_attempts', 'Vos tentatives')}
        </h3>
        {guessCount > 0 && (
          <span className="text-[10px] font-black uppercase tracking-widest opacity-30">
            {t('games.classic.game.closest_first', 'les plus proches en tête')}
          </span>
        )}
      </div>

      {guessCount === 0 ? (
        <div className="text-center py-12">
          <Target className="w-12 h-12 mx-auto mb-4 opacity-15" />
          <p className="font-black italic uppercase opacity-30 text-sm">
            {t('games.classic.game.no_lead_title', "Aucune piste pour l'instant")}
          </p>
          <p className="text-xs font-bold opacity-25 mt-1">
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
                    ? 'border-green-500 bg-green-500/[0.08]'
                    : `border-black/5 dark:border-white/5 bg-black/[0.02] dark:bg-white/[0.02] ${heat.glow}`
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2.5">
                  <div className="min-w-0">
                    <p className="font-black truncate leading-tight">{g.title}</p>
                    {g.title_english && g.title_english !== g.title && (
                      <p className="text-[11px] font-bold opacity-40 truncate">{g.title_english}</p>
                    )}
                  </div>
                  {g.is_correct ? (
                    <span className="shrink-0 inline-flex items-center gap-1.5 text-xs font-black uppercase px-3 py-1.5 rounded-full bg-green-500 text-white">
                      <Check className="w-3.5 h-3.5" /> {t('games.classic.game.found', 'Trouvé')}
                    </span>
                  ) : (
                    <div className="shrink-0 flex items-center gap-2">
                      <span
                        className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full ${heat.chip}`}
                      >
                        {heat.label}
                      </span>
                      <span className="text-lg font-black tabular-nums w-12 text-right">
                        {score}%
                      </span>
                    </div>
                  )}
                </div>
                {!g.is_correct && (
                  <div className="h-2 rounded-full bg-black/5 dark:bg-white/5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${heat.bar} transition-all duration-700`}
                      style={{ width: `${Math.max(4, score)}%` }}
                    />
                  </div>
                )}
                {(g.reasons ?? []).length > 0 && (
                  <ul className="mt-2 space-y-1 pl-1">
                    {(g.reasons ?? []).map((reason: ClassicReason) => (
                      <li key={reason.kind} className="text-xs text-gray-600 dark:text-gray-400">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">
                          {reason.label}
                        </span>
                        {reason.detail.length > 0 && (
                          <span className="text-gray-500 dark:text-gray-500">
                            {' '}
                            — {reason.detail.join(' · ')}
                          </span>
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
