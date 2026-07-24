import React from 'react';
import { Sparkles, Heart, MessageSquare, Share2, Zap, TrendingUp, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fusionService } from '../../features/social/services/fusionService';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { queryClient } from '../../utils/queryClient';
import { CreativeFusion } from '../../types';
import { useTranslation } from 'react-i18next';

const CommunityFeedPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: feed, isLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['fusions-feed'],
    queryFn: fusionService.getFeed,
  });

  const likeMutation = useMutation({
    mutationFn: (id: number) => fusionService.likeFusion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fusions-feed'] });
    },
  });

  if (isLoading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
      <AnimatedPage>
        <div className="mx-auto max-w-7xl px-6 py-16">
          <header className="relative mb-16">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
              aria-hidden
            />
            <div className="relative flex flex-col justify-between gap-8 md:flex-row md:items-end">
              <div>
                <div className="flex items-center gap-3">
                  <span className="explore-stamp -rotate-2" aria-hidden>
                    流
                  </span>
                  <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                    {t('social.feed.eyebrow', 'Registre · Fusions')}
                  </span>
                </div>
                <h1 className="font-manga mt-4 text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-7xl">
                  FUSION <span className="text-[#E8442B]">FEED</span>
                </h1>
                <p className="mt-4 max-w-xl text-sm font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                  {t('social.feed.subtitle', 'Découvrez les créations du Nexus Communautaire.')}
                </p>
              </div>

              <div className="flex gap-4">
                <Link
                  to="/forge/"
                  className="font-manga group inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-8 py-4 text-base font-black uppercase italic text-[#F4F1E8] no-underline transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                >
                  <Plus className="h-5 w-5 transition-transform duration-500 group-hover:rotate-90" />{' '}
                  {t('social.feed.new_fusion', 'NOUVELLE FUSION')}
                </Link>
              </div>
            </div>
            <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
          </header>

          {/* Categories / Filter Bar (Visual only for now) */}
          <div className="no-scrollbar mb-12 flex gap-3 overflow-x-auto pb-4">
            <span className="cursor-pointer whitespace-nowrap rounded-full border border-[#E8442B] bg-[#E8442B] px-6 py-2 text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
              {t('social.feed.filter_trends', '🔥 TENDANCES')}
            </span>
            <span className="cursor-pointer whitespace-nowrap rounded-full border border-[#F4F1E8]/15 px-6 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]">
              {t('social.feed.filter_recent', '✨ RÉCENT')}
            </span>
            <span className="cursor-pointer whitespace-nowrap rounded-full border border-[#F4F1E8]/15 px-6 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]">
              {t('social.feed.filter_popular', '💎 POPULAIRE')}
            </span>
            <span className="cursor-pointer whitespace-nowrap rounded-full border border-[#F4F1E8]/15 px-6 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]">
              {t('social.feed.filter_ai_picks', '🤖 IA PICKS')}
            </span>
          </div>

          {!feed || feed.length === 0 ? (
            <div className="flex flex-col items-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-32 text-center">
              <Sparkles className="mb-6 h-20 w-20 text-[#8F94A5]/30" />
              <p className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/60">
                {t('social.feed.empty_feed', 'Le flux est vide... Soyez le premier à fusionner !')}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
              {feed.map((fusion: CreativeFusion) => (
                <article
                  key={fusion.id}
                  className="group overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-all duration-300 hover:-translate-y-1 hover:border-[#FDB913]/50"
                >
                  <div className="relative aspect-video overflow-hidden bg-[#0B0C10]">
                    {fusion.image_url ? (
                      <img
                        src={fusion.image_url}
                        className="h-full w-full object-cover transition-transform duration-1000 group-hover:scale-110"
                        alt={fusion.title_a}
                        loading="lazy"
                        decoding="async"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-[#F4F1E8]/10">
                        <Sparkles className="h-16 w-16" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-[#0B0C10]/40 to-transparent"></div>

                    {/* Overlay Info */}
                    <div className="absolute bottom-6 left-6 right-6">
                      <div className="mb-2 flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#FDB913] text-[10px] font-black text-[#0B0C10]">
                          {fusion.creator_name?.[0].toUpperCase() || '?'}
                        </div>
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#F4F1E8]/70">
                          {fusion.creator_name || t('social.feed.anonymous', 'Anonyme')}
                        </span>
                      </div>
                      <h3 className="font-manga truncate text-2xl font-black uppercase italic leading-none text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                        {fusion.title_a} <span className="text-[#E8442B]">×</span> {fusion.title_b}
                      </h3>
                    </div>
                  </div>

                  <div className="space-y-6 p-6">
                    <div className="flex gap-2">
                      <span className="rounded border border-[#F4F1E8]/10 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {fusion.media_type_a}
                      </span>
                      <span className="rounded border border-[#F4F1E8]/10 px-2 py-1 text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {fusion.media_type_b}
                      </span>
                    </div>

                    <p className="line-clamp-3 text-[10px] font-bold uppercase italic leading-relaxed text-[#8F94A5]/70">
                      "{fusion.scenario_text?.substring(0, 150)}..."
                    </p>

                    <div className="flex items-center justify-between border-t border-[#F4F1E8]/10 pt-6">
                      <div className="flex gap-4">
                        <button
                          onClick={() => likeMutation.mutate(fusion.id)}
                          className={`flex cursor-pointer items-center gap-2 transition-colors ${fusion.is_liked ? 'text-[#E8442B]' : 'text-[#8F94A5] hover:text-[#E8442B]'}`}
                        >
                          <Heart className={`h-5 w-5 ${fusion.is_liked ? 'fill-current' : ''}`} />
                          <span className="text-xs font-black text-[#FDB913]">
                            {fusion.likes_count || 0}
                          </span>
                        </button>
                        <button className="flex cursor-pointer items-center gap-2 text-[#8F94A5] transition-colors hover:text-[#F4F1E8]">
                          <MessageSquare className="h-5 w-5" />
                          <span className="text-xs font-black">4</span>
                        </button>
                      </div>
                      <div className="flex gap-2">
                        <button className="rounded-full border border-[#F4F1E8]/10 bg-transparent p-2 text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#FDB913]">
                          <Zap className="h-4 w-4" />
                        </button>
                        <button className="rounded-full border border-[#F4F1E8]/10 bg-transparent p-2 text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]">
                          <Share2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* Legend Box */}
          <section className="relative mt-32 flex flex-col items-center gap-12 overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-10 text-center md:flex-row md:p-12 md:text-left">
            <span
              className="font-manga pointer-events-none absolute -bottom-14 -right-4 select-none text-[11rem] font-black italic leading-none text-[#E8442B]/[0.05]"
              aria-hidden
            >
              流
            </span>
            <div className="relative flex h-24 w-24 flex-none items-center justify-center rounded-2xl border border-[#FDB913]/30 bg-[#FDB913]/[0.08]">
              <TrendingUp className="h-12 w-12 text-[#FDB913]" />
            </div>
            <div className="relative">
              <h4 className="font-manga mb-4 text-3xl font-black uppercase italic tracking-tighter text-[#F4F1E8]">
                Nexus Trends v2.0
              </h4>
              <p className="max-w-3xl text-sm leading-relaxed text-[#8F94A5]">
                {t(
                  'social.feed.trends_desc',
                  "Les fusions les plus populaires sont automatiquement propulsées dans le Graphe de Lore global d'Animetix, créant ainsi de nouveaux canons narratifs validés par la communauté.",
                )}
              </p>
            </div>
          </section>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default CommunityFeedPage;
