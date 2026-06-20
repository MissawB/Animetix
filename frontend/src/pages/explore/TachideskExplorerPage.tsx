import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Search, ArrowLeft, Loader2, BookOpen, CheckCircle, AlertCircle, RefreshCw, X, ChevronRight, Download, Trash2, ArrowUpCircle } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface Source {
  id: string;
  name: string;
  lang: string;
}

interface Manga {
  id: string;
  title: string;
  thumbnailUrl: string;
}

interface Chapter {
  id: string;
  name: string;
  chapterNumber: number;
}

interface Extension {
  pkgName: string;
  name: string;
  versionName: string;
  isInstalled: boolean;
  hasUpdate: boolean;
  lang: string;
  iconUrl: string;
  isNsfw: boolean;
  isObsolete: boolean;
}

const TachideskExplorerPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'catalog' | 'extensions'>('catalog');
  
  // Catalog States
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [mangas, setMangas] = useState<Manga[]>([]);
  const [selectedManga, setSelectedManga] = useState<Manga | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  
  // Extension States
  const [extensions, setExtensions] = useState<Extension[]>([]);
  const [extensionSearchQuery, setExtensionSearchQuery] = useState('');
  const [actionProgress, setActionProgress] = useState<Record<string, boolean>>({});

  // Loading States
  const [loadingSources, setLoadingSources] = useState(false);
  const [loadingMangas, setLoadingMangas] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [loadingExtensions, setLoadingExtensions] = useState(false);
  const [importingChapter, setImportingChapter] = useState<string | null>(null);
  
  // Feedback Messages
  const [error, setError] = useState<string | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  // Fetch available sources on mount
  useEffect(() => {
    fetchSources();
  }, []);

  // Fetch extensions when tab changes
  useEffect(() => {
    if (activeTab === 'extensions') {
      setSelectedManga(null); // Close detail drawer
      fetchExtensions();
    }
  }, [activeTab]);

  const fetchSources = async () => {
    setLoadingSources(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/explore/suwayomi/sources/');
      if (!res.ok) throw new Error('Impossible de charger les sources Suwayomi');
      const data = await res.json();
      setSources(data);
      if (data.length > 0 && !selectedSource) {
        setSelectedSource(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue lors du chargement des sources');
    } finally {
      setLoadingSources(false);
    }
  };

  const fetchExtensions = async () => {
    setLoadingExtensions(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/explore/suwayomi/extensions/');
      if (!res.ok) throw new Error('Impossible de charger les extensions Suwayomi');
      const data = await res.json();
      setExtensions(data);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des extensions');
    } finally {
      setLoadingExtensions(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedSource) return;

    setLoadingMangas(true);
    setError(null);
    setMangas([]);
    try {
      const res = await fetch(`/api/v1/explore/suwayomi/search/?source_id=${selectedSource}&q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error('La recherche a échoué');
      const data = await res.json();
      setMangas(data);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la recherche des mangas');
    } finally {
      setLoadingMangas(false);
    }
  };

  // Trigger search on source change
  useEffect(() => {
    if (selectedSource && activeTab === 'catalog') {
      handleSearch();
    }
  }, [selectedSource, activeTab]);

  const selectManga = async (manga: Manga) => {
    setSelectedManga(manga);
    setChapters([]);
    setLoadingDetails(true);
    setError(null);

    try {
      const extId = `suwayomi:${selectedSource}:${manga.id}`;
      const res = await fetch(`/api/v1/media/Manga/${extId}/chapters/`);
      if (res.ok) {
        const data = await res.json();
        setChapters(data);
      } else {
        const importRes = await fetch('/api/v1/explore/suwayomi/import/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            source_id: selectedSource,
            suwayomi_manga_id: manga.id
          })
        });
        if (importRes.ok) {
          const chRes = await fetch(`/api/v1/media/Manga/${extId}/chapters/`);
          if (chRes.ok) {
            setChapters(await chRes.json());
          }
        }
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleReadChapter = async (chapter: Chapter) => {
    if (!selectedManga) return;
    setImportingChapter(chapter.id);
    setImportStatus("Synchronisation en cours...");

    const extId = `suwayomi:${selectedSource}:${selectedManga.id}`;

    try {
      const res = await fetch('/api/v1/explore/suwayomi/import/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_id: selectedSource,
          suwayomi_manga_id: selectedManga.id
        })
      });

      if (!res.ok) throw new Error("Erreur d'importation");

      setImportStatus("Redirection vers le lecteur...");
      navigate(`/media/manga/${extId}/${chapter.chapterNumber}/`);
    } catch (err: any) {
      setError("Impossible d'importer le chapitre. Vérifiez votre connexion Suwayomi.");
      setImportStatus(null);
    } finally {
      setImportingChapter(null);
    }
  };

  const handleExtensionAction = async (pkgName: string, action: 'install' | 'uninstall' | 'update') => {
    setActionProgress(prev => ({ ...prev, [pkgName]: true }));
    setError(null);
    try {
      const res = await fetch('/api/v1/explore/suwayomi/extensions/action/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ids: [pkgName],
          action
        })
      });
      if (!res.ok) throw new Error(`L'action ${action} a échoué`);
      
      // Refresh both list of extensions and sources list to sync
      await fetchExtensions();
      await fetchSources();
    } catch (err: any) {
      setError(err.message || `Une erreur est survenue lors de l'exécution de l'action ${action}`);
    } finally {
      setActionProgress(prev => ({ ...prev, [pkgName]: false }));
    }
  };

  const getProxiedImageUrl = (url: string) => {
    if (!url) return 'https://via.placeholder.com/300x450';
    if (url.startsWith('/api/')) return url;
    try {
      const utf8Bytes = new TextEncoder().encode(url);
      const binaryString = Array.from(utf8Bytes, byte => String.fromCharCode(byte)).join('');
      const encoded = btoa(binaryString);
      return `/api/v1/media/Manga/suwayomi-image/?page_url=${encoded}`;
    } catch (e) {
      return url;
    }
  };

  // Extensions filtering
  const filteredExtensions = extensions.filter(ext => 
    ext.name.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
    ext.pkgName.toLowerCase().includes(extensionSearchQuery.toLowerCase()) ||
    ext.lang.toLowerCase().includes(extensionSearchQuery.toLowerCase())
  );

  const updateExtensions = filteredExtensions.filter(ext => ext.hasUpdate);
  const installedExtensions = filteredExtensions.filter(ext => ext.isInstalled && !ext.hasUpdate);
  const availableExtensions = filteredExtensions.filter(ext => !ext.isInstalled);

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white flex flex-col">
        {/* Header navigation bar */}
        <header className="bg-navy-950/40 backdrop-blur-xl border-b border-white/5 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
          <div className="flex items-center gap-6">
            <Link to="/explore/" className="p-2 hover:bg-white/5 rounded-full transition-colors text-white">
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <div>
              <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-0.5">
                <Globe className="w-3.5 h-3.5" />
                Mihon Integration
              </div>
              <h1 className="text-2xl font-black italic uppercase tracking-tight flex items-center gap-2">
                Tachidesk Explorer
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Tab Selector */}
            <div className="bg-navy-900/60 p-1.5 rounded-2xl flex gap-1 border border-white/5">
              <button
                onClick={() => setActiveTab('catalog')}
                className={`px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${
                  activeTab === 'catalog'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                Catalogue
              </button>
              <button
                onClick={() => setActiveTab('extensions')}
                className={`px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${
                  activeTab === 'extensions'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                Extensions
              </button>
            </div>

            <button 
              onClick={activeTab === 'catalog' ? fetchSources : fetchExtensions} 
              disabled={loadingSources || loadingExtensions}
              className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5 disabled:opacity-50"
              title={activeTab === 'catalog' ? "Rafraîchir les sources" : "Rafraîchir les extensions"}
            >
              <RefreshCw className={`w-5 h-5 opacity-60 ${(loadingSources || loadingExtensions) ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </header>

        {/* Error panel */}
        {error && (
          <div className="mx-8 mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div>{error}</div>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="flex-1 flex overflow-hidden">
          {/* Main panel */}
          {activeTab === 'catalog' ? (
            /* CATALOG TAB VIEW */
            <>
              <main className="flex-1 overflow-y-auto px-8 py-8 space-y-8">
                {/* Search and Source Selector */}
                <div className="bg-navy-950/20 backdrop-blur-md border border-white/5 p-6 rounded-3xl flex flex-col md:flex-row gap-4 items-center">
                  <div className="w-full md:w-1/3 flex flex-col gap-1.5">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Source Suwayomi</label>
                    <select
                      value={selectedSource}
                      onChange={(e) => setSelectedSource(e.target.value)}
                      className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-semibold"
                    >
                      {sources.length === 0 && !loadingSources ? (
                        <option value="">Aucune source installée</option>
                      ) : (
                        sources.map((src) => (
                          <option key={src.id} value={src.id}>
                            {src.name} ({src.lang.toUpperCase()})
                          </option>
                        ))
                      )}
                    </select>
                  </div>

                  <form onSubmit={handleSearch} className="w-full md:flex-1 flex flex-col gap-1.5">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500">Rechercher</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Rechercher un manga (ex: Solo Leveling)..."
                        className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-medium"
                      />
                      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    </div>
                  </form>

                  <button
                    onClick={() => handleSearch()}
                    disabled={loadingMangas}
                    className="mt-5 w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-black uppercase italic rounded-xl flex items-center justify-center gap-2 transition-all"
                  >
                    {loadingMangas ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rechercher'}
                  </button>
                </div>

                {/* Results Grid */}
                <div className="space-y-4">
                  <h2 className="text-lg font-black uppercase tracking-widest flex items-center gap-3">
                    Résultats du Catalogue
                    <span className="h-px bg-white/5 flex-1" />
                  </h2>

                  {loadingMangas ? (
                    <div className="flex flex-col items-center justify-center py-24 gap-4">
                      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                      <p className="text-gray-400 text-sm font-semibold">Parcours du catalogue externe...</p>
                    </div>
                  ) : mangas.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-24 text-gray-500">
                      <Globe className="w-12 h-12 mb-4 opacity-20" />
                      <p className="font-bold">Aucun manga trouvé</p>
                      <p className="text-sm opacity-60">Sélectionnez une source ou installez-en depuis l'onglet Extensions.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
                      {mangas.map((manga) => (
                        <motion.div
                          key={manga.id}
                          whileHover={{ scale: 1.03 }}
                          className={`rounded-2xl border transition-all overflow-hidden relative cursor-pointer group bg-[#0d0d1b]/40 backdrop-blur-md ${
                            selectedManga?.id === manga.id ? 'border-blue-500 shadow-lg shadow-blue-500/5' : 'border-white/5 hover:border-white/20'
                          }`}
                          onClick={() => selectManga(manga)}
                        >
                          <div className="aspect-[2/3] overflow-hidden relative bg-black/20">
                            <img
                              src={getProxiedImageUrl(manga.thumbnailUrl)}
                              alt={manga.title}
                              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                              loading="lazy"
                            />
                          </div>
                          <div className="p-3">
                            <h4 className="text-xs font-black uppercase line-clamp-2 leading-tight group-hover:text-blue-400 transition-colors">
                              {manga.title}
                            </h4>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              </main>

              {/* Right panel: Sidebar Details */}
              <AnimatePresence>
                {selectedManga && (
                  <motion.aside
                    initial={{ x: 400, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 400, opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    className="w-[400px] border-l border-white/5 bg-[#080811]/90 backdrop-blur-2xl p-8 flex flex-col h-full overflow-hidden"
                  >
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-sm font-black uppercase tracking-widest text-blue-500 flex items-center gap-2">
                        <BookOpen className="w-4 h-4" /> Détails de l'œuvre
                      </h3>
                      <button
                        onClick={() => setSelectedManga(null)}
                        className="p-1.5 hover:bg-white/5 rounded-full transition-colors"
                      >
                        <X className="w-5 h-5 text-gray-400 hover:text-white" />
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-6 pr-2 -mr-2">
                      <div className="flex gap-4">
                        <div className="w-28 aspect-[2/3] rounded-xl overflow-hidden flex-shrink-0 bg-white/5 border border-white/10">
                          <img
                            src={getProxiedImageUrl(selectedManga.thumbnailUrl)}
                            alt={selectedManga.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 flex flex-col justify-center">
                          <h2 className="text-lg font-black uppercase leading-tight italic tracking-tight mb-2">
                            {selectedManga.title}
                          </h2>
                        </div>
                      </div>

                      {importStatus && (
                        <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-3 text-blue-400 text-xs font-semibold">
                          <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
                          <div>{importStatus}</div>
                        </div>
                      )}

                      {/* Chapters List */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-black uppercase tracking-widest text-gray-500 flex items-center justify-between">
                          <span>Chapitres Disponibles</span>
                          <span className="text-[10px] bg-white/5 text-gray-400 px-2 py-0.5 rounded-full">
                            {chapters.length} chapitres
                          </span>
                        </h4>

                        {loadingDetails ? (
                          <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-400">
                            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                            <p className="text-xs font-medium">Récupération des chapitres...</p>
                          </div>
                        ) : chapters.length === 0 ? (
                          <div className="text-center py-12 text-gray-500 text-xs font-semibold border border-dashed border-white/5 rounded-2xl">
                            Aucun chapitre indexé pour ce manga.
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
                            {chapters.map((ch) => (
                              <div
                                key={ch.id}
                                className="p-3 bg-[#0d0d1b]/80 border border-white/5 hover:border-white/15 rounded-xl flex items-center justify-between group transition-all"
                              >
                                <div className="flex flex-col min-w-0 pr-4">
                                  <span className="text-xs font-bold text-gray-200 line-clamp-1 group-hover:text-blue-400 transition-colors">
                                    {ch.name}
                                  </span>
                                  <span className="text-[9px] text-gray-500 font-medium">
                                    Numéro {ch.chapterNumber}
                                  </span>
                                </div>

                                <button
                                  onClick={() => handleReadChapter(ch)}
                                  disabled={!!importingChapter}
                                  className="px-3 py-1.5 bg-blue-500/10 hover:bg-blue-600 border border-blue-500/20 text-blue-400 hover:text-white rounded-lg text-[10px] font-black uppercase italic tracking-wider flex items-center gap-1 hover:scale-[1.03] transition-all disabled:opacity-50"
                                >
                                  {importingChapter === ch.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <>
                                      Lire <ChevronRight className="w-3 h-3" />
                                    </>
                                  )}
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.aside>
                )}
              </AnimatePresence>
            </>
          ) : (
            /* EXTENSIONS TAB VIEW */
            <main className="flex-1 overflow-y-auto px-8 py-8 space-y-6">
              {/* Search Bar for extensions */}
              <div className="bg-navy-950/20 backdrop-blur-md border border-white/5 p-6 rounded-3xl flex justify-between items-center gap-4">
                <div className="relative flex-1 max-w-md">
                  <input
                    type="text"
                    value={extensionSearchQuery}
                    onChange={(e) => setExtensionSearchQuery(e.target.value)}
                    placeholder="Rechercher une extension par nom ou langue (ex: en, fr)..."
                    className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-medium"
                  />
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                </div>
                <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
                  Total : {filteredExtensions.length} / {extensions.length} extensions
                </div>
              </div>

              {loadingExtensions ? (
                <div className="flex flex-col items-center justify-center py-32 gap-4">
                  <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                  <p className="text-gray-400 text-sm font-semibold">Récupération de la liste des extensions...</p>
                </div>
              ) : (
                <div className="space-y-8">
                  {/* CATEGORY 1: Updates Available */}
                  {updateExtensions.length > 0 && (
                    <div className="space-y-4">
                      <h3 className="text-xs font-black uppercase tracking-widest text-blue-500 flex items-center gap-2">
                        <ArrowUpCircle className="w-4 h-4" /> Mises à jour disponibles ({updateExtensions.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {updateExtensions.map((ext) => (
                          <ExtensionRow key={ext.pkgName} ext={ext} onAction={handleExtensionAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* CATEGORY 2: Installed Extensions */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" /> Extensions Installées ({installedExtensions.length})
                    </h3>
                    {installedExtensions.length === 0 ? (
                      <p className="text-xs text-gray-500 italic">Aucune extension installée actuellement.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {installedExtensions.map((ext) => (
                          <ExtensionRow key={ext.pkgName} ext={ext} onAction={handleExtensionAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                        ))}
                      </div>
                    )}
                  </div>

                  {/* CATEGORY 3: Available Extensions */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 flex items-center gap-2">
                      <Globe className="w-4 h-4 text-blue-500" /> Extensions Disponibles ({availableExtensions.length})
                    </h3>
                    {availableExtensions.length === 0 ? (
                      <p className="text-xs text-gray-500 italic">Aucune extension disponible correspondante.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {availableExtensions.map((ext) => (
                          <ExtensionRow key={ext.pkgName} ext={ext} onAction={handleExtensionAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </main>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

interface ExtensionRowProps {
  ext: Extension;
  onAction: (pkgName: string, action: 'install' | 'uninstall' | 'update') => void;
  inProgress: boolean;
  getProxiedImageUrl: (url: string) => string;
}

const ExtensionRow: React.FC<ExtensionRowProps> = ({ ext, onAction, inProgress, getProxiedImageUrl }) => {
  return (
    <div className="p-4 bg-[#0c0c1b]/60 hover:bg-[#0c0c1b]/95 border border-white/5 hover:border-white/10 rounded-2xl flex items-center gap-4 transition-all group">
      {/* Icon */}
      <img
        src={getProxiedImageUrl(ext.iconUrl)}
        alt={ext.name}
        className="w-10 h-10 object-contain bg-white/5 p-1 rounded-xl border border-white/5 flex-shrink-0"
        onError={(e) => {
          e.currentTarget.src = 'https://via.placeholder.com/150?text=Manga';
        }}
      />

      {/* Info details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-bold text-gray-200 line-clamp-1 group-hover:text-blue-400 transition-colors">
            {ext.name}
          </h4>
          <span className="text-[8px] bg-white/5 text-gray-400 px-2 py-0.5 rounded-full font-black uppercase tracking-wider">
            {ext.lang}
          </span>
        </div>
        <p className="text-[10px] text-gray-500 font-medium truncate mt-0.5">
          v{ext.versionName}
        </p>

        {/* Dynamic Warning Badges */}
        <div className="flex gap-1.5 mt-1.5">
          {ext.isNsfw && (
            <span className="bg-red-500/10 text-red-500 border border-red-500/10 text-[7px] font-black uppercase px-1.5 py-0.5 rounded tracking-widest">
              18+
            </span>
          )}
          {ext.isObsolete && (
            <span className="bg-yellow-500/10 text-yellow-500 border border-yellow-500/10 text-[7px] font-black uppercase px-1.5 py-0.5 rounded tracking-widest">
              Obsolète
            </span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex-shrink-0">
        {ext.hasUpdate ? (
          <button
            onClick={() => onAction(ext.pkgName, 'update')}
            disabled={inProgress}
            className="p-2.5 bg-blue-600/10 hover:bg-blue-600 border border-blue-600/20 text-blue-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Mettre à jour l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <ArrowUpCircle className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">MàJ</span>
              </>
            )}
          </button>
        ) : ext.isInstalled ? (
          <button
            onClick={() => onAction(ext.pkgName, 'uninstall')}
            disabled={inProgress}
            className="p-2.5 bg-red-600/10 hover:bg-red-600 border border-red-600/20 text-red-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Désinstaller l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">Suppr.</span>
              </>
            )}
          </button>
        ) : (
          <button
            onClick={() => onAction(ext.pkgName, 'install')}
            disabled={inProgress}
            className="p-2.5 bg-green-600/10 hover:bg-green-600 border border-green-600/20 text-green-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Installer l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">Instal.</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default TachideskExplorerPage;
