import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Calendar, 
  TrendingUp, 
  Tag, 
  ArrowLeft, 
  Play, 
  Network,
  Sparkles,
  Bookmark,
  Heart,
  Share2,
  BookOpen
} from 'lucide-react';
import { useMediaDetail } from '../../features/media/hooks/useMediaDetail';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { ChapterList } from '../../features/manga-reader/components/ChapterList';
import { useTranslation } from 'react-i18next';

import { RelatedItem, MediaDetail } from '../../types';

const MediaDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { mediaType, itemId } = useParams<{ mediaType: string; itemId: string }>();
  const { data: item, isLoading, isError } = useMediaDetail(mediaType || 'Anime', itemId || '') as { data: MediaDetail | undefined, isLoading: boolean, isError: boolean };

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  if (isError || !item) return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
          <h2 className="text-4xl font-black italic manga-font text-red-500 mb-6 uppercase">{t('media.detail.not_found', 'Œuvre introuvable')}</h2>
          <p className="text-gray-500 font-bold uppercase tracking-widest mb-12">{t('media.detail.not_found_desc', 'Le Nexus s\'est peut-être effondré...')}</p>
          <Button as={Link} to="/explore/" variant="outline">{t('media.detail.back_nexus', 'RETOURNER AU NEXUS')}</Button>
      </div>
  );

  return (
    <AnimatedPage>
      {/* Background Decor */}
      <div className="absolute inset-0 top-0 h-[600px] overflow-hidden pointer-events-none opacity-20">
          <img src={item.image} className="w-full h-full object-cover blur-3xl scale-110" alt="" loading="lazy" decoding="async" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-950 to-navy-950" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        {/* Navigation */}
        <Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors mb-12 no-underline group">
            <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> {t('media.detail.back_nexus_link', 'Retour au Nexus')}
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
            {/* Poster & Actions */}
            <div className="lg:col-span-4 space-y-12">
                <div className="relative group">
                    {/* Frame stylisée */}
                    <div className="absolute -inset-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                    <Card padding="none" className="relative overflow-hidden rounded-2xl shadow-2xl border-white/10">
                        <img src={item.image} className="w-full aspect-[2/3] object-cover" alt={item.title} loading="lazy" decoding="async" />
                    </Card>
                    <Badge variant="primary" className="absolute top-6 left-6 shadow-xl bg-blue-600 font-black italic uppercase tracking-tighter">
                        {mediaType?.toUpperCase()}
                    </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    {mediaType?.toLowerCase() === 'manga' ? (
                        <Button as={Link} to={`/media/manga/${itemId}/1/`} variant="primary" fullWidth className="bg-anime-accent text-white border-none py-6 group col-span-2 shadow-[0_0_20px_rgba(255,0,120,0.3)]">
                            <BookOpen className="w-5 h-5 group-hover:scale-110 transition-transform" /> {t('media.detail.read_manga', 'LIRE LE MANGA')}
                        </Button>
                    ) : (
                        <Button variant="primary" fullWidth className="bg-yellow-400 text-black border-none py-6 group">
                            <Play className="w-5 h-5 group-hover:scale-110 transition-transform" /> {t('media.detail.watch', 'VOIR')}
                        </Button>
                    )}
                    <Button variant="primary" fullWidth className="bg-white/10 text-white border-none py-6 group">
                        <Bookmark className="w-5 h-5 group-hover:fill-current" /> {t('media.detail.add', 'AJOUTER')}
                    </Button>
                    <Button variant="outline" fullWidth className="py-6 border-white/10 hover:bg-red-500/10 hover:text-red-500 group">
                        <Heart className="w-5 h-5 group-hover:fill-current" /> {t('media.detail.favorites', 'FAVORIS')}
                    </Button>
                </div>
                
                <Button variant="outline" fullWidth className="py-4 border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest hover:bg-white/10">
                    <Share2 className="w-3 h-3" /> {t('media.detail.share_club', 'Partager dans le club')}
                </Button>
            </div>

            {/* Info Content */}
            <div className="lg:col-span-8 space-y-12">
                <header>
                    <div className="flex flex-wrap gap-2 mb-6">
                        {item.genres?.map((g: string) => (
                            <Badge key={g} variant="neutral" className="bg-white/5 border-white/10 text-[9px] uppercase tracking-widest font-black italic">{g}</Badge>
                        ))}
                    </div>
                    <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none text-glow">
                        {item.title}
                    </h1>
                    {item.title_english && <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em] mb-4">{item.title_english}</p>}
                    
                    <div className="flex flex-wrap gap-8 items-center mt-10">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                                <Calendar className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="text-[10px] font-black opacity-30 uppercase">{t('media.detail.release', 'Sortie')}</p>
                                <p className="font-bold italic">{item.year || 'TBA'}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-500">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="text-[10px] font-black opacity-30 uppercase">{t('media.detail.popularity', 'Popularité')}</p>
                                <p className="font-bold italic">#{item.popularity || 'N/A'}</p>
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

                {/* Synopsis */}
                <section>
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Tag className="w-4 h-4 text-blue-400" /> Synopsis
                    </h3>
                    <Card padding="lg" className="bg-white/5 border-white/5 shadow-inner">
                        <p className="text-sm leading-relaxed opacity-80 font-medium italic">
                            {item.description || t('media.detail.no_synopsis', 'Aucun synopsis disponible dans le Nexus.')}
                        </p>
                    </Card>
                </section>

                {mediaType?.toLowerCase() === 'manga' && itemId && (
                  <ChapterList mediaId={itemId} mediaTitle={item.title} />
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    {/* Technical Stack */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-yellow-400" /> {t('media.detail.creative_team', 'Équipe Créative')}
                        </h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-2xl border border-white/5">
                                <span className="text-[10px] font-black opacity-30 uppercase">Studio</span>
                                <span className="font-bold italic text-sm">{item.studios?.[0] || 'N/A'}</span>
                            </div>
                            <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-2xl border border-white/5">
                                <span className="text-[10px] font-black opacity-30 uppercase">{t('media.detail.author', 'Auteur')}</span>
                                <span className="font-bold italic text-sm text-yellow-400">{item.author || t('media.detail.unknown', 'Inconnu')}</span>
                            </div>
                        </div>
                    </section>

                    {/* Semantic Tags */}
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                            <Play className="w-4 h-4 text-emerald-400" /> {t('media.detail.micro_tags', 'Micro-Tags IA')}
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {item.micro_tags?.slice(0, 10).map((t: string) => (
                                <Badge key={t} variant="neutral" className="bg-black text-[8px] uppercase tracking-tighter opacity-50">{t}</Badge>
                            ))}
                            {(!item.micro_tags || item.micro_tags.length === 0) && <p className="text-xs opacity-20 italic">{t('media.detail.analysis_running', 'Analyse en cours...')}</p>}
                        </div>
                    </section>
                </div>

                {/* Related Items */}
                {item.related_items && item.related_items.length > 0 && (
                    <section>
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                            <Network className="w-4 h-4 text-purple-400" /> {t('media.detail.related_works', 'Œuvres Liées dans le Graphe')}
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                            {item.related_items.map((rel: RelatedItem) => (
                                <Link key={rel.id} to={`/media/${mediaType}/${rel.id}/`} className="no-underline group">
                                    <div className="aspect-[2/3] rounded-2xl overflow-hidden bg-gray-900 mb-3 border border-white/5 group-hover:border-purple-500/30 transition-all group-hover:scale-105 shadow-xl">
                                        <img src={rel.image} className="w-full h-full object-cover" alt={rel.title} loading="lazy" decoding="async" />
                                    </div>
                                    <p className="text-[10px] font-black uppercase tracking-tighter line-clamp-1 opacity-50 group-hover:text-purple-400 group-hover:opacity-100 transition-all">{rel.title}</p>
                                </Link>
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default MediaDetailPage;
