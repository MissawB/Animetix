import React from 'react';
import { Award, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ApiAchievement } from '../../../features/social/types/profileTypes';

interface ProfileAchievementsCardProps {
  recentAchievements?: ApiAchievement[];
}

export const ProfileAchievementsCard: React.FC<ProfileAchievementsCardProps> = ({
  recentAchievements,
}) => {
  const { t } = useTranslation();

  return (
    <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 md:p-8">
      <h3 className="mb-6 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5]">
        <Award className="h-4 w-4 text-[#FDB913]" />
        {t('social.profile.recent_achievements', 'Succès Récents')}
      </h3>
      <div className="space-y-3">
        {recentAchievements?.map((ach: ApiAchievement, i: number) => (
          <div
            key={i}
            className="group flex items-center gap-4 rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-4 transition-colors hover:border-[#FDB913]/40"
          >
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#FDB913]/10 text-[#FDB913] transition-transform group-hover:scale-110">
              <Award className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-black uppercase italic text-[#F4F1E8]">
                {ach.name}
              </p>
              <p className="truncate text-[10px] font-bold uppercase text-[#8F94A5]">
                {ach.description}
              </p>
            </div>
          </div>
        ))}
        {(!recentAchievements || recentAchievements.length === 0) && (
          <p className="py-8 text-center italic text-[#8F94A5]/50">
            {t('social.profile.no_achievements', 'Aucun succès débloqué pour le moment.')}
          </p>
        )}
      </div>
      <div className="mt-6 border-t border-[#F4F1E8]/10 pt-6">
        <Link
          to="/achievements/"
          className="text-[10px] font-black uppercase tracking-widest text-[#FDB913] no-underline transition-colors hover:text-[#F4F1E8]"
        >
          {t('social.profile.view_all_achievements', 'Voir tous les succès')}
          <ArrowRight className="ml-1 inline h-3 w-3" />
        </Link>
      </div>
    </section>
  );
};
