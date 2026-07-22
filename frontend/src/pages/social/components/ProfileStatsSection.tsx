import React from 'react';
import { Zap, Award, User as UserIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon }) => (
  <div className="bg-gray-50 dark:bg-black/20 p-8 rounded-[2rem] text-center border border-black/5 dark:border-white/5 shadow-inner">
    <div className="w-12 h-12 bg-white dark:bg-[#0f0f1a] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-md border border-black/5 dark:border-white/5">
      {icon}
    </div>
    <div className="text-3xl font-black text-blue-600 dark:text-blue-400 mb-1">{value}</div>
    <div className="text-[10px] font-black uppercase opacity-40 tracking-widest text-black dark:text-white">
      {label}
    </div>
  </div>
);

interface ProfileStatsSectionProps {
  xp?: number;
  achievementsCount?: number;
  collectionCount?: number;
}

export const ProfileStatsSection: React.FC<ProfileStatsSectionProps> = ({
  xp = 0,
  achievementsCount = 0,
  collectionCount = 0,
}) => {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
      <StatCard
        label={t('social.profile.xp')}
        value={xp}
        icon={<Zap className="text-orange-500" />}
      />
      <StatCard
        label={t('social.profile.achievements')}
        value={achievementsCount}
        icon={<Award className="text-yellow-500" />}
      />
      <StatCard
        label={t('social.profile.collection')}
        value={collectionCount}
        icon={<UserIcon className="text-blue-500" />}
      />
    </div>
  );
};
