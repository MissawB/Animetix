import React from 'react';
import { Link } from 'react-router-dom';
import { Film, Play, Clock, Heart, ChevronRight, BookOpen, Library } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import type { CreativeFusion } from '../../types';

const TheaterPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: vns, isLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['theater-list'],
    queryFn: () => apiClient('/api/v1/archetypist/theater/'),
  });

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10]">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <header className="relative mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
              aria-hidden
            />
            <div className="relative">
              <div className="flex items-center gap-3 mb-4">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  幕
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  <Library className="inline w-3 h-3 mr-1 -mt-0.5" /> Narrative Archive
                </span>
              </div>
              <h1 className="font-manga text-6xl md:text-7xl font-black italic tracking-tighter uppercase mb-2 leading-none text-[#F4F1E8]">
                AI <span className="text-[#E8442B]">THEATER</span>
              </h1>
              <p className="text-base leading-relaxed text-[#8F94A5] max-w-2xl">
                {t(
                  'games.theater.subtitle',
                  'Explorez la bibliothèque des Visual Novels générés par la Forge.',
                )}
              </p>
            </div>

            <div className="relative flex gap-4">
              <Button
                as={Link}
                to="/forge/"
                variant="primary"
                className="!bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none py-6 px-10 rounded-xl transition-colors"
              >
                {t('games.theater.generate_story', 'GÉNÉRER MON HISTOIRE')}
              </Button>
            </div>
          </header>

          {!vns || vns.length === 0 ? (
            <div className="text-center py-32 rounded-2xl border border-dashed border-[#F4F1E8]/15">
              <Film className="w-24 h-24 mx-auto mb-6 text-[#8F94A5]/40" />
              <p className="font-manga text-2xl font-black italic uppercase text-[#F4F1E8]/60">
                {t('games.theater.empty', 'Aucun Visual Novel archivé pour le moment')}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
              {vns.map((vn) => (
                <article
                  key={vn.id}
                  className="group overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-all duration-500 hover:-translate-y-2 hover:border-[#E8442B]/40 flex flex-col"
                >
                  <div className="aspect-[16/10] relative overflow-hidden bg-[#0B0C10]">
                    {vn.image_url ? (
                      <img
                        src={vn.image_url}
                        className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                        alt={vn.title_a}
                        loading="lazy"
                        decoding="async"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Film className="w-16 h-16 text-[#F4F1E8]/10" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-transparent to-transparent opacity-70 group-hover:opacity-90 transition-opacity"></div>

                    {/* Bouton de lecture en survol */}
                    <Link
                      to={`/forge/vn/${vn.id}/`}
                      className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100 no-underline"
                    >
                      <div className="w-20 h-20 bg-[#E8442B] rounded-full flex items-center justify-center">
                        <Play className="w-8 h-8 text-[#F4F1E8] fill-current" />
                      </div>
                    </Link>

                    <span className="absolute top-4 right-4 rounded-[2px] border-2 border-[#E8442B] bg-[#0B0C10]/70 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-[#E8442B] backdrop-blur-md">
                      VISUAL NOVEL
                    </span>
                  </div>

                  <div className="p-8 space-y-6 flex-grow flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-5 h-5 rounded-full border border-[#F4F1E8]/15 flex items-center justify-center text-[8px] font-black text-[#8F94A5]">
                          {vn.creator_name?.[0].toUpperCase() || '?'}
                        </div>
                        <span className="text-[9px] font-black text-[#8F94A5] uppercase tracking-widest">
                          {vn.creator_name || t('games.theater.anonymous', 'Anonyme')}
                        </span>
                      </div>
                      <h3 className="font-manga font-black italic text-2xl leading-tight mb-4 uppercase text-[#F4F1E8] group-hover:text-[#E8442B] transition-colors">
                        {vn.title_a} <span className="text-[#E8442B]">×</span> {vn.title_b}
                      </h3>
                      <p className="text-[11px] leading-relaxed text-[#8F94A5] line-clamp-3 italic">
                        "{vn.scenario_text?.substring(0, 120)}..."
                      </p>
                    </div>

                    <div className="pt-6 border-t border-[#F4F1E8]/10 flex items-center justify-between">
                      <div className="flex items-center gap-4 text-[#8F94A5]">
                        <div className="flex items-center gap-1">
                          <Heart className="w-4 h-4" />
                          <span className="text-[10px] font-black text-[#FDB913]">
                            {vn.likes_count || 0}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          <span className="text-[10px] font-black">5 min</span>
                        </div>
                      </div>
                      <Link to={`/forge/vn/${vn.id}/`} className="no-underline">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#E8442B] group-hover:gap-3 transition-all">
                          {t('games.theater.play', 'Jouer')} <ChevronRight className="w-3 h-3" />
                        </div>
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* Notice de l'atelier */}
          <div className="relative mt-32 p-10 md:p-12 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] flex flex-col md:flex-row items-center gap-12 text-center md:text-left overflow-hidden">
            <span
              className="font-manga pointer-events-none absolute -bottom-14 -right-4 text-[11rem] font-black italic leading-none text-[#E8442B]/[0.05]"
              aria-hidden
            >
              幕
            </span>
            <div className="relative flex-none">
              <div className="w-24 h-24 rounded-xl border border-[#E8442B]/30 bg-[#E8442B]/10 flex items-center justify-center -rotate-6">
                <BookOpen className="w-12 h-12 text-[#E8442B]" />
              </div>
            </div>
            <div className="relative">
              <h4 className="font-manga text-3xl font-black italic uppercase mb-4 tracking-tighter text-[#F4F1E8]">
                Director's Cut v4.2
              </h4>
              <p className="text-sm leading-relaxed text-[#8F94A5] max-w-3xl italic text-justify">
                {t(
                  'games.theater.legend_text',
                  "Chaque Visual Novel est une création unique générée par des réseaux de neurones récurrents. Ils s'adaptent dynamiquement à vos choix et peuvent être remixés par la communauté pour explorer des embranchements narratifs alternatifs.",
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TheaterPage;
