import React from 'react';
import { Bookmark, Sparkles, Image as ImageIcon, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CreativeFusion } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

const CollectionPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: fusions, isLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['collection'],
    queryFn: () => apiClient('/api/v1/social/collection/'),
  });

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="relative mb-12 text-center">
          <div className="flex items-center justify-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              集
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              Nexus social · Galerie
            </span>
          </div>
          <h1 className="font-manga mt-4 text-5xl font-black italic uppercase tracking-tighter text-[#F4F1E8]">
            {t('social.collection.title_my', 'MA')}{' '}
            <span className="text-[#E8442B]">
              {t('social.collection.title_collection', 'COLLECTION')}
            </span>
          </h1>
        </header>

        {!fusions || fusions.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 bg-[#0F1016] py-20 text-center">
            <Bookmark className="mx-auto mb-6 h-20 w-20 text-[#8F94A5]/25" />
            <p className="text-xl font-bold italic uppercase tracking-widest text-[#8F94A5]">
              {t(
                'social.collection.empty_gallery',
                "Votre galerie est vide. Explorez l'Archetypist !",
              )}
            </p>
            <Button
              as={Link}
              to="/forge/"
              variant="primary"
              size="lg"
              className="mt-8 border-none !bg-[#E8442B] px-12 font-manga italic !text-[#F4F1E8] hover:!bg-[#c93a24]"
            >
              {t('social.collection.create_fusion', 'CRÉER UNE FUSION')}
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {fusions.map((fusion: CreativeFusion) => (
              <div
                key={fusion.id}
                className="group overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-colors hover:border-[#F4F1E8]/20"
              >
                <div className="aspect-[3/4] relative overflow-hidden bg-[#0B0C10]">
                  {fusion.image_url ? (
                    <img
                      src={fusion.image_url}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                      alt={fusion.title_a}
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-[#8F94A5]/25">
                      <ImageIcon className="w-16 h-16" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-transparent to-transparent opacity-60 transition-opacity group-hover:opacity-80"></div>
                </div>

                <div className="p-6">
                  <h3 className="font-manga mb-4 truncate text-lg font-black italic uppercase leading-none text-[#F4F1E8]">
                    {fusion.title_a} <span className="text-[#FDB913]">×</span> {fusion.title_b}
                  </h3>
                  <div className="flex items-center justify-between">
                    <Badge
                      variant="neutral"
                      className="!bg-[#F4F1E8]/5 !border-[#F4F1E8]/10 text-[8px] !text-[#8F94A5]"
                    >
                      {fusion.media_type_a}
                    </Badge>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="rounded-xl border-none p-2 text-[#E8442B] hover:bg-[#E8442B]/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        className="rounded-xl border-none p-2 text-[#FDB913] hover:bg-[#FDB913]/10"
                      >
                        <Sparkles className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CollectionPage;
