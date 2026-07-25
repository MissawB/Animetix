import React from 'react';
import { Zap, Award, Boxes } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  accent: string;
  glyph: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, accent, glyph }) => (
  <div className="group relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 transition-colors hover:border-[#F4F1E8]/25">
    <span
      className="font-manga pointer-events-none absolute -bottom-4 -right-2 text-6xl font-black italic leading-none opacity-[0.06] select-none"
      style={{ color: accent }}
      aria-hidden
    >
      {glyph}
    </span>
    <div
      className="mb-4 grid h-11 w-11 place-items-center rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-transform group-hover:scale-110"
      style={{ color: accent }}
    >
      {icon}
    </div>
    <div className="mb-1 text-3xl font-black italic tabular-nums" style={{ color: accent }}>
      {value}
    </div>
    <div className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">{label}</div>
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
    <div className="mb-12 grid grid-cols-1 gap-5 md:grid-cols-3">
      <StatCard
        label={t('social.profile.xp')}
        value={xp}
        icon={<Zap className="h-5 w-5 fill-current" />}
        accent="#FDB913"
        glyph="験"
      />
      <StatCard
        label={t('social.profile.achievements')}
        value={achievementsCount}
        icon={<Award className="h-5 w-5" />}
        accent="#E8442B"
        glyph="功"
      />
      <StatCard
        label={t('social.profile.collection')}
        value={collectionCount}
        icon={<Boxes className="h-5 w-5" />}
        accent="#5D7FD3"
        glyph="蔵"
      />
    </div>
  );
};
