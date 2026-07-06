import React from 'react';
import { 
  Sparkles, 
  Heart, 
  MessageSquare, 
  Share2, 
  Zap, 
  TrendingUp,
  Plus
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fusionService } from '../../features/social/services/fusionService';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { queryClient } from "../../utils/queryClient";
import {CreativeFusion} from "../../types";
import { useTranslation } from 'react-i18next';

const CommunityFeedPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: feed, isLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['fusions-feed'],
    queryFn: fusionService.getFeed
  });

  const likeMutation = useMutation({
    mutationFn: (id: number) => fusionService.likeFusion(id),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['fusions-feed'] });
    }
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
        </div>
    </div>
  );

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div>
                <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
                    FUSION <span className="text-yellow-400 text-glow">FEED</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em]">
                    {t('social.feed.subtitle', 'Découvrez les créations du Nexus Communautaire.')}
                </p>
            </div>
            
            <div className="flex gap-4">
                <Button as={Link} to="/forge/" variant="primary" className="bg-yellow-400 text-black border-none py-6 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all group">
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" /> {t('social.feed.new_fusion', 'NOUVELLE FUSION')}
                </Button>
            </div>
        </header>

        {/* Categories / Filter Bar (Visual only for now) */}
        <div className="flex gap-4 mb-12 overflow-x-auto pb-4 no-scrollbar">
            <Badge variant="primary" className="bg-yellow-400 text-black px-6 py-2 cursor-pointer shadow-lg">{t('social.feed.filter_trends', '🔥 TENDANCES')}</Badge>
            <Badge variant="neutral" className="bg-white/5 border-white/10 px-6 py-2 cursor-pointer hover:bg-white/10">{t('social.feed.filter_recent', '✨ RÉCENT')}</Badge>
            <Badge variant="neutral" className="bg-white/5 border-white/10 px-6 py-2 cursor-pointer hover:bg-white/10">{t('social.feed.filter_popular', '💎 POPULAIRE')}</Badge>
            <Badge variant="neutral" className="bg-white/5 border-white/10 px-6 py-2 cursor-pointer hover:bg-white/10">{t('social.feed.filter_ai_picks', '🤖 IA PICKS')}</Badge>
        </div>

        {!feed || feed.length === 0 ? (
          <div className="text-center py-32 opacity-20">
              <Sparkles className="w-24 h-24 mx-auto mb-6" />
              <p className="text-2xl font-black italic manga-font uppercase">{t('social.feed.empty_feed', 'Le flux est vide... Soyez le premier à fusionner !')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {feed.map((fusion: CreativeFusion) => (
              <Card key={fusion.id} padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-yellow-400/30 transition-all duration-500 hover:-translate-y-2">
                <div className="aspect-video relative overflow-hidden bg-black shadow-inner">
                  {fusion.image_url ? (
                    <img src={fusion.image_url} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" alt={fusion.title_a} loading="lazy" decoding="async" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center opacity-10">
                      <Sparkles className="w-16 h-16 text-white" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-transparent to-transparent opacity-80 group-hover:opacity-90 transition-opacity"></div>
                  
                  {/* Overlay Info */}
                  <div className="absolute bottom-6 left-6 right-6">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded-full bg-yellow-400 flex items-center justify-center text-[10px] font-black text-black">
                            {fusion.creator_name?.[0].toUpperCase() || '?'}
                        </div>
                        <span className="text-[10px] font-black text-white/60 uppercase tracking-widest">{fusion.creator_name || t('social.feed.anonymous', 'Anonyme')}</span>
                    </div>
                    <h3 className="font-black italic text-2xl leading-none truncate uppercase manga-font text-white group-hover:text-yellow-400 transition-colors">
                        {fusion.title_a} <span className="text-yellow-400">×</span> {fusion.title_b}
                    </h3>
                  </div>
                </div>
                
                <div className="p-6 space-y-6">
                  <div className="flex gap-2">
                      <Badge variant="neutral" className="bg-white/5 border-white/10 text-[8px] uppercase tracking-widest font-black">{fusion.media_type_a}</Badge>
                      <Badge variant="neutral" className="bg-white/5 border-white/10 text-[8px] uppercase tracking-widest font-black">{fusion.media_type_b}</Badge>
                  </div>

                  <p className="text-[10px] leading-relaxed opacity-40 uppercase font-bold line-clamp-3 italic">
                      "{fusion.scenario_text?.substring(0, 150)}..."
                  </p>

                  <div className="pt-6 border-t border-white/5 flex items-center justify-between">
                    <div className="flex gap-4">
                        <button 
                            onClick={() => likeMutation.mutate(fusion.id)}
                            className={`flex items-center gap-2 transition-all hover:scale-110 ${fusion.is_liked ? 'text-red-500' : 'text-white/30 hover:text-red-400'}`}
                        >
                            <Heart className={`w-5 h-5 ${fusion.is_liked ? 'fill-current' : ''}`} />
                            <span className="text-xs font-black">{fusion.likes_count || 0}</span>
                        </button>
                        <button className="flex items-center gap-2 text-white/30 hover:text-blue-400 transition-all hover:scale-110">
                            <MessageSquare className="w-5 h-5" />
                            <span className="text-xs font-black">4</span>
                        </button>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="p-2 border-white/5 bg-white/5 hover:bg-yellow-400/10 hover:text-yellow-400">
                            <Zap className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" className="p-2 border-white/5 bg-white/5 hover:bg-blue-400/10 hover:text-blue-400">
                            <Share2 className="w-4 h-4" />
                        </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Legend Box */}
        <div className="mt-32 p-12 rounded-[4rem] bg-navy-900/40 border border-white/5 flex flex-col md:flex-row items-center gap-12 text-center md:text-left">
            <div className="relative">
                <div className="absolute -inset-4 bg-yellow-400/20 rounded-full blur-2xl animate-pulse"></div>
                <div className="w-24 h-24 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-3xl flex items-center justify-center rotate-12 shadow-2xl relative">
                    <TrendingUp className="w-12 h-12 text-black" />
                </div>
            </div>
            <div>
                <h4 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter">Nexus Trends v2.0</h4>
                <p className="text-sm font-bold opacity-40 uppercase leading-relaxed max-w-3xl italic">
                    {t('social.feed.trends_desc', "Les fusions les plus populaires sont automatiquement propulsées dans le Graphe de Lore global d'Animetix, créant ainsi de nouveaux canons narratifs validés par la communauté.")}
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default CommunityFeedPage;


