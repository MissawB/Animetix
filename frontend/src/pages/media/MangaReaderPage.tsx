import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MangaReader } from '../../features/manga-reader';
import { useReaderStore } from '../../features/manga-reader/stores/useReaderStore';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { apiClient } from '../../utils/apiClient';
import { ArrowLeft, BookOpen, ChevronRight, Settings } from 'lucide-react';

const MangaReaderPage: React.FC = () => {
  const { mediaId, chapterId } = useParams<{ mediaId: string; chapterId: string }>();
  const navigate = useNavigate();
  const { setPages, setCurrentPageIndex } = useReaderStore();

  // Fetch Manga Metadata
  const { data: manga } = useQuery({
    queryKey: ['media', 'Manga', mediaId],
    queryFn: () => apiClient(`/api/v1/media/Manga/${mediaId}/`),
  });

  // Fetch Chapter Content
  const { data: chapter, isLoading: isChapterLoading } = useQuery({
    queryKey: ['media', 'Manga', mediaId, 'chapters', chapterId],
    queryFn: () => apiClient(`/api/v1/media/Manga/${mediaId}/chapters/${chapterId}/`),
  });

  useEffect(() => {
    if (chapter?.pages) {
      const formattedPages = chapter.pages.map((p: any) => ({
        url: p.image_url,
        index: p.number
      }));
      setPages(formattedPages);
      setCurrentPageIndex(0);
    }
  }, [chapter, setPages, setCurrentPageIndex]);

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
                {manga?.title || 'Chargement...'}
                <ChevronRight className="w-4 h-4 opacity-30" />
                <span className="text-anime-accent">Chapter {chapterId}</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5">
              <Settings className="w-5 h-5 opacity-60" />
            </button>
          </div>
        </header>

        <main className="container mx-auto px-4 py-12">
          <MangaReader />
        </main>

        {/* Bottom Navigation (Quick Chapter Switch) */}
        <footer className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
            <div className="bg-navy-900/90 backdrop-blur-2xl border border-white/10 px-8 py-4 rounded-full shadow-2xl flex items-center gap-8">
                <button className="text-xs font-black uppercase tracking-tighter opacity-40 hover:opacity-100 transition-opacity">Chapitre Précédent</button>
                <div className="w-px h-4 bg-white/10"></div>
                <button className="text-xs font-black uppercase tracking-tighter opacity-40 hover:opacity-100 transition-opacity">Chapitre Suivant</button>
            </div>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default MangaReaderPage;
