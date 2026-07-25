import React from 'react';
import { Zap, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ApiCreativeFusion } from '../../../features/social/types/profileTypes';

interface ProfileFusionsCardProps {
  topFusions?: ApiCreativeFusion[];
}

export const ProfileFusionsCard: React.FC<ProfileFusionsCardProps> = ({ topFusions }) => {
  const { t } = useTranslation();

  return (
    <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 md:p-8">
      <h3 className="mb-6 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5]">
        <Zap className="h-4 w-4 text-[#5D7FD3]" />
        {t('social.profile.favorite_fusions', 'Fusions Favorites')}
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {topFusions?.map((fusion: ApiCreativeFusion, i: number) => (
          <div
            key={i}
            className="group relative aspect-video cursor-pointer overflow-hidden rounded-xl border border-[#F4F1E8]/10 transition-colors hover:border-[#5D7FD3]"
          >
            <img
              src={fusion.image_url ?? undefined}
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
              alt=""
              loading="lazy"
              decoding="async"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-[#0B0C10]/30 to-transparent" />
            <p className="absolute bottom-3 left-3 w-[80%] truncate text-[8px] font-black uppercase text-[#F4F1E8]">
              {fusion.title_a} x {fusion.title_b}
            </p>
          </div>
        ))}
      </div>
      {(!topFusions || topFusions.length === 0) && (
        <p className="py-8 text-center italic text-[#8F94A5]/50">
          {t('social.profile.empty_collection', 'La collection est vide.')}
        </p>
      )}
      <div className="mt-6 border-t border-[#F4F1E8]/10 pt-6">
        <Link
          to="/social/collection/"
          className="text-[10px] font-black uppercase tracking-widest text-[#5D7FD3] no-underline transition-colors hover:text-[#F4F1E8]"
        >
          {t('social.profile.go_collection', 'Accéder à la collection')}
          <ArrowRight className="ml-1 inline h-3 w-3" />
        </Link>
      </div>
    </section>
  );
};
