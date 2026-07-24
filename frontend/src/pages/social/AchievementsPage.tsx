import React from 'react';
import { CheckCircle2, Trophy } from 'lucide-react';
import { useAchievements } from '../../features/social/hooks/useAchievements';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';

interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  rarity: string;
  xp_reward: number;
  is_unlocked?: boolean;
}

const AchievementsPage: React.FC = () => {
  const { t } = useTranslation();
  const { data: achievements, isLoading, isError } = useAchievements();

  if (isLoading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  if (isError || !achievements)
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-[#0B0C10] text-center">
        <p className="font-manga text-2xl font-black uppercase italic text-[#E8442B]">
          {t('common.error')}
        </p>
      </div>
    );

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="relative mb-12 text-center">
          <div
            className="explore-halftone pointer-events-none absolute inset-x-0 -top-8 h-36"
            aria-hidden
          />
          <div className="relative mb-4 flex items-center justify-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              章
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('social.achievements.eyebrow', 'Registre · Hauts Faits')}
            </span>
          </div>
          <h1 className="font-manga relative text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-5xl">
            {t('social.achievements.title', 'Grimoire des Hauts Faits')}
          </h1>
          <p className="relative mt-4 text-xs font-black uppercase tracking-widest text-[#8F94A5]">
            {t('social.achievements.subtitle', "Votre légende s'écrit à chaque secret découvert.")}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
          {achievements.map((ach: Achievement) => (
            <div
              key={ach.id}
              className={`rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-5 transition-colors ${
                ach.is_unlocked ? 'hover:border-[#FDB913]/50' : 'opacity-60 grayscale'
              }`}
            >
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-20 w-20 flex-none items-center justify-center rounded-2xl ${
                    ach.is_unlocked
                      ? 'bg-[#FDB913] text-[#0B0C10]'
                      : 'border border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5]'
                  }`}
                >
                  <Trophy className="h-8 w-8" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <h5 className="font-manga text-sm font-black uppercase italic leading-none text-[#F4F1E8]">
                      {ach.name}
                    </h5>
                    <span className="flex-none rounded-full border border-[#F4F1E8]/10 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                      {ach.rarity}
                    </span>
                  </div>
                  <p className="mb-2 text-xs font-medium leading-relaxed text-[#8F94A5]">
                    {ach.description}
                  </p>
                  <div
                    className={`flex items-center text-[10px] font-black uppercase tracking-tighter ${
                      ach.is_unlocked ? 'text-[#FDB913]' : 'text-[#8F94A5]'
                    }`}
                  >
                    <CheckCircle2 className="mr-1 h-3 w-3" />{' '}
                    {ach.is_unlocked
                      ? t('social.achievements.unlocked', 'Débloqué')
                      : t('social.achievements.locked', 'Verrouillé (+{{xp}} XP)', {
                          xp: ach.xp_reward,
                        })}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AchievementsPage;
