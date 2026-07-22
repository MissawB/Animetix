import React from 'react';
import { Zap, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { ApiCreativeFusion } from '../../../features/social/types/profileTypes';

interface ProfileFusionsCardProps {
  topFusions?: ApiCreativeFusion[];
}

export const ProfileFusionsCard: React.FC<ProfileFusionsCardProps> = ({ topFusions }) => {
  const { t } = useTranslation();

  return (
    <Card padding="lg" className="bg-gray-50 dark:bg-black/20 border-none shadow-xl">
      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
        <Zap className="w-4 h-4 text-blue-500" />{' '}
        {t('social.profile.favorite_fusions', 'Fusions Favorites')}
      </h3>
      <div className="grid grid-cols-2 gap-4">
        {topFusions?.map((fusion: ApiCreativeFusion, i: number) => (
          <div
            key={i}
            className="aspect-video rounded-xl overflow-hidden relative group cursor-pointer border border-black/5 dark:border-white/5 hover:border-blue-500 transition-all shadow-sm"
          >
            <img
              src={fusion.image_url ?? undefined}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
              alt=""
              loading="lazy"
              decoding="async"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
            <p className="absolute bottom-3 left-3 text-[8px] font-black uppercase text-white truncate w-[80%]">
              {fusion.title_a} x {fusion.title_b}
            </p>
          </div>
        ))}
      </div>
      {(!topFusions || topFusions.length === 0) && (
        <p className="text-center py-8 opacity-20 italic">
          {t('social.profile.empty_collection', 'La collection est vide.')}
        </p>
      )}
      <div className="mt-8 pt-8 border-t border-black/5 dark:border-white/5">
        <Link
          to="/social/collection/"
          className="text-[10px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 no-underline"
        >
          {t('social.profile.go_collection', 'Accéder à la collection')}{' '}
          <ArrowRight className="inline w-3 h-3 ml-1" />
        </Link>
      </div>
    </Card>
  );
};
