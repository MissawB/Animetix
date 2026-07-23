import React from 'react';
import { useTranslation } from 'react-i18next';
import { Swords, Trophy } from 'lucide-react';
import { VsBattleResult as VsBattleResultData } from '../../../types';

/** Échelle de puissance en encres de la forge : plus c'est haut, plus c'est chaud. */
const getTierColor = (value: number) => {
  if (value >= 90) return 'text-[#E8442B]';
  if (value >= 70) return 'text-[#FDB913]';
  if (value >= 50) return 'text-[#F4F1E8]';
  return 'text-[#8F94A5]';
};

interface Props {
  result: VsBattleResultData;
  onReset: () => void;
}

export const VsBattleResult: React.FC<Props> = ({ result, onReset }) => {
  const { t } = useTranslation();
  return (
    <div className="space-y-12 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 hidden md:block">
          <div className="w-16 h-16 -rotate-3 rounded-[4px] border-2 border-[#E8442B] bg-[#0B0C10] flex items-center justify-center text-3xl font-bold leading-none text-[#E8442B] shadow-[0_0_30px_rgba(232,68,43,0.35)]">
            闘
          </div>
        </div>

        {[result.character_a, result.character_b].map((char, idx) => (
          <div
            key={idx}
            className={`relative overflow-hidden rounded-2xl border ${
              idx === 0
                ? 'border-[#E8442B]/40 bg-[#E8442B]/5'
                : 'border-[#F4F1E8]/25 bg-[#F4F1E8]/5'
            }`}
          >
            {char.image_url && (
              <div
                className="absolute inset-0 opacity-15 bg-cover bg-center grayscale"
                style={{ backgroundImage: `url(${char.image_url})` }}
              />
            )}
            <div className="relative z-10 p-8 md:p-10">
              <span
                className={`mb-4 inline-block text-[9px] font-black uppercase tracking-[0.25em] ${
                  idx === 0 ? 'text-[#E8442B]' : 'text-[#F4F1E8]/70'
                }`}
              >
                {char.franchise}
              </span>
              <h3 className="text-3xl font-black uppercase italic mb-6 manga-font text-[#F4F1E8]">
                {char.name}
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-[#0B0C10]/70 rounded-xl border border-[#F4F1E8]/10">
                  <span className="text-[10px] uppercase font-black text-[#8F94A5] block mb-1">
                    Power Tier
                  </span>
                  <span
                    className={`text-xl font-black italic ${getTierColor(char.stats.tier_value)}`}
                  >
                    {char.stats.tier}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-[#0B0C10]/70 rounded-xl border border-[#F4F1E8]/10">
                    <span className="text-[10px] uppercase font-black text-[#8F94A5] block mb-1">
                      {t('games.vs_battle.speed', 'Vitesse')}
                    </span>
                    <span className="text-xs font-bold truncate block text-[#F4F1E8]">
                      {char.stats.speed}
                    </span>
                  </div>
                  <div className="p-4 bg-[#0B0C10]/70 rounded-xl border border-[#F4F1E8]/10">
                    <span className="text-[10px] uppercase font-black text-[#8F94A5] block mb-1">
                      {t('games.vs_battle.durability', 'Endurance')}
                    </span>
                    <span className="text-xs font-bold truncate block text-[#F4F1E8]">
                      {char.stats.durability}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="relative overflow-hidden rounded-2xl border border-[#E8442B]/40 bg-[#0F1016] p-10 md:p-14">
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Trophy className="w-40 h-40" />
        </div>
        <div className="text-center relative z-10">
          <h2 className="text-[10px] font-black uppercase tracking-[0.4em] text-[#8F94A5] mb-4">
            {t('games.vs_battle.referee_verdict', "Verdict de l'Arbitre IA")}
          </h2>
          <div className="text-4xl md:text-6xl font-black italic uppercase manga-font mb-8 bg-gradient-to-br from-[#FDB913] to-[#E8442B] bg-clip-text text-transparent">
            {t('games.vs_battle.x_wins', { defaultValue: '{{name}} GAGNE', name: result.winner })}
          </div>
          <p className="text-lg leading-relaxed text-[#F4F1E8]/80 font-medium italic max-w-3xl mx-auto">
            "{result.verdict_summary}"
          </p>
        </div>
      </div>

      <div className="text-center pt-4">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-3 px-12 py-4 rounded-full border border-[#F4F1E8]/20 bg-transparent text-[#F4F1E8] uppercase font-black italic tracking-widest transition-colors hover:border-[#FDB913] cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
        >
          <Swords className="w-5 h-5" aria-hidden="true" />
          {t('games.vs_battle.new_challenge', 'NOUVEAU CHALLENGE')}
        </button>
      </div>
    </div>
  );
};
