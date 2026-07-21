import React from 'react';
import { useTranslation } from 'react-i18next';
import { Target } from 'lucide-react';
import type { HeatConfig } from './ClassicGuessTrail';

interface Props {
  howTo: { t: string; d: string }[];
  heat: Record<string, HeatConfig>;
  heatLegend: { key: string; range: string }[];
}

export const ClassicHowToPanel: React.FC<Props> = ({ howTo, heat, heatLegend }) => {
  const { t } = useTranslation();
  return (
    <div className="rounded-[2rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-6 shadow-token-card">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-widest opacity-40 mb-5">
        <Target className="w-4 h-4 text-blue-500" />{' '}
        {t('games.classic.game.how_to_title', 'Comment jouer')}
      </div>
      <ol className="space-y-4">
        {howTo.map((s, i) => (
          <li key={s.t} className="flex gap-3.5">
            <span className="shrink-0 w-7 h-7 rounded-xl bg-blue-500/10 text-blue-500 grid place-items-center font-black text-sm">
              {i + 1}
            </span>
            <div>
              <p className="font-black text-sm leading-tight">{s.t}</p>
              <p className="text-xs font-medium opacity-55 leading-snug mt-0.5">{s.d}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="mt-6 pt-5 border-t border-black/5 dark:border-white/10">
        <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-3">
          {t('games.classic.game.heat_scale', 'Échelle de chaleur')}
        </p>
        <div className="grid grid-cols-4 gap-2">
          {heatLegend.map(({ key, range }) => (
            <div key={key} className="text-center">
              <div className={`h-1.5 rounded-full ${heat[key].bar} mb-1.5`} />
              <p className="text-[10px] font-black uppercase leading-none">{heat[key].label}</p>
              <p className="text-[9px] font-bold opacity-40 tabular-nums mt-0.5">{range}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
