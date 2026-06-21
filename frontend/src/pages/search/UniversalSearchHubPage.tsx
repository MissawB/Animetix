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
  Terminal,
  Play,
  Clock,
  Video
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { motion, AnimatePresence } from 'framer-motion';

import { SearchItem, VideoSegment } from '../../types';

type SearchMode = 'global' | 'visual';

const UniversalSearchHubPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialMode = (searchParams.get('mode') as SearchMode) || 'global';
  
  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [visualResults, setVisualResults] = useState<VideoSegment[]>([]);

  // Global Search Query
  const { data: globalData, isLoading: isGlobalLoading } = useQuery<SearchItem[] | { results: SearchItem[] }>({
    queryKey: ['global-search', query],
    queryFn: () => apiClient(`/api/v1/search/?q=${encodeURIComponent(query)}`),
    enabled: mode === 'global' && !!query,
  });

  // Visual Search Mutation
  const visualMutation = useMutation({
    mutationFn: (q: string) => apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`),
    onSuccess: (data) => {
        // Map backend temporal segment to VideoSegment if needed, or update VideoSegment interface
        setVisualResults(data.results || []);
    }
  });

  useEffect(() => {
    if (initialQuery && initialMode === 'visual') {
        visualMutation.mutate(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentional mount-only initialization from URL params

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
        setSearchParams({ q: query.trim(), mode });
        if (mode === 'visual') {
            visualMutation.mutate(query.trim());
        }
    }
  };

  const globalResults = Array.isArray(globalData) ? globalData : globalData?.results || [];
  const filteredGlobalResults = activeTab === 'all' 
    ? globalResults 
    : globalResults.filter((item: SearchItem) => item.type?.toLowerCase() === activeTab.toLowerCase());


  const TABS = [
    { id: 'all', label: 'TOUT', icon: Grid },
    { id: 'Anime', label: 'ANIME', icon: Tv },
    { id: 'Manga', label: 'MANGA', icon: Tv }, // Using Tv icon as placeholder or BookOpen if available
    { id: 'Actor', label: 'SEIYUU', icon: Tv },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#020202] relative overflow-hidden">
        {/* Ambient Glows */}
        <div className="fixed inset-0 pointer-events-none z-0 opacity-10">
          <div className={`absolute top-1/4 left-1/4 w-[600px] h-[600px] blur-[150px] rounded-full transition-colors duration-1000 ${mode === 'global' ? 'bg-blue-600/20' : 'bg-purple-600/20'}`} />
          <div className={`absolute bottom-1/4 right-1/4 w-[600px] h-[600px] blur-[150px] rounded-full transition-colors duration-1000 ${mode === 'global' ? 'bg-emerald-600/20' : 'bg-red-600/20'}`} />
        </div>

        <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
          <header className="mb-12 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-[0.3em] text-blue-500 mb-8">
              <Terminal className="w-3 h-3" /> Universal Search Protocol v3.0
            </div>
            <h1 className="text-8xl font-black italic manga-font uppercase tracking-tighter text-white mb-6">
              UNIVERSAL <span className={mode === 'global' ? 'text-blue-500 text-glow' : 'text-purple-600 text-glow'}>SEARCH</span>
            </h1>
            
            {/* Mode Switcher */}
            <div className="flex justify-center gap-4 mb-12">
                <button 
                    onClick={() => setMode('global')}
                    className={`px-8 py-4 rounded-3xl flex items-center gap-3 transition-all font-black italic text-xs uppercase tracking-[0.2em] border-2 ${
                        mode === 'global' 
                        ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_30px_rgba(37,99,235,0.4)] scale-105' 
                        : 'bg-white/5 border-white/5 text-white/30 hover:bg-white/10'
                    }`}
                >
                    <Search className="w-5 h-5" /> Meta-Search
                </button>
                <button 
                    onClick={() => setMode('visual')}
                    className={`px-8 py-4 rounded-3xl flex items-center gap-3 transition-all font-black italic text-xs uppercase tracking-[0.2em] border-2 ${
                        mode === 'visual' 
                        ? 'bg-purple-600 border-purple-500 text-white shadow-[0_0_30px_rgba(147,51,234,0.4)] scale-105' 
                        : 'bg-white/5 border-white/5 text-white/30 hover:bg-white/10'
                    }`}
                >
                    <Eye className="w-5 h-5" /> Visual Nexus
                </button>
            </div>

            <form onSubmit={handleSearch} className="max-w-3xl mx-auto flex gap-4">
                <div className="relative flex-grow group">
                    <Search className={`absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 transition-colors ${mode === 'global' ? 'text-blue-500/20 group-focus-within:text-blue-500' : 'text-purple-500/20 group-focus-within:text-purple-500'}`} />
                    <input
                        type="text"
                        aria-label="Rechercher"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={mode === 'global' ? "Rechercher un anime, manga, seiyuu..." : "Décrivez une scène visuelle ou un moment précis..."}
                        className="w-full bg-black border-2 border-white/5 rounded-[2.5rem] py-6 pl-16 pr-8 text-lg font-bold focus:border-blue-500 outline-none transition-all placeholder:opacity-20"
                    />
                </div>
                <Button 
                    type="submit" 
                    className={`px-10 rounded-[2.5rem] font-black italic text-xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none ${mode === 'global' ? 'bg-blue-600 hover:bg-blue-500' : 'bg-purple-600 hover:bg-purple-500'}`}
                >
                    SCAN
                </Button>
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
                    {/* Tabs / Filters */}
                    <div className="flex justify-center gap-2 mb-12 overflow-x-auto pb-4 no-scrollbar">
                        {TABS.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`px-6 py-3 rounded-2xl flex items-center gap-3 transition-all font-black italic text-[10px] uppercase tracking-widest border-2 ${
                                    activeTab === tab.id 
                                    ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_20px_rgba(59,130,246,0.4)] scale-105' 
                                    : 'bg-white/5 border-white/5 text-white/30 hover:bg-white/10'
                                }`}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {isGlobalLoading ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                            {[1,2,3,4].map(i => <CardSkeleton key={i} />)}
                        </div>
                    ) : filteredGlobalResults.length === 0 ? (
                        <div className="text-center py-32 opacity-20 border-4 border-dashed border-white/5 rounded-[4rem]">
                            <Search className="w-24 h-24 mx-auto mb-6" />
                            <p className="text-2xl font-black italic manga-font uppercase">Aucun résultat meta-data</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                            {filteredGlobalResults.map((item: SearchItem, i: number) => (
                                <Link key={i} to={`/media/${item.type}/${item.id}/`} className="no-underline group">
                                    <Card padding="none" className="h-full overflow-hidden bg-navy-900/40 border-white/5 hover:border-blue-500/30 transition-all duration-500 hover:-translate-y-2 relative rounded-3xl shadow-2xl">
                                        <div className="aspect-[2/3] relative overflow-hidden bg-black shadow-inner">
                                            {item.image_url ? (
                                                <img src={item.image_url} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" alt={item.title} loading="lazy" decoding="async" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center opacity-10">
                                                    <Sparkles className="w-16 h-16 text-white" />
                                                </div>
                                            )}
                                            <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
                                            
                                            <Badge variant="primary" className="absolute top-4 right-4 bg-blue-600/80 backdrop-blur-md border-none text-[8px] font-black italic">
                                                {item.type}
                                            </Badge>
                                        </div>
                                        
                                        <div className="p-6">
                                            <h3 className="font-black italic text-lg leading-tight mb-2 uppercase manga-font text-white group-hover:text-blue-400 transition-colors line-clamp-2">
                                                {item.title || item.name}
                                            </h3>
                                        </div>
                                    </Card>
                                </Link>
                            ))}
                        </div>
                    )}
                </motion.div>
            ) : (
                <motion.div 
                    key="visual"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                >
                    <div className="space-y-12">
                        <div className="flex items-center justify-between px-4">
                            <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                                <Layers className="w-4 h-4 text-purple-400" /> Segments Temporels Identifiés
                            </h3>
                            {visualResults.length > 0 && (
                                <Badge variant="primary" className="bg-purple-600 text-[8px] font-black">{visualResults.length} MOMENTS TROUVÉS</Badge>
                            )}
                        </div>

                        {visualMutation.isPending ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {[1, 2, 3].map(i => (
                                    <Card key={i} className="aspect-video bg-white/5 border-white/5 animate-pulse rounded-3xl"><></></Card>
                                ))}
                            </div>
                        ) : visualResults.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {visualResults.map((segment, idx) => (
                                    <Card key={idx} padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-purple-500/30 transition-all duration-500 rounded-3xl relative shadow-2xl">
                                        <div className="aspect-video bg-black relative">
                                            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-900/20 to-black">
                                                <Film className="w-12 h-12 text-white/10 group-hover:scale-110 transition-transform duration-700" />
                                            </div>
                                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                <div className="w-16 h-16 rounded-full bg-purple-600 flex items-center justify-center shadow-2xl scale-75 group-hover:scale-100 transition-transform duration-500">
                                                    <Play className="w-8 h-8 text-white fill-current" />
                                                </div>
                                            </div>
                                            <div className="absolute bottom-4 right-4 px-3 py-1 bg-black/80 backdrop-blur-md rounded-lg text-[10px] font-mono font-bold text-white flex items-center gap-2">
                                                <Clock className="w-3 h-3 text-purple-400" />
                                                {Math.floor(segment.start_time / 60)}:{(segment.start_time % 60).toString().padStart(2, '0')}
                                            </div>
                                        </div>
                                        <div className="p-6">
                                            <h4 className="font-black italic text-lg uppercase manga-font mb-2 truncate group-hover:text-purple-400 transition-colors">
                                                {segment.media_title || `Vidéo #${segment.video_id}`}
                                            </h4>
                                            <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed line-clamp-2 italic mb-4">
                                                "{segment.description}"
                                            </p>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-48 opacity-10 border-4 border-dashed border-white/5 rounded-[4rem]">
                                <Video className="w-32 h-32 mx-auto mb-8" />
                                <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Moteur Optique Prêt</h3>
                                <p className="text-sm font-bold uppercase tracking-[0.3em]">Entrez une description pour scanner la base de clips.</p>
                            </div>
                        )}
                    </div>
                </motion.div>
            )}
          </AnimatePresence>

          {/* Global Suggestion / Tech stats */}
          <footer className="mt-32 pt-16 border-t border-white/5 grid grid-cols-1 md:grid-cols-3 gap-12 text-center md:text-left opacity-30">
              <div className="space-y-4">
                  <Badge variant="neutral" className="bg-white/5 border-none">Multimodal RAG</Badge>
                  <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider">
                      La recherche unifiée combine les métadonnées de MAL/AniList avec l'analyse d'images par Computer Vision.
                  </p>
              </div>
              <div className="space-y-4">
                  <Badge variant="neutral" className="bg-white/5 border-none">Knowledge Graph</Badge>
                  <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider">
                      Toutes les entités sont reliées via Neo4j, permettant de trouver des corrélations thématiques entre anime et manga.
                  </p>
              </div>
              <div className="space-y-4">
                  <Badge variant="neutral" className="bg-white/5 border-none">Temporal Index</Badge>
                  <p className="text-[10px] font-bold uppercase leading-relaxed tracking-wider">
                      L'indexation temporelle permet de chercher directement des frames au sein des épisodes.
                  </p>
              </div>
          </footer>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default UniversalSearchHubPage;


