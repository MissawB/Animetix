import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, BookOpen, Trash2, WifiOff, HardDrive, Compass, Library, Loader2 } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { listDownloads, deleteChapter, type DownloadedChapter } from '../../features/manga-reader/offline/offlineLibrary';

export const OfflineMangaPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [downloads, setDownloads] = useState<DownloadedChapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [quota, setQuota] = useState<{ usage: number; limit: number } | null>(null);

  // The fetch itself only mutates state *after* awaiting, so it can be invoked from
  // an effect without synchronously calling setState (no cascading-render warning).
  const loadData = async () => {
    try {
      const list = await listDownloads();
      setDownloads(list.sort((a, b) => b.downloadedAt - a.downloadedAt));

      if (navigator.storage && navigator.storage.estimate) {
        const est = await navigator.storage.estimate();
        setQuota({
          usage: est.usage ?? 0,
          limit: est.quota ?? 0
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Manual refresh helper: shows the spinner first, then reloads. Used by the
  // delete / clear-all handlers (not by the mount effect).
  const reload = async () => {
    setLoading(true);
    await loadData();
  };

  useEffect(() => {
    // `loading` already initializes to true. setState runs only inside the async
    // callback (after awaiting), so the effect body itself performs no synchronous
    // setState — the recommended pattern for syncing with an async data source.
    void (async () => {
      await loadData();
    })();
  }, []);

  const handleDelete = async (mediaId: string, chapterNumber: number) => {
    await deleteChapter(mediaId, chapterNumber);
    await reload();
  };

  const handleClearAll = async () => {
    if (window.confirm(t('labs.offline_manga.clear_all_confirm', 'Êtes-vous sûr de vouloir supprimer tous les chapitres téléchargés ?'))) {
      await Promise.all(downloads.map((d) => deleteChapter(d.mediaId, d.chapterNumber)));
      await reload();
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Fallback storage size if quota api fails/blocked
  const calculatedTotalSize = downloads.reduce((acc, curr) => acc + (curr.totalBytes ?? 0), 0);

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        <header className="sticky top-0 z-50 bg-[#05050a]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-white/5 rounded-full transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-anime-accent mb-0.5">
                <Library className="w-3 h-3 text-orange-400" />
                {t('labs.offline_manga.title', 'Manga Hors-ligne')}
              </div>
              <h1 className="text-lg font-black italic manga-font uppercase flex items-center gap-2">
                {t('labs.offline_manga.title', 'Manga Hors-ligne')}
              </h1>
            </div>
          </div>
          {downloads.length > 0 && (
            <button 
              onClick={handleClearAll}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-black uppercase tracking-wider rounded-xl transition-all border border-red-500/20 active:scale-95"
            >
              <Trash2 className="w-4 h-4" />
              {t('labs.offline_manga.clear_all', 'Tout supprimer')}
            </button>
          )}
        </header>

        <main className="container mx-auto px-6 py-8">
          {/* Metrics Panel */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white/5 border border-white/5 backdrop-blur-xl p-6 rounded-3xl flex items-center gap-6">
              <div className="w-12 h-12 bg-orange-500/10 border border-orange-500/20 rounded-2xl flex items-center justify-center text-orange-400">
                <BookOpen className="w-6 h-6" />
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-wider text-white/40 mb-1">
                  {t('labs.offline_manga.stats_chapters', 'Chapitres téléchargés')}
                </p>
                <h3 className="text-3xl font-black italic manga-font">{downloads.length}</h3>
              </div>
            </div>

            <div className="bg-white/5 border border-white/5 backdrop-blur-xl p-6 rounded-3xl flex items-center gap-6">
              <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center text-cyan-400">
                <HardDrive className="w-6 h-6" />
              </div>
              <div className="flex-grow">
                <p className="text-[10px] font-black uppercase tracking-wider text-white/40 mb-1">
                  {t('labs.offline_manga.stats_storage', 'Espace disque utilisé')}
                </p>
                <h3 className="text-3xl font-black italic manga-font">
                  {formatSize(quota ? quota.usage : calculatedTotalSize)}
                </h3>
                {quota && quota.limit > 0 && (
                  <div className="mt-2 w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-cyan-400 h-full shadow-[0_0_10px_#06b6d4] transition-all duration-500" 
                      style={{ width: `${Math.min(100, (quota.usage / quota.limit) * 100)}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
              <p className="text-xs font-black uppercase tracking-widest text-white/40">{t('labs.offline_manga.system_init', 'Initialisation du système...')}</p>
            </div>
          ) : downloads.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center gap-6 bg-white/5 border border-white/5 backdrop-blur-xl rounded-3xl p-8">
              <WifiOff className="w-16 h-16 text-white/20" />
              <div>
                <h2 className="text-xl font-black uppercase tracking-widest text-white mb-2">
                  {t('labs.offline_manga.empty_title', 'Aucun chapitre téléchargé')}
                </h2>
                <p className="text-sm text-white/40 max-w-md mx-auto">
                  {t('labs.offline_manga.empty_subtitle', 'Parcourez le catalogue pour télécharger des chapitres et les lire sans connexion internet.')}
                </p>
              </div>
              <Link 
                to="/explore/"
                className="flex items-center gap-2 px-6 py-3 bg-yellow-400 hover:bg-yellow-300 text-black text-xs font-black uppercase tracking-wider rounded-2xl transition-all shadow-lg active:scale-95"
              >
                <Compass className="w-4 h-4" />
                {t('labs.offline_manga.btn_explore', 'Parcourir les mangas')}
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {downloads.map((d) => (
                <div 
                  key={`${d.mediaId}:${d.chapterNumber}`}
                  className="bg-white/5 border border-white/5 hover:border-white/10 backdrop-blur-xl rounded-3xl p-6 flex flex-col justify-between transition-all group hover:scale-[1.02] hover:bg-white/[0.07]"
                >
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-wider text-orange-400 bg-orange-400/10 px-2.5 py-1 rounded-full">
                      Manga
                    </span>
                    <h4 className="text-base font-black italic manga-font uppercase tracking-tight text-white mt-4 line-clamp-1">
                      {d.mediaTitle}
                    </h4>
                    <p className="text-sm font-bold text-white/80 mt-1 line-clamp-1">
                      Chapter {d.chapterNumber}{d.chapterTitle ? ` : ${d.chapterTitle}` : ''}
                    </p>
                    <div className="flex flex-col gap-1.5 mt-4 text-[10px] font-semibold text-white/40 uppercase tracking-widest">
                      <span>{t('labs.offline_manga.item_pages', '{{count}} pages', { count: d.pageCount })}</span>
                      <span>{formatSize(d.totalBytes)}</span>
                      <span>
                        {t('labs.offline_manga.item_date', 'Téléchargé le {{date}}', {
                          date: new Date(d.downloadedAt).toLocaleDateString()
                        })}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mt-6">
                    <button 
                      onClick={() => navigate(`/media/manga/${d.mediaId}/${d.chapterNumber}/`)}
                      className="flex items-center justify-center gap-2 py-2.5 bg-yellow-400 hover:bg-yellow-300 text-black text-[10px] font-black uppercase tracking-widest rounded-xl transition-all shadow-md active:scale-95"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      {t('labs.offline_manga.btn_read', 'Lire')}
                    </button>
                    <button 
                      onClick={() => handleDelete(d.mediaId, d.chapterNumber)}
                      className="flex items-center justify-center gap-2 py-2.5 bg-white/5 hover:bg-red-500/10 text-white/60 hover:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all border border-white/5 hover:border-red-500/20 active:scale-95"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {t('labs.offline_manga.btn_delete', 'Supprimer')}
                    </button>
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

export default OfflineMangaPage;
