import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MangaReader } from '../../features/manga-reader';
import { useReaderStore } from '../../features/manga-reader/stores/useReaderStore';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { apiClient } from '../../utils/apiClient';
import { ArrowLeft, BookOpen, ChevronRight, ServerCrash, Settings, WifiOff } from 'lucide-react';
import { useChapterPages } from '../../features/manga-reader/offline/useChapterPages';
import { useReadingProgress } from '../../features/manga-reader/progress/useReadingProgress';
import { useResumeReadingPosition } from '../../features/manga-reader/progress/useResumeReadingPosition';
import { useAuthStore } from '../../store/authStore';

const MangaReaderPage: React.FC = () => {
  const { t } = useTranslation();
  const { mediaId, chapterId } = useParams<{ mediaId: string; chapterId: string }>();
  const navigate = useNavigate();
  const { setPages, setCurrentPageIndex, currentPageIndex, pages: readerPages } = useReaderStore();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isAuthLoading = useAuthStore((s) => s.isLoading);

  // Fetch Manga Metadata
  const { data: manga } = useQuery({
    queryKey: ['media', 'Manga', mediaId],
    queryFn: () => apiClient(`/api/v1/media/Manga/${mediaId}/`),
  });

  const { pages, source } = useChapterPages(mediaId!, chapterId!);

  useEffect(() => {
    setPages(pages);
    setCurrentPageIndex(0);
  }, [pages, setPages, setCurrentPageIndex]);

  // Resumes at the saved position — once per chapter. See
  // useResumeReadingPosition for why the guard must wait on the progress
  // query settling rather than firing the moment pages are ready.
  const { isResolved } = useResumeReadingPosition({
    mediaId,
    chapterId,
    isAuthenticated,
    isAuthLoading,
    readerPagesLength: readerPages.length,
    setCurrentPageIndex,
  });
  // Writes the reading position as it changes; the server itself pushes to
  // AniList/MyAnimeList when a chapter flips to read, so no separate sync call
  // is made here — neither on the last page nor on "next chapter".
  // Gated on `isResolved` as well as auth: before the resume answer lands,
  // currentPageIndex is a placeholder 0, and writing it would wipe the very
  // progress we are about to restore.
  const { saveState, markCurrentChapterRead } = useReadingProgress({
    mediaId,
    chapterNumber: chapterId,
    enabled: isAuthenticated && isResolved,
  });

  const handleNextChapter = () => {
    if (mediaId && chapterId) {
      // Skipping ahead still counts the current chapter as finished — through
      // the normal progress path, which is also what notifies the trackers.
      markCurrentChapterRead();
      navigate(`/media/manga/${mediaId}/${parseFloat(chapterId) + 1}/`);
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        {/* Top Navigation Bar */}
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
                <BookOpen className="w-3 h-3" />
                Manga Reader
              </div>
              <h1 className="text-lg font-black italic manga-font uppercase flex items-center gap-2">
                {manga?.title || t('common.loading', 'Chargement...')}
                <ChevronRight className="w-4 h-4 opacity-30" />
                <span className="text-anime-accent">Chapter {chapterId}</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {readerPages.length > 0 && (
              <span className="text-[10px] font-black uppercase tracking-widest opacity-40">
                Page {currentPageIndex + 1}/{readerPages.length}
                {saveState === 'error' && <span className="ml-2 text-red-400">Non enregistré</span>}
              </span>
            )}
            {source === 'offline' && (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 text-[10px] font-black uppercase tracking-widest">
                <WifiOff className="w-3 h-3" /> {t('common.offline', 'Hors-ligne')}
              </span>
            )}
            <button className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5">
              <Settings className="w-5 h-5 opacity-60" />
            </button>
          </div>
        </header>

        <main className="container mx-auto px-4 py-12">
          {source === 'unreachable' ? (
            <div className="flex flex-col items-center justify-center py-32 text-center gap-4">
              <ServerCrash className="w-12 h-12 text-red-500" />
              <p className="text-sm font-black uppercase tracking-widest opacity-60">
                {t('media.reader.source_unreachable', 'Source manga injoignable')}
              </p>
              <p className="text-xs opacity-30 max-w-md">
                {t(
                  'media.reader.source_unreachable_hint',
                  "Le serveur de chapitres (Suwayomi) n'a pas répondu. Vérifie qu'il est démarré, puis recharge la page.",
                )}
              </p>
            </div>
          ) : source === 'unavailable' ? (
            <div className="flex flex-col items-center justify-center py-32 text-center gap-4">
              <WifiOff className="w-12 h-12 text-red-500" />
              <p className="text-sm font-black uppercase tracking-widest opacity-60">
                {t('media.reader.unavailable_offline', 'Chapitre indisponible hors-ligne')}
              </p>
              <p className="text-xs opacity-30">
                {t(
                  'media.reader.download_online_hint',
                  'Téléchargez ce chapitre lorsque vous êtes connecté.',
                )}
              </p>
            </div>
          ) : (
            <MangaReader />
          )}
        </main>

        {/* Bottom Navigation (Quick Chapter Switch) */}
        <footer className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
          <div className="bg-navy-900/90 backdrop-blur-2xl border border-white/10 px-8 py-4 rounded-full shadow-2xl flex items-center gap-8">
            <button
              onClick={() => navigate(`/media/manga/${mediaId}/${parseFloat(chapterId!) - 1}/`)}
              disabled={parseFloat(chapterId!) <= 1}
              className="text-xs font-black uppercase tracking-tighter opacity-40 hover:opacity-100 transition-opacity disabled:hidden"
            >
              {t('media.reader.prev_chapter', 'Chapitre Précédent')}
            </button>
            <div className="w-px h-4 bg-white/10"></div>
            <button
              onClick={handleNextChapter}
              className="text-xs font-black uppercase tracking-tighter opacity-40 hover:opacity-100 transition-opacity"
            >
              {t('media.reader.next_chapter', 'Chapitre Suivant')}
            </button>
          </div>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default MangaReaderPage;
