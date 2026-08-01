import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BookOpen } from 'lucide-react';
import { apiClient } from '../../../utils/apiClient';
import { useAuthStore } from '../../../store/authStore';
import { ChapterDownloadButton, type ApiChapter } from './ChapterDownloadButton';
import { ChapterReadBadge } from './ChapterReadBadge';
import { useMangaProgress, mangaProgressKey } from '../progress/useMangaProgress';
import { markChaptersRead } from '../progress/progressService';

export const ChapterList: React.FC<{ mediaId: string; mediaTitle: string }> = ({
  mediaId,
  mediaTitle,
}) => {
  const { data, isLoading, isError } = useQuery<ApiChapter[]>({
    queryKey: ['media', 'Manga', mediaId, 'chapters'],
    queryFn: () => apiClient(`/api/v1/media/Manga/${mediaId}/chapters/`),
  });

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { data: progressData, byChapter } = useMangaProgress(mediaId, isAuthenticated);
  const queryClient = useQueryClient();

  const handleToggleRead = (chapterNumber: number, next: boolean) => {
    void markChaptersRead(mediaId, [chapterNumber], next).then(() =>
      queryClient.invalidateQueries({ queryKey: mangaProgressKey(mediaId) }),
    );
  };

  if (isLoading) {
    return (
      <p className="text-xs opacity-30 uppercase tracking-widest italic">
        Chargement des chapitres...
      </p>
    );
  }
  if (isError) {
    return (
      <p className="text-xs opacity-30 uppercase tracking-widest italic">
        Erreur lors du chargement des chapitres.
      </p>
    );
  }
  if (!data || data.length === 0) {
    return (
      <p className="text-xs opacity-30 uppercase tracking-widest italic">
        Aucun chapitre disponible.
      </p>
    );
  }

  return (
    <section>
      <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-anime-accent" /> Chapitres
      </h3>
      {progressData?.resume && (
        <Link
          to={`/media/manga/${mediaId}/${progressData.resume.chapter_number}/`}
          className="mb-4 flex items-center justify-between rounded-2xl border border-anime-accent/30 bg-anime-accent/10 px-4 py-3 text-xs font-black uppercase tracking-widest text-anime-accent no-underline"
        >
          Reprendre au chapitre {progressData.resume.chapter_number}
          <span className="opacity-60">
            {progressData.read_count}/{progressData.total_count} lus
          </span>
        </Link>
      )}
      <div className="space-y-2">
        {data.map((chapter) => (
          <div
            key={chapter.id}
            className="flex items-center justify-between p-4 bg-gray-900/50 rounded-2xl border border-white/5 hover:border-white/10 transition-colors"
          >
            <Link
              to={`/media/manga/${mediaId}/${chapter.number}/`}
              className="flex-1 no-underline text-current group"
            >
              <span className="text-[10px] font-black opacity-30 uppercase mr-3">
                #{chapter.number}
              </span>
              <span className="font-bold italic text-sm group-hover:text-anime-accent transition-colors">
                {chapter.title || `Chapitre ${chapter.number}`}
              </span>
            </Link>
            <div className="flex items-center gap-3">
              {isAuthenticated && (
                <ChapterReadBadge
                  progress={byChapter.get(chapter.number)}
                  onToggleRead={(next) => handleToggleRead(chapter.number, next)}
                />
              )}
              <ChapterDownloadButton mediaId={mediaId} mediaTitle={mediaTitle} chapter={chapter} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
