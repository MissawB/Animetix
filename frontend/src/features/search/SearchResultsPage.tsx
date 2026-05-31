import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Grid, 
  List as ListIcon, 
  Sparkles, 
  ChevronRight,
  Tv,
  BookOpen,
  User as UserIcon,
  Gamepad2,
  Film
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

const SearchResultsPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [inputValue, setInputValue] = useState(query);
  const [activeTab, setActiveTab] = useState<string>('all');

  useEffect(() => {
    setInputValue(query);
  }, [query]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
        setSearchParams({ q: inputValue.trim() });
    }
  };

  const { data, isLoading, isError } = useQuery<any>({
    queryKey: ['global-search', query],
    queryFn: () => apiClient(`/api/v1/search/?q=${encodeURIComponent(query)}`),
    enabled: !!query,
  });

  const results = Array.isArray(data) ? data : (data as any)?.results || [];

  const filteredResults = activeTab === 'all' 
    ? results 
    : results.filter((item: any) => item.type?.toLowerCase() === activeTab.toLowerCase());

  const TABS = [
    { id: 'all', label: 'TOUT', icon: Grid },
    { id: 'Anime', label: 'ANIME', icon: Tv },
    { id: 'Manga', label: 'MANGA', icon: BookOpen },
    { id: 'Actor', label: 'SEIYUU', icon: UserIcon },
    { id: 'Game', label: 'JEUX', icon: Gamepad2 },
    { id: 'Movie', label: 'FILMS', icon: Film },
  ];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-12">
            <div className="flex items-center gap-4 text-gray-500 mb-4">
                <Search className="w-5 h-5" />
                <span className="text-xs font-black uppercase tracking-widest">Nexus Search Engine v2.0</span>
            </div>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2">
                RÉSULTATS POUR : <span className="text-blue-500 text-glow">"{query}"</span>
            </h1>
            
            <form onSubmit={handleSearch} className="mt-8 max-w-xl flex gap-4">
                <div className="relative flex-grow">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/20" />
                    <input 
                        type="text" 
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Rechercher à nouveau..."
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-6 text-sm font-bold focus:border-blue-500 outline-none transition-all"
                    />
                </div>
                <Button type="submit" variant="primary" className="px-8 bg-blue-600 border-none">RECHERCHER</Button>
            </form>
        </header>

        {/* Tabs / Filters */}
        <div className="flex gap-2 mb-12 overflow-x-auto pb-4 no-scrollbar">
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

        {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
            </div>
        ) : filteredResults.length === 0 ? (
            <div className="text-center py-32 opacity-20 border-4 border-dashed border-white/5 rounded-[4rem]">
                <Search className="w-24 h-24 mx-auto mb-6" />
                <p className="text-2xl font-black italic manga-font uppercase">Aucun résultat dans cette catégorie</p>
            </div>
        ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 animate-fade-in">
                {filteredResults.map((item: any, i: number) => (
                    <Link key={i} to={`/media/${item.type}/${item.id}/`} className="no-underline group">
                        <Card padding="none" className="h-full overflow-hidden bg-navy-900/40 border-white/5 hover:border-blue-500/30 transition-all duration-500 hover:-translate-y-2 relative">
                            <div className="aspect-[2/3] relative overflow-hidden bg-black shadow-inner">
                                {item.image_url ? (
                                    <img src={item.image_url} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" alt={item.title} />
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
                                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-500 opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all">
                                    Consulter la fiche <ChevronRight className="w-3 h-3" />
                                </div>
                            </div>
                        </Card>
                    </Link>
                ))}
            </div>
        )}

        {/* Suggestion Box */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/20 to-transparent border border-white/5 flex flex-col md:flex-row items-center gap-12 text-center md:text-left">
            <div className="p-6 bg-blue-600 rounded-3xl shadow-[0_0_30px_rgba(37,99,235,0.5)]">
                <Sparkles className="w-12 h-12 text-white" />
            </div>
            <div>
                <h4 className="text-3xl font-black italic manga-font uppercase mb-4 tracking-tighter text-white">IA Deep RAG Enabled</h4>
                <p className="text-sm font-bold opacity-40 uppercase leading-relaxed max-w-3xl italic mb-6">
                    La recherche sémantique analyse non seulement les titres, mais aussi les thèmes profonds, les relations entre personnages et les arcs narratifs indexés dans le Knowledge Graph.
                </p>
                <Button 
                    as={Link} 
                    to={`/search/expert/?q=${encodeURIComponent(query)}`}
                    variant="primary" 
                    className="bg-blue-600 border-none px-8 rounded-2xl"
                >
                    PASSER EN MODE EXPERT
                </Button>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SearchResultsPage;
