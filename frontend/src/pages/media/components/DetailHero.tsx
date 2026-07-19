import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  Bookmark,
  Calendar,
  Heart,
  Play,
  Share2,
  TrendingUp,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import type { MediaDetail } from '../../../types';

interface DetailHeroProps {
  item: MediaDetail;
  mediaType: string;
  itemId: string;
}

export const DetailHero: React.FC<DetailHeroProps> = ({ item, mediaType, itemId }) => {
  const { t } = useTranslation();
  const isManga = mediaType.toLowerCase() === 'manga';
  const subTitles = [item.title_native, item.title_english].filter(Boolean);

  return (
    <header className="relative min-h-[55vh] w-full overflow-hidden flex flex-col bg-navy-950 text-white">
      <div className="absolute inset-0 pointer-events-none">
        <img
          src={item.image}
          className="w-full h-full object-cover blur-2xl scale-110 opacity-30"
          alt=""
          fetchPriority="high"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-950/60 to-navy-950" />
      </div>
      <div className="relative z-10 max-w-7xl mx-auto w-full px-6 pt-10 flex-1 flex flex-col">
        <Link
          to="/explore/"
          className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors no-underline group self-start"
        >
          <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" />{' '}
          {t('media.detail.back_nexus_link', 'Retour au Nexus')}
        </Link>
        <div className="mt-auto flex flex-col md:flex-row items-start md:items-end gap-8 pb-10 pt-12">
          <div className="relative flex-none">
            <img
              src={item.image}
              className="w-44 md:w-52 aspect-[2/3] object-cover rounded-xl shadow-2xl border border-white/10"
              alt={item.title}
              fetchPriority="high"
              decoding="async"
            />
            <Badge
              variant="primary"
              className="absolute top-3 left-3 shadow-xl bg-blue-600 font-black italic uppercase tracking-tighter"
            >
              {mediaType.toUpperCase()}
            </Badge>
          </div>
          <div className="space-y-4 min-w-0">
            <div className="flex flex-wrap gap-2">
              {item.genres?.map((g: string) => (
                <Badge
                  key={g}
                  variant="neutral"
                  className="bg-white/5 border-white/10 text-[9px] uppercase tracking-widest font-black italic"
                >
                  {g}
                </Badge>
              ))}
            </div>
            <h1 className="text-4xl md:text-6xl font-black italic manga-font tracking-tighter uppercase leading-none text-glow">
              {item.title}
            </h1>
            {subTitles.length > 0 && (
              <p className="text-sm md:text-base font-bold opacity-40 uppercase tracking-[0.2em]">
                {subTitles.join(' · ')}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-6 text-sm font-bold italic">
              <span className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-blue-400" aria-hidden="true" />
                {item.year || 'TBA'}
              </span>
              {item.popularity != null && (
                <span
                  className="flex items-center gap-2"
                  title={t('media.detail.popularity', 'Popularité')}
                >
                  <TrendingUp className="w-4 h-4 text-blue-400" aria-hidden="true" />
                  {item.popularity.toLocaleString('fr-FR')}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-3 pt-2">
              {isManga ? (
                <Button
                  as={Link}
                  to={`/media/manga/${itemId}/1/`}
                  variant="primary"
                  className="bg-anime-accent text-white border-none group"
                >
                  <BookOpen className="w-5 h-5" /> {t('media.detail.read_manga', 'LIRE LE MANGA')}
                </Button>
              ) : (
                <Button variant="primary" className="bg-yellow-400 text-black border-none group">
                  <Play className="w-5 h-5" /> {t('media.detail.watch', 'VOIR')}
                </Button>
              )}
              <Button variant="primary" className="bg-white/10 text-white border-none group">
                <Bookmark className="w-5 h-5 group-hover:fill-current" />{' '}
                {t('media.detail.add', 'AJOUTER')}
              </Button>
              <Button
                variant="outline"
                className="border-white/10 hover:bg-red-500/10 hover:text-red-500 group"
              >
                <Heart className="w-5 h-5 group-hover:fill-current" />{' '}
                {t('media.detail.favorites', 'FAVORIS')}
              </Button>
              <Button
                variant="outline"
                aria-label={t('media.detail.share_club', 'Partager dans le club')}
                className="border-white/5 bg-white/5 hover:bg-white/10"
              >
                <Share2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
