import React from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  TrendingUp,
  Network,
  Play,
  Bookmark,
  Heart,
  Share2,
  BookOpen,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';
import type { MediaDetail } from '../../../types';

interface DetailHeroProps {
  item: MediaDetail;
  mediaType: string;
  itemId: string;
}

export const DetailHero: React.FC<DetailHeroProps> = ({ item, mediaType, itemId }) => {
  const { t } = useTranslation();

  return (
    <div className="relative">
      {/* Background Decor */}
      <div className="absolute inset-0 top-0 h-[600px] overflow-hidden pointer-events-none opacity-20">
        <img
          src={item.image}
          className="w-full h-full object-cover blur-3xl scale-110"
          alt=""
          loading="lazy"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-950 to-navy-950" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
          {/* Poster & Actions */}
          <div className="lg:col-span-4 space-y-12">
            <div className="relative group">
              {/* Frame stylisée */}
              <div className="absolute -inset-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
              <Card
                padding="none"
                className="relative overflow-hidden rounded-2xl shadow-2xl border-white/10"
              >
                <img
                  src={item.image}
                  className="w-full aspect-[2/3] object-cover"
                  alt={item.title}
                  loading="lazy"
                  decoding="async"
                />
              </Card>
              <Badge
                variant="primary"
                className="absolute top-6 left-6 shadow-xl bg-blue-600 font-black italic uppercase tracking-tighter"
              >
                {mediaType?.toUpperCase()}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {mediaType?.toLowerCase() === 'manga' ? (
                <Button
                  as={Link}
                  to={`/media/manga/${itemId}/1/`}
                  variant="primary"
                  fullWidth
                  className="bg-anime-accent text-white border-none py-6 group col-span-2 shadow-[0_0_20px_rgba(255,0,120,0.3)]"
                >
                  <BookOpen className="w-5 h-5 group-hover:scale-110 transition-transform" />{' '}
                  {t('media.detail.read_manga', 'LIRE LE MANGA')}
                </Button>
              ) : (
                <Button
                  variant="primary"
                  fullWidth
                  className="bg-yellow-400 text-black border-none py-6 group"
                >
                  <Play className="w-5 h-5 group-hover:scale-110 transition-transform" />{' '}
                  {t('media.detail.watch', 'VOIR')}
                </Button>
              )}
              <Button
                variant="primary"
                fullWidth
                className="bg-white/10 text-white border-none py-6 group"
              >
                <Bookmark className="w-5 h-5 group-hover:fill-current" />{' '}
                {t('media.detail.add', 'AJOUTER')}
              </Button>
              <Button
                variant="outline"
                fullWidth
                className="py-6 border-white/10 hover:bg-red-500/10 hover:text-red-500 group"
              >
                <Heart className="w-5 h-5 group-hover:fill-current" />{' '}
                {t('media.detail.favorites', 'FAVORIS')}
              </Button>
            </div>

            <Button
              variant="outline"
              fullWidth
              className="py-4 border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10"
            >
              <Share2 className="w-3 h-3" /> {t('media.detail.share_club', 'Partager dans le club')}
            </Button>
          </div>

          {/* Info Content */}
          <div className="lg:col-span-8 space-y-12">
            <header>
              <div className="flex flex-wrap gap-2 mb-6">
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
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none text-glow">
                {item.title}
              </h1>
              {item.title_english && (
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em] mb-4">
                  {item.title_english}
                </p>
              )}

              <div className="flex flex-wrap gap-8 items-center mt-10">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-black opacity-30 uppercase">
                      {t('media.detail.release', 'Sortie')}
                    </p>
                    <p className="font-bold italic">{item.year || 'TBA'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-500">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-black opacity-30 uppercase">
                      {t('media.detail.popularity', 'Popularité')}
                    </p>
                    <p className="font-bold italic">{`#${item.popularity || 'N/A'}`}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-purple-500/10 rounded-xl text-purple-500">
                    <Network className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-black opacity-30 uppercase">Knowledge Graph</p>
                    <p className="font-bold italic">Deep Indexed</p>
                  </div>
                </div>
              </div>
            </header>
          </div>
        </div>
      </div>
    </div>
  );
};
