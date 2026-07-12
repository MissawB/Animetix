import React from 'react';
import { useTranslation } from 'react-i18next';

const MAX_TIER = 12;
const LIMITER_DAMAGE = 4096;

interface Props {
  tier: number;
  limiterBreak: boolean;
}

/**
 * Twelve rungs, each worth twice the one below. The doubling is drawn, not stated:
 * the rung grows with the damage, so the climb is visibly steeper than it is long.
 */
export const TierLadder: React.FC<Props> = ({ tier, limiterBreak }) => {
  const { t } = useTranslation();
  const rungs = Array.from({ length: MAX_TIER }, (_, i) => MAX_TIER - i); // 12 at the top

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-3">
        {t('games.world_boss.ladder', 'Échelle de puissance')}
      </h3>

      {limiterBreak && (
        <div className="mb-3 rounded-xl border border-red-500 bg-red-600/15 px-4 py-3 text-center">
          <div className="text-sm font-black uppercase italic tracking-widest text-red-400">
            {t('games.world_boss.limiter_break', 'Brisage de Limiteur')}
          </div>
          <div className="font-mono text-3xl font-black text-red-300">{LIMITER_DAMAGE}</div>
        </div>
      )}

      {rungs.map((n) => {
        const damage = 2 ** (n - 1);
        const current = n === tier && !limiterBreak;
        const cleared = n < tier;
        return (
          <div
            key={n}
            aria-label={t('games.world_boss.tier', 'Palier {{n}}', { n })}
            data-current={current}
            className={`flex items-center justify-between rounded-lg border px-3 transition-colors ${
              current
                ? 'border-amber-400 bg-amber-400/15 text-amber-300'
                : cleared
                  ? 'border-white/10 bg-white/5 text-gray-400'
                  : 'border-white/5 text-gray-700'
            }`}
            style={{ height: `${18 + n * 2}px` }} // the rung grows with what it is worth
          >
            {/* The rung index is prefixed ("#1") so it never collides, in text
                queries or at a glance, with the damage value it sits beside —
                at tier 1 the two would otherwise both read bare "1". */}
            <span className="font-mono text-xs font-bold">{`#${n}`}</span>
            <span className="font-mono text-xs font-black">{damage}</span>
          </div>
        );
      })}
    </div>
  );
};
