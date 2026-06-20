import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen } from 'lucide-react';
import { apiClient } from '../../../utils/apiClient';
import { ChapterDownloadButton, type ApiChapter } from './ChapterDownloadButton';

export const ChapterList: React.FC<{ mediaId: string; mediaTitle: string }> = ({
  mediaId,
  mediaTitle,
}) => {
  const { data, isLoading, isError } = useQuery<ApiChapter[]>({
    queryKey: ['media', 'Manga', mediaId, 'chapters'],
    queryFn: () => apiClient(`/api/v1/media/Manga/${mediaId}/chapters/`),
  });

  if (isLoading) {
    return <p className="text-xs opacity-30 uppercase tracking-widest italic">Chargement des chapitres...</p>;
  }
  if (isError) {
    return <p className="text-xs opacity-30 uppercase tracking-widest italic">Erreur lors du chargement des chapitres.</p>;
  }
  if (!data || data.length === 0) {
    return <p className="text-xs opacity-30 uppercase tracking-widest italic">Aucun chapitre disponible.</p>;
  }

  return (
    <section>
      <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-anime-accent" /> Chapitres
      </h3>
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
              <span className="text-[10px] font-black opacity-30 uppercase mr-3">#{chapter.number}</span>
              <span className="font-bold italic text-sm group-hover:text-anime-accent transition-colors">
                {chapter.title || `Chapitre ${chapter.number}`}
              </span>
            </Link>
            <ChapterDownloadButton mediaId={mediaId} mediaTitle={mediaTitle} chapter={chapter} />
          </div>
        ))}
      </div>
    </section>
  );
};
