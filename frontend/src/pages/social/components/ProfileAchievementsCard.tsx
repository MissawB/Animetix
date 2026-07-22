import React from 'react';
import { Award, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { ApiAchievement } from '../../../features/social/types/profileTypes';

interface ProfileAchievementsCardProps {
  recentAchievements?: ApiAchievement[];
}

export const ProfileAchievementsCard: React.FC<ProfileAchievementsCardProps> = ({
  recentAchievements,
}) => {
  const { t } = useTranslation();

  return (
    <Card padding="lg" className="bg-gray-50 dark:bg-black/20 border-none shadow-xl">
      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
        <Award className="w-4 h-4 text-yellow-500" />{' '}
        {t('social.profile.recent_achievements', 'Succès Récents')}
      </h3>
      <div className="space-y-4">
        {recentAchievements?.map((ach: ApiAchievement, i: number) => (
          <div
            key={i}
            className="flex items-center gap-4 p-4 bg-white dark:bg-white/5 rounded-2xl border border-black/5 dark:border-white/5 group hover:border-yellow-400 transition-all shadow-sm"
          >
            <div className="w-10 h-10 bg-yellow-500/10 rounded-xl flex items-center justify-center text-yellow-500 group-hover:scale-110 transition-transform">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-black italic uppercase">{ach.name}</p>
              <p className="text-[10px] opacity-40 uppercase font-bold">{ach.description}</p>
            </div>
          </div>
        ))}
        {(!recentAchievements || recentAchievements.length === 0) && (
          <p className="text-center py-8 opacity-20 italic">
            {t('social.profile.no_achievements', 'Aucun succès débloqué pour le moment.')}
          </p>
        )}
      </div>
      <div className="mt-8 pt-8 border-t border-black/5 dark:border-white/5">
        <Link
          to="/achievements/"
          className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline"
        >
          {t('social.profile.view_all_achievements', 'Voir tous les succès')}{' '}
          <ArrowRight className="inline w-3 h-3 ml-1" />
        </Link>
      </div>
    </Card>
  );
};
