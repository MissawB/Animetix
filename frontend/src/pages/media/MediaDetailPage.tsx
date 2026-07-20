import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Tag, Cpu, Network, Sparkles, Mic, Users } from 'lucide-react';
import { useMediaDetail } from '../../features/media/hooks/useMediaDetail';
import { useMediaCharacters } from '../../features/media/hooks/useMediaCharacters';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { ChapterList } from '../../features/manga-reader/components/ChapterList';
import { useTranslation } from 'react-i18next';
import { DetailHero } from './components/DetailHero';
import { SectionHeader } from './components/SectionHeader';
import { SeiyuuGrid } from './components/SeiyuuGrid';
import { CharacterGrid } from './components/CharacterGrid';
import { RelatedCarousel } from './components/RelatedCarousel';
import { MediaDetail } from '../../types';

const MediaDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { mediaType, itemId } = useParams<{ mediaType: string; itemId: string }>();
  const {
    data: item,
    isLoading,
    isError,
  } = useMediaDetail(mediaType || 'Anime', itemId || '') as {
    data: MediaDetail | undefined;
    isLoading: boolean;
    isError: boolean;
  };
  const { data: charactersData } = useMediaCharacters(mediaType, itemId);
  const characters = charactersData?.characters ?? [];

  if (isLoading)
    return (
      <div className="max-w-7xl mx-auto px-6 py-16">
        <CardSkeleton />
      </div>
    );

  if (isError || !item)
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <h2 className="text-4xl font-black italic manga-font text-red-500 mb-6 uppercase">
          {t('media.detail.not_found', 'Œuvre introuvable')}
        </h2>
        <p className="text-gray-500 font-bold uppercase tracking-widest mb-12">
          {t('media.detail.not_found_desc', 'Le Nexus s’est peut-être effondré…')}
        </p>
        <Button as={Link} to="/explore/" variant="outline">
          {t('media.detail.back_nexus', 'RETOURNER AU NEXUS')}
        </Button>
      </div>
    );

  return (
    <AnimatedPage>
      <DetailHero item={item} mediaType={mediaType || 'Anime'} itemId={itemId || ''} />

      <div className="max-w-7xl mx-auto px-6 pb-24 relative z-10 space-y-12">
        <section className="pt-4">
          <SectionHeader title="Synopsis" icon={Tag} iconClassName="text-blue-400" />
          <p className="text-sm leading-relaxed font-medium max-w-3xl">
            {item.description ||
              t('media.detail.no_synopsis', 'Aucun synopsis disponible dans le Nexus.')}
          </p>
        </section>

        {characters.length > 0 && (
          <section>
            <SectionHeader
              title={t('media.detail.characters', 'Personnages')}
              icon={Users}
              iconClassName="text-blue-400"
            />
            <CharacterGrid characters={characters} />
          </section>
        )}

        {mediaType?.toLowerCase() === 'manga' && itemId && (
          <ChapterList mediaId={itemId} mediaTitle={item.title} />
        )}

        <section>
          <SectionHeader
            title={t('media.detail.creative_team', 'Équipe Créative')}
            icon={Sparkles}
            iconClassName="text-blue-400"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-4 bg-gray-900 rounded-2xl border border-white/5">
              <span className="text-[10px] font-black text-gray-500 uppercase">Studio</span>
              <span className="font-bold italic text-sm text-white">
                {item.studios?.[0] || 'N/A'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 bg-gray-900 rounded-2xl border border-white/5">
              <span className="text-[10px] font-black text-gray-500 uppercase">
                {t('media.detail.author', 'Auteur')}
              </span>
              <span className="font-bold italic text-sm text-yellow-400">
                {item.author || t('media.detail.unknown', 'Inconnu')}
              </span>
            </div>
          </div>
        </section>

        {item.seiyuu && item.seiyuu.length > 0 && (
          <section>
            <SectionHeader
              title={t('media.detail.seiyuu', 'Seiyuu')}
              icon={Mic}
              iconClassName="text-blue-400"
            />
            <SeiyuuGrid seiyuu={item.seiyuu} />
          </section>
        )}

        {item.micro_tags && item.micro_tags.length > 0 && (
          <section>
            <SectionHeader
              title={t('media.detail.micro_tags', 'Micro-Tags IA')}
              icon={Cpu}
              iconClassName="text-blue-400"
            />
            <div className="flex flex-wrap gap-2">
              {item.micro_tags.slice(0, 10).map((tag: string) => (
                <Badge
                  key={tag}
                  variant="neutral"
                  className="bg-gray-900 text-gray-300 text-[8px] uppercase tracking-tighter"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </section>
        )}

        {item.related_items && item.related_items.length > 0 && (
          <section className="!mt-20">
            <SectionHeader
              title={t('media.detail.related_works', 'Œuvres Liées dans le Graphe')}
              icon={Network}
              iconClassName="text-blue-400"
            />
            <RelatedCarousel items={item.related_items} mediaType={mediaType || 'Anime'} />
          </section>
        )}
      </div>

      <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </AnimatedPage>
  );
};

export default MediaDetailPage;
