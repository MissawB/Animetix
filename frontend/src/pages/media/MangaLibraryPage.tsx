import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  ArrowLeft, BookOpen, Compass, Loader2, Folder, 
  Search, SlidersHorizontal, Trash2, CheckCircle2, Bookmark, Eye, BookmarkCheck
} from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { FavoriteManga } from '../../types';

export const MangaLibraryPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [favorites, setFavorites] = useState<FavoriteManga[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'reading' | 'plan_to_read' | 'completed'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'title' | 'unread' | 'date_added'>('title');

  const fetchFavorites = async () => {
    try {
      const res = await fetch('/api/v1/media/favorites/');
      if (res.ok) {
        const data = await res.json();
        setFavorites(data);
      }
    } catch (e) {
      console.error('Failed to fetch favorites', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const handleUpdateStatus = async (mediaId: string, status: string | null) => {
    try {
      const options: RequestInit = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || '',
        },
      };
      if (status) {
        options.body = JSON.stringify({ status });
      }
      const res = await fetch(`/api/v1/media/Manga/${mediaId}/favorite/`, options);
      if (res.ok) {
        await fetchFavorites();
      }
    } catch (e) {
      console.error('Failed to update status', e);
    }
  };

  const getCookie = (name: string): string | null => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const getCount = (tab: 'all' | 'reading' | 'plan_to_read' | 'completed') => {
    if (tab === 'all') return favorites.length;
    return favorites.filter(f => f.status === tab).length;
  };

  const getStatusIcon = (status: 'reading' | 'plan_to_read' | 'completed') => {
    switch (status) {
      case 'reading':
        return <BookOpen className="w-3.5 h-3.5" />;
      case 'plan_to_read':
        return <Bookmark className="w-3.5 h-3.5" />;
      case 'completed':
        return <CheckCircle2 className="w-3.5 h-3.5" />;
    }
  };

  const getStatusLabel = (status: 'reading' | 'plan_to_read' | 'completed') => {
    switch (status) {
      case 'reading':
        return t('library.status_reading', 'En cours');
      case 'plan_to_read':
        return t('library.status_plan', 'À lire');
      case 'completed':
        return t('library.status_completed', 'Terminé');
    }
  };

  const filteredFavorites = favorites
    .filter(f => {
      if (activeTab !== 'all' && f.status !== activeTab) return false;
      if (searchQuery) {
        const title = f.manga.title.toLowerCase();
        return title.includes(searchQuery.toLowerCase());
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'title') {
        return a.manga.title.localeCompare(b.manga.title);
      }
      if (sortBy === 'unread') {
        return b.unread_chapters_count - a.unread_chapters_count;
      }
      if (sortBy === 'date_added') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      return 0;
    });

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        <header className="sticky top-0 z-50 bg-[#05050a]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-white/5 rounded-full transition-colors animate-hover"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-yellow-400 mb-0.5">
                <BookmarkCheck className="w-3 h-3 text-yellow-400" />
                {t('library.nav_category', 'Ma Bibliothèque')}
              </div>
              <h1 className="text-lg font-black italic manga-font uppercase flex items-center gap-2">
                {t('library.title', 'Bibliothèque Manga')}
              </h1>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-8">
          {/* Tabs and Controls */}
          <div className="flex flex-col md:flex-row gap-6 justify-between items-center mb-8 border-b border-white/5 pb-6">
            {/* Tabs */}
            <div className="flex bg-white/5 p-1.5 rounded-2xl gap-1 w-full md:w-auto">
              {(['all', 'reading', 'plan_to_read', 'completed'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-grow md:flex-grow-0 px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 ${
                    activeTab === tab 
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-lg font-black scale-105' 
                      : 'text-white/60 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {tab === 'all' && t('library.tab_all', 'Tous')}
                  {tab === 'reading' && t('library.tab_reading', 'En cours')}
                  {tab === 'plan_to_read' && t('library.tab_plan', 'À lire')}
                  {tab === 'completed' && t('library.tab_completed', 'Terminés')}
                  <span className={`ml-2 px-1.5 py-0.5 rounded-md text-[9px] ${activeTab === tab ? 'bg-black/20 text-black' : 'bg-white/10 text-white/60'}`}>
                    {getCount(tab)}
                  </span>
                </button>
              ))}
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto items-center">
              {/* Search */}
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="text"
                  placeholder={t('library.search_placeholder', 'Rechercher un manga...')}
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-white/5 border border-white/5 hover:border-white/10 focus:border-yellow-400/50 outline-none rounded-2xl text-xs transition-all text-white placeholder-white/40"
                />
              </div>

              {/* Sort Dropdown */}
              <div className="flex items-center gap-2 bg-white/5 border border-white/5 rounded-2xl px-4 py-2.5 w-full sm:w-auto justify-between">
                <SlidersHorizontal className="w-4 h-4 text-white/40" />
                <select
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as any)}
                  className="bg-transparent text-xs font-black uppercase tracking-wider text-white border-none outline-none cursor-pointer"
                >
                  <option value="title" className="bg-[#05050a]">{t('library.sort_title', 'Titre')}</option>
                  <option value="unread" className="bg-[#05050a]">{t('library.sort_unread', 'Non lus')}</option>
                  <option value="date_added" className="bg-[#05050a]">{t('library.sort_date', 'Ajoutés')}</option>
                </select>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-yellow-400" />
              <p className="text-xs font-black uppercase tracking-widest text-white/40">{t('library.loading', 'Synchronisation de la bibliothèque...')}</p>
            </div>
          ) : filteredFavorites.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center gap-6 bg-white/5 border border-white/5 backdrop-blur-xl rounded-3xl p-8">
              <Folder className="w-16 h-16 text-white/20 animate-pulse" />
              <div>
                <h2 className="text-xl font-black uppercase tracking-widest text-white mb-2">
                  {t('library.empty_title', 'Bibliothèque vide')}
                </h2>
                <p className="text-sm text-white/40 max-w-md mx-auto">
                  {t('library.empty_subtitle', 'Ajoutez des mangas à votre bibliothèque depuis l\'explorateur pour les organiser et suivre votre lecture.')}
                </p>
              </div>
              <Link 
                to="/explore/tachidesk/"
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-300 hover:to-orange-400 text-black text-xs font-black uppercase tracking-wider rounded-2xl transition-all shadow-lg active:scale-95 border-b-4 border-orange-700"
              >
                <Compass className="w-4 h-4" />
                {t('library.btn_explore', 'Découvrir des mangas')}
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {filteredFavorites.map(fav => (
                <div 
                  key={fav.id}
                  className="bg-white/5 border border-white/5 hover:border-white/10 backdrop-blur-xl rounded-3xl overflow-hidden flex flex-col justify-between transition-all duration-300 group hover:scale-[1.02] hover:bg-white/[0.07]"
                >
                  <div className="relative aspect-[3/4] overflow-hidden bg-gray-900">
                    <img 
                      src={fav.manga.image || '/assets/manga-placeholder.png'} 
                      alt={fav.manga.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    
                    {/* Unread badge */}
                    {fav.unread_chapters_count > 0 && (
                      <div className="absolute top-4 right-4 bg-red-600 text-white text-[10px] font-black uppercase px-2.5 py-1 rounded-full shadow-[0_0_15px_rgba(220,38,38,0.5)] border border-red-500 animate-pulse">
                        +{fav.unread_chapters_count}
                      </div>
                    )}

                    {/* Status badge */}
                    <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-md text-[9px] font-bold tracking-wider text-white px-2.5 py-1 rounded-full border border-white/10 flex items-center gap-1.5 uppercase">
                      {getStatusIcon(fav.status)}
                      {getStatusLabel(fav.status)}
                    </div>
                  </div>

                  <div className="p-5 flex-grow flex flex-col justify-between">
                    <div>
                      <h4 className="text-sm font-black italic manga-font uppercase tracking-tight text-white line-clamp-1 group-hover:text-yellow-400 transition-colors">
                        {fav.manga.title}
                      </h4>
                      {fav.manga.author && (
                        <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest mt-1">
                          {fav.manga.author}
                        </p>
                      )}
                      
                      <div className="mt-3 text-[10px] font-bold text-white/50 bg-white/5 p-2.5 rounded-xl border border-white/5">
                        <div className="flex justify-between items-center">
                          <span>{t('library.last_read', 'Lu')}</span>
                          <span className="text-white font-black">Ch. {fav.last_read_chapter}</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 flex flex-col gap-2">
                      <button 
                        onClick={() => navigate(`/media/manga/${fav.manga.id}/${fav.last_read_chapter + 1}/`)}
                        className="flex items-center justify-center gap-2 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-black text-[10px] font-black uppercase tracking-widest rounded-xl transition-all shadow-md active:scale-95"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        {t('library.btn_continue', 'Continuer')}
                      </button>

                      <div className="flex gap-2">
                        {/* Status update selector dropdown styled as premium button */}
                        <div className="relative flex-grow">
                          <select
                            value={fav.status}
                            onChange={e => handleUpdateStatus(fav.manga.id, e.target.value)}
                            className="w-full text-center py-2 bg-white/5 hover:bg-white/10 text-white/80 text-[9px] font-black uppercase tracking-wider rounded-xl border border-white/5 outline-none cursor-pointer appearance-none"
                          >
                            <option value="reading" className="bg-[#05050a] text-white">{t('library.status_reading', 'En cours')}</option>
                            <option value="plan_to_read" className="bg-[#05050a] text-white">{t('library.status_plan', 'À lire')}</option>
                            <option value="completed" className="bg-[#05050a] text-white">{t('library.status_completed', 'Terminé')}</option>
                          </select>
                        </div>

                        {/* Remove button */}
                        <button 
                          onClick={() => handleUpdateStatus(fav.manga.id, null)}
                          className="p-2 bg-red-600/10 hover:bg-red-600/20 text-red-500 rounded-xl transition-colors border border-red-500/10 hover:border-red-500/20 active:scale-95"
                          title={t('library.remove_favorite', 'Retirer des favoris')}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </AnimatedPage>
  );
};

export default MangaLibraryPage;
