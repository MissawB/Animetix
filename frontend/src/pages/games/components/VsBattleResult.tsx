import React from 'react';
import { useTranslation } from 'react-i18next';
import { Swords, Trophy } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { VsBattleResult as VsBattleResultData } from '../../../types';

const getTierColor = (value: number) => {
  if (value >= 90) return 'text-red-500';
  if (value >= 70) return 'text-orange-500';
  if (value >= 50) return 'text-yellow-500';
  if (value >= 30) return 'text-green-500';
  return 'text-blue-500';
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
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
          <div className="w-20 h-20 bg-red-600 rounded-full flex items-center justify-center border-4 border-black shadow-[0_0_40px_rgba(220,38,38,0.5)]">
            <Swords className="w-10 h-10 text-white" />
          </div>
        </div>

        {[result.character_a, result.character_b].map((char, idx) => (
          <Card
            key={idx}
            className={`relative overflow-hidden rounded-[3rem] border-white/10 ${idx === 0 ? 'bg-red-950/20' : 'bg-blue-950/20'}`}
          >
            {char.image_url && (
              <div
                className="absolute inset-0 opacity-20 bg-cover bg-center grayscale group-hover:grayscale-0 transition-all duration-700"
                style={{ backgroundImage: `url(${char.image_url})` }}
              />
            )}
            <div className="relative z-10 p-10">
              <Badge
                variant="neutral"
                className="mb-4 bg-white/5 border-white/10 text-[8px] font-black tracking-widest"
              >
                {char.franchise}
              </Badge>
              <h3 className="text-3xl font-black uppercase italic mb-6 manga-font">{char.name}</h3>
              <div className="space-y-6">
                <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                  <span className="text-[10px] uppercase font-black opacity-30 block mb-1">
                    Power Tier
                  </span>
                  <span
                    className={`text-xl font-black italic ${getTierColor(char.stats.tier_value)}`}
                  >
                    {char.stats.tier}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                    <span className="text-[10px] uppercase font-black opacity-30 block mb-1">
                      {t('games.vs_battle.speed', 'Vitesse')}
                    </span>
                    <span className="text-xs font-bold truncate block">{char.stats.speed}</span>
                  </div>
                  <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                    <span className="text-[10px] uppercase font-black opacity-30 block mb-1">
                      {t('games.vs_battle.durability', 'Endurance')}
                    </span>
                    <span className="text-xs font-bold truncate block">
                      {char.stats.durability}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card
        padding="lg"
        className="border-4 border-red-600/50 bg-navy-900 rounded-[4rem] relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Trophy className="w-40 h-40" />
        </div>
        <div className="text-center relative z-10">
          <h2 className="text-xs font-black uppercase tracking-[0.5em] opacity-40 mb-4">
            {t('games.vs_battle.referee_verdict', "Verdict de l'Arbitre IA")}
          </h2>
          <div className="text-6xl font-black italic uppercase text-red-500 manga-font mb-8 text-glow">
            {t('games.vs_battle.x_wins', { defaultValue: '{{name}} GAGNE', name: result.winner })}
          </div>
          <p className="text-lg leading-relaxed text-white/80 font-medium italic max-w-3xl mx-auto">
            "{result.verdict_summary}"
          </p>
        </div>
      </Card>

      <div className="text-center pt-8">
        <Button
          size="lg"
          variant="outline"
          onClick={onReset}
          className="px-12 py-4 border-white/10 rounded-2xl uppercase font-black italic tracking-widest"
        >
          {t('games.vs_battle.new_challenge', 'NOUVEAU CHALLENGE')}
        </Button>
      </div>
    </div>
  );
};
