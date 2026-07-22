import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, BookOpen, Star, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/Button';
import { WatchButton } from './WatchButton';
import { LibraryButton } from './LibraryButton';
import { ShareButton } from './ShareButton';
import type { MediaDetail } from '../../../types';

const MEDIA_JP: Record<string, string> = {
  anime: 'アニメ',
  manga: 'マンガ',
  game: 'ゲーム',
  movie: '映画',
};

interface DetailHeroProps {
  item: MediaDetail;
  mediaType: string;
  itemId: string;
}

export const DetailHero: React.FC<DetailHeroProps> = ({ item, mediaType, itemId }) => {
  const { t } = useTranslation();
  const isManga = mediaType.toLowerCase() === 'manga';
  const subTitles = [item.title_native, item.title_english].filter(Boolean);
  const jp = MEDIA_JP[mediaType.toLowerCase()];

  return (
    <header className="relative w-full overflow-hidden border-b border-[#F4F1E8]/10 bg-[#0B0C10] text-[#F4F1E8]">
      <div className="pointer-events-none absolute inset-0">
        <img
          src={item.image}
          className="h-full w-full scale-110 object-cover opacity-20 blur-2xl"
          alt=""
          fetchPriority="high"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#0B0C10]/60 via-[#0B0C10]/85 to-[#0B0C10]" />
        <div className="explore-halftone absolute inset-0" aria-hidden />
      </div>
      <div className="relative z-10 mx-auto flex min-h-[55vh] w-full max-w-7xl flex-col px-4 pt-10 sm:px-6">
        <Link
          to="/explore/"
          className="group inline-flex items-center gap-2 self-start text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913]"
        >
          <ArrowLeft className="h-3 w-3 transition-transform group-hover:-translate-x-1" />{' '}
          {t('media.detail.back_nexus_link', 'Retour au Nexus')}
        </Link>
        <div className="mt-auto flex flex-col items-start gap-8 pb-10 pt-12 md:flex-row md:items-end">
          <div className="relative flex-none">
            <span
              className="absolute -inset-1.5 translate-x-3 translate-y-3 rounded-sm border-2 border-[#E8442B]/60"
              aria-hidden
            />
            <img
              src={item.image}
              className="relative aspect-[2/3] w-44 rounded-sm object-cover shadow-[0_24px_60px_-12px_rgba(0,0,0,0.8)] ring-1 ring-[#F4F1E8]/15 md:w-52"
              alt={item.title}
              fetchPriority="high"
              decoding="async"
            />
            <span className="explore-stamp absolute -left-2 -top-2 -rotate-3 bg-[#0B0C10]/90">
              {mediaType.toUpperCase()}
              {jp && (
                <span aria-hidden className="ml-1.5 font-normal">
                  {jp}
                </span>
              )}
            </span>
          </div>
          <div className="min-w-0 space-y-4">
            <div className="flex flex-wrap gap-2">
              {item.genres?.map((g: string) => (
                <span
                  key={g}
                  className="rounded-sm border border-[#F4F1E8]/15 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]"
                >
                  {g}
                </span>
              ))}
            </div>
            <h1 className="font-manga text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
              {item.title}
            </h1>
            {subTitles.length > 0 && (
              <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F4F1E8]/40 md:text-base">
                {subTitles.join(' · ')}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-6 text-sm font-bold">
              {item.rating != null && (
                <span className="flex items-center gap-1.5 text-lg font-black text-[#FDB913]">
                  <Star className="h-4 w-4" fill="currentColor" aria-hidden="true" />
                  {item.rating.toFixed(1)}
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
                    / 100
                  </span>
                </span>
              )}
              <span className="text-[#F4F1E8]/80">{item.year || 'TBA'}</span>
              {item.popularity != null && (
                <span
                  className="flex items-center gap-2 text-[#8F94A5]"
                  title={t('media.detail.popularity', 'Popularité')}
                >
                  <TrendingUp className="h-4 w-4 text-[#E8442B]" aria-hidden="true" />
                  {item.popularity.toLocaleString('fr-FR')}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-3 pt-2">
              {isManga ? (
                <>
                  <Button
                    as={Link}
                    to={`/media/manga/${itemId}/1/`}
                    variant="primary"
                    className="group border-none !bg-[#E8442B] text-[#F4F1E8] hover:!bg-[#c93a24]"
                  >
                    <BookOpen className="h-5 w-5" /> {t('media.detail.read_manga', 'LIRE LE MANGA')}
                  </Button>
                  <LibraryButton mediaId={itemId} />
                </>
              ) : (
                <WatchButton title={item.title} platforms={item.streaming_platforms ?? []} />
              )}
              <ShareButton title={item.title} />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
