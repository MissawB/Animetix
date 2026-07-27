import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Search,
  Eye,
  Sparkles,
  Tv,
  Grid,
  Layers,
  Film,
  Play,
  Clock,
  Video,
  Brain,
  Star,
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

import { SearchItem, VideoSegment } from '../../types';
import ExpertNexusPanel from './components/ExpertNexusPanel';

type SearchMode = 'global' | 'visual' | 'expert';

const UniversalSearchHubPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useTranslation();
  const initialQuery = searchParams.get('q') || '';
  const initialMode = (searchParams.get('mode') as SearchMode) || 'global';

  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [activeTab, setActiveTab] = useState<string>('all');

  // On débounce la requête : sans cela, useQuery se relançait à CHAQUE frappe
  // (une requête réseau par caractère). On n'interroge qu'après une pause de 400 ms.
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery.trim());
  useEffect(() => {
    const id = setTimeout(() => setDebouncedQuery(query.trim()), 400);
    return () => clearTimeout(id);
  }, [query]);

  // Global Search Query
  const { data: globalData, isLoading: isGlobalLoading } = useQuery<
    SearchItem[] | { results: SearchItem[] }
  >({
    queryKey: ['global-search', debouncedQuery],
    queryFn: () => apiClient(`/api/v1/search/?q=${encodeURIComponent(debouncedQuery)}`),
    enabled: mode === 'global' && !!debouncedQuery,
  });

  // Visual Search Mutation
  const visualMutation = useMutation({
    mutationFn: (q: string) => apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`),
  });

  const visualResults: VideoSegment[] = visualMutation.data?.results || [];

  // Disponibilité de la recherche vidéo (Video-RAG). La collection n'est peuplée
  // que par un endpoint admin masqué : pour la plupart des utilisateurs elle est
  // vide et une recherche visuelle ne peut jamais aboutir. On lit ce flag pour
  // présenter honnêtement le mode plutôt que de laisser croire qu'il est prêt.
  const { data: videoLab } = useQuery<{ video_rag_available?: boolean }>({
    queryKey: ['video-rag-availability'],
    queryFn: () => apiClient('/api/v1/labs/video/'),
    staleTime: 5 * 60 * 1000,
  });
  const visualUnavailable = videoLab?.video_rag_available === false;

  // Expert Nexus (RAG agentique) intégré comme 3e mode, piloté par la même barre
  // de recherche. runId démarre à 1 si on arrive déjà en mode expert avec ?q=.
  const [expertQuery, setExpertQuery] = useState(
    initialMode === 'expert' ? initialQuery.trim() : '',
  );
  const [expertRunId, setExpertRunId] = useState(
    initialMode === 'expert' && initialQuery.trim() ? 1 : 0,
  );
  const [expertStreaming, setExpertStreaming] = useState(false);

  useEffect(() => {
    if (initialQuery && initialMode === 'visual' && !visualUnavailable) {
      visualMutation.mutate(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentional mount-only initialization from URL params

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim(), mode });
      setDebouncedQuery(query.trim()); // recherche immédiate (on court-circuite le debounce)
      if (mode === 'visual' && !visualUnavailable) {
        visualMutation.mutate(query.trim());
      } else if (mode === 'expert') {
        setExpertQuery(query.trim());
        setExpertRunId((n) => n + 1);
      }
    }
  };

  const globalResults = Array.isArray(globalData) ? globalData : globalData?.results || [];
  const filteredGlobalResults =
    activeTab === 'all'
      ? globalResults
      : globalResults.filter(
          (item: SearchItem) => item.type?.toLowerCase() === activeTab.toLowerCase(),
        );

  const TABS = [
    { id: 'all', label: t('search.hub.tab_all', 'TOUT'), icon: Grid },
    { id: 'Anime', label: t('search.hub.tab_anime', 'ANIME'), icon: Tv },
    { id: 'Manga', label: t('search.hub.tab_manga', 'MANGA'), icon: Tv },
    { id: 'Actor', label: t('search.hub.tab_seiyuu', 'SEIYUU'), icon: Tv },
  ];

  // Encre d'accent du mode actif : or pour la recherche visuelle (voix données),
  // shu pour la méta-recherche et l'Expert Nexus (voix éditoriale).
  const accentInk = mode === 'visual' ? '#FDB913' : '#E8442B';

  return (
    <AnimatedPage>
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20 text-[#F4F1E8]">
        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6">
          <header className="relative mb-14 text-center">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-48"
              aria-hidden
            />
            <div className="relative mb-8 flex items-center justify-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                探
              </span>
              <span className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                <Search className="h-3 w-3" /> Moteur de recherche unifié
              </span>
            </div>
            <h1 className="font-manga relative text-5xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-8xl">
              RECHERCHE <span style={{ color: accentInk }}>UNIVERSELLE</span>
            </h1>

            {/* Sélecteur de mode */}
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <button
                onClick={() => setMode('global')}
                className={`flex items-center gap-3 rounded-xl border px-7 py-3.5 text-xs font-black uppercase italic tracking-[0.2em] transition-colors ${
                  mode === 'global'
                    ? 'border-[#E8442B] bg-[#E8442B] text-[#F4F1E8]'
                    : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                }`}
              >
                <Search className="h-5 w-5" /> Méta-recherche
              </button>
              <button
                onClick={() => setMode('visual')}
                className={`flex items-center gap-3 rounded-xl border px-7 py-3.5 text-xs font-black uppercase italic tracking-[0.2em] transition-colors ${
                  mode === 'visual'
                    ? 'border-[#FDB913] bg-[#FDB913] text-[#0B0C10]'
                    : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                }`}
              >
                <Eye className="h-5 w-5" /> Nexus visuel
                {visualUnavailable && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-[8px] font-black not-italic tracking-widest ${
                      mode === 'visual'
                        ? 'bg-[#0B0C10]/20 text-[#0B0C10]'
                        : 'bg-[#F4F1E8]/10 text-[#8F94A5]'
                    }`}
                  >
                    Bientôt
                  </span>
                )}
              </button>
              <button
                onClick={() => setMode('expert')}
                className={`flex items-center gap-3 rounded-xl border px-7 py-3.5 text-xs font-black uppercase italic tracking-[0.2em] transition-colors ${
                  mode === 'expert'
                    ? 'border-[#E8442B] bg-[#E8442B] text-[#F4F1E8]'
                    : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                }`}
              >
                <Brain className="h-5 w-5" /> Expert Nexus
              </button>
            </div>

            <form onSubmit={handleSearch} className="mx-auto mt-10 flex max-w-3xl gap-3">
              <div className="group relative flex-grow">
                <Search className="absolute left-5 top-1/2 h-6 w-6 -translate-y-1/2 text-[#8F94A5]/50 transition-colors group-focus-within:text-[#FDB913]" />
                <input
                  type="text"
                  aria-label="Rechercher"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    mode === 'global'
                      ? t('search.hub.global_placeholder', 'Rechercher un anime, manga, seiyuu...')
                      : mode === 'visual'
                        ? t(
                            'search.hub.visual_placeholder',
                            'Décrivez une scène visuelle ou un moment précis...',
                          )
                        : t(
                            'search.expert.placeholder',
                            'Posez une question profonde sur un univers, une relation ou un arc narratif...',
                          )
                  }
                  className="w-full rounded-2xl border border-[#F4F1E8]/15 bg-[#0F1016] py-5 pl-14 pr-6 text-lg font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                />
              </div>
              <button
                type="submit"
                disabled={mode === 'expert' && expertStreaming}
                className="rounded-2xl border-none bg-[#E8442B] px-8 font-manga text-xl font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              >
                {mode === 'expert' && expertStreaming ? 'ANALYSE…' : 'SCANNER'}
              </button>
            </form>
          </header>

          <AnimatePresence mode="wait">
            {mode === 'global' ? (
              <motion.div
                key="global"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                {/* Onglets / Filtres */}
                <div className="no-scrollbar mb-12 flex justify-center gap-2 overflow-x-auto pb-4">
                  {TABS.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-3 rounded-xl border px-6 py-3 text-[10px] font-black uppercase italic tracking-widest transition-colors ${
                        activeTab === tab.id
                          ? 'border-[#E8442B] bg-[#E8442B] text-[#F4F1E8]'
                          : 'border-[#F4F1E8]/15 bg-transparent text-[#8F94A5] hover:border-[#FDB913] hover:text-[#F4F1E8]'
                      }`}
                    >
                      <tab.icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  ))}
                </div>

                {isGlobalLoading ? (
                  <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
                    {[1, 2, 3, 4].map((i) => (
                      <CardSkeleton key={i} />
                    ))}
                  </div>
                ) : filteredGlobalResults.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 py-32 text-center text-[#8F94A5]">
                    <Search className="mx-auto mb-6 h-20 w-20 text-[#8F94A5]/40" />
                    <p className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/50">
                      {t('search.hub.no_metadata', 'Aucun résultat meta-data')}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
                    {filteredGlobalResults.map((item: SearchItem, i: number) => (
                      <Link
                        key={i}
                        to={`/media/${item.type}/${item.id}/`}
                        className="group no-underline"
                      >
                        <div className="relative h-full overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-colors duration-300 hover:border-[#FDB913]/40">
                          <div className="relative aspect-[2/3] overflow-hidden bg-[#0B0C10]">
                            {item.image_url ? (
                              <img
                                src={item.image_url}
                                className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                                alt={item.title}
                                loading="lazy"
                                decoding="async"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center opacity-10">
                                <Sparkles className="h-16 w-16 text-[#F4F1E8]" />
                              </div>
                            )}
                            <div className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-transparent to-transparent opacity-70"></div>

                            <span className="absolute right-3 top-3 rounded-[2px] border border-[#E8442B]/60 bg-[#0B0C10]/80 px-2 py-1 text-[8px] font-black uppercase italic tracking-widest text-[#E8442B] backdrop-blur-md">
                              {item.type}
                            </span>

                            {item.rating != null && (
                              <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-[2px] border border-[#FDB913]/50 bg-[#0B0C10]/80 px-2 py-1 text-[9px] font-black tabular-nums text-[#FDB913] backdrop-blur-md">
                                <Star
                                  className="h-2.5 w-2.5"
                                  fill="currentColor"
                                  aria-hidden="true"
                                />
                                {item.rating.toFixed(0)}
                              </span>
                            )}
                          </div>

                          <div className="p-5">
                            <h3 className="font-manga line-clamp-2 text-lg font-black uppercase italic leading-tight text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                              {item.title || item.name}
                            </h3>
                            {item.title_english &&
                              item.title_english.trim().toLowerCase() !==
                                (item.title || '').trim().toLowerCase() && (
                                <p className="mt-1 line-clamp-1 text-xs font-medium text-[#8F94A5]">
                                  {item.title_english}
                                </p>
                              )}
                            {item.year && (
                              <p className="mt-2.5 text-[10px] font-bold uppercase tracking-widest tabular-nums text-[#8F94A5]">
                                {item.year}
                              </p>
                            )}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </motion.div>
            ) : mode === 'visual' ? (
              <motion.div
                key="visual"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {visualUnavailable ? (
                  <div className="rounded-2xl border border-dashed border-[#FDB913]/25 bg-[#FDB913]/[0.04] px-6 py-28 text-center">
                    <Video
                      className="mx-auto mb-8 h-24 w-24 text-[#FDB913]/30"
                      aria-hidden="true"
                    />
                    <h3 className="font-manga mb-4 text-3xl font-black uppercase italic text-[#F4F1E8]/70 md:text-4xl">
                      Nexus visuel — bientôt
                    </h3>
                    <p className="mx-auto mb-8 max-w-md text-sm leading-relaxed text-[#8F94A5]">
                      La recherche par scène s'appuie sur un index vidéo qui n'est pas encore
                      constitué. Elle s'activera dès que des vidéos seront indexées — en attendant,
                      la méta-recherche couvre animes, mangas et personnages.
                    </p>
                    <button
                      type="button"
                      onClick={() => setMode('global')}
                      className="inline-flex items-center gap-2 rounded-xl border border-[#F4F1E8]/15 px-6 py-3 text-xs font-black uppercase italic tracking-[0.2em] text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                    >
                      <Search className="h-4 w-4" /> Passer à la méta-recherche
                    </button>
                  </div>
                ) : (
                  <div className="space-y-10">
                    <div className="flex items-center justify-between px-1">
                      <h3 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                        <Layers className="h-4 w-4 text-[#FDB913]" />{' '}
                        {t('search.hub.temporal_segments', 'Segments Temporels Identifiés')}
                      </h3>
                      {visualResults.length > 0 && (
                        <span className="rounded-full border border-[#FDB913]/40 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                          {t('search.hub.moments_found', '{{count}} MOMENTS TROUVÉS', {
                            count: visualResults.length,
                          })}
                        </span>
                      )}
                    </div>

                    {visualMutation.isPending ? (
                      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                          <div
                            key={i}
                            className="aspect-video animate-pulse rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]"
                          />
                        ))}
                      </div>
                    ) : visualResults.length > 0 ? (
                      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
                        {visualResults.map((segment, idx) => (
                          <div
                            key={idx}
                            className="group relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-colors duration-300 hover:border-[#FDB913]/40"
                          >
                            <div className="relative aspect-video bg-[#0B0C10]">
                              <div className="absolute inset-0 flex items-center justify-center">
                                <Film className="h-12 w-12 text-[#F4F1E8]/10 transition-transform duration-500 group-hover:scale-110" />
                              </div>
                              <div className="absolute inset-0 flex items-center justify-center bg-[#0B0C10]/40 opacity-0 transition-opacity group-hover:opacity-100">
                                <div className="flex h-16 w-16 scale-75 items-center justify-center rounded-full bg-[#E8442B] transition-transform duration-300 group-hover:scale-100">
                                  <Play className="h-8 w-8 fill-current text-[#F4F1E8]" />
                                </div>
                              </div>
                              <div className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg bg-[#0B0C10]/80 px-3 py-1 font-mono text-[10px] font-bold text-[#F4F1E8] backdrop-blur-md">
                                <Clock className="h-3 w-3 text-[#FDB913]" />
                                {Math.floor(segment.start_time / 60)}:
                                {(segment.start_time % 60).toString().padStart(2, '0')}
                              </div>
                            </div>
                            <div className="p-5">
                              <h4 className="font-manga mb-2 truncate text-lg font-black uppercase italic text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                                {segment.media_title ||
                                  t('search.hub.video_fallback', 'Vidéo #{{id}}', {
                                    id: segment.video_id,
                                  })}
                              </h4>
                              <p className="line-clamp-2 text-[10px] font-bold uppercase italic leading-relaxed text-[#8F94A5]">
                                "{segment.description}"
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 py-40 text-center text-[#8F94A5]">
                        <Video className="mx-auto mb-8 h-28 w-28 text-[#8F94A5]/40" />
                        <h3 className="font-manga mb-4 text-4xl font-black uppercase italic text-[#F4F1E8]/50">
                          {t('search.hub.engine_ready', 'Moteur Optique Prêt')}
                        </h3>
                        <p className="text-sm font-bold uppercase tracking-[0.3em]">
                          {t(
                            'search.hub.engine_desc',
                            'Entrez une description pour scanner la base de clips.',
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="expert"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <ExpertNexusPanel
                  key={expertRunId}
                  query={expertQuery}
                  onStreamingChange={setExpertStreaming}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Suggestions globales / stats techniques */}
          <footer className="mt-32 grid grid-cols-1 gap-12 border-t border-[#F4F1E8]/10 pt-16 text-center md:grid-cols-3 md:text-left">
            <div className="space-y-4">
              <span className="inline-block rounded-full border border-[#F4F1E8]/15 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                Multimodal RAG
              </span>
              <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider text-[#8F94A5]/70">
                {t(
                  'search.hub.footer_rag',
                  "La recherche unifiée combine les métadonnées de MAL/AniList avec l'analyse d'images par Computer Vision.",
                )}
              </p>
            </div>
            <div className="space-y-4">
              <span className="inline-block rounded-full border border-[#F4F1E8]/15 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                Knowledge Graph
              </span>
              <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider text-[#8F94A5]/70">
                {t(
                  'search.hub.footer_graph',
                  'Toutes les entités sont reliées via Neo4j, permettant de trouver des corrélations thématiques entre anime et manga.',
                )}
              </p>
            </div>
            <div className="space-y-4">
              <span className="inline-block rounded-full border border-[#F4F1E8]/15 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                Temporal Index
              </span>
              <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider text-[#8F94A5]/70">
                {t(
                  'search.hub.footer_temporal',
                  "L'indexation temporelle permet de chercher directement des frames au sein des épisodes.",
                )}
              </p>
            </div>
          </footer>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default UniversalSearchHubPage;
