import React from 'react';
import { Download, Loader2, Trash2, AlertCircle } from 'lucide-react';
import { useChapterDownload } from '../offline/useChapterDownload';
import type { DownloadablePage } from '../offline/offlineLibrary';

export interface ApiChapter {
  id: number;
  number: number;
  title: string;
  pages: DownloadablePage[];
}

export const ChapterDownloadButton: React.FC<{
  mediaId: string;
  mediaTitle: string;
  chapter: ApiChapter;
}> = ({ mediaId, mediaTitle, chapter }) => {
  const meta = {
    mediaId,
    mediaTitle,
    chapterNumber: chapter.number,
    chapterTitle: chapter.title,
  };
  const { status, progress, error, download, remove } = useChapterDownload(meta, chapter.pages);

  if (status === 'downloading') {
    return (
      <span className="flex items-center gap-1.5 text-[10px] font-black text-anime-accent">
        <Loader2 className="w-4 h-4 animate-spin" />
        {Math.round(progress * 100)}%
      </span>
    );
  }

  if (status === 'downloaded') {
    return (
      <button
        type="button"
        onClick={remove}
        aria-label="Supprimer le téléchargement"
        className="p-2 rounded-full text-green-400 hover:bg-red-500/10 hover:text-red-500 transition-colors"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={download}
      aria-label="Télécharger le chapitre"
      title={error || undefined}
      className={`p-2 rounded-full transition-colors ${
        status === 'error' ? 'text-red-500 hover:bg-red-500/10' : 'opacity-50 hover:opacity-100 hover:bg-white/10'
      }`}
    >
      {status === 'error' ? <AlertCircle className="w-4 h-4" /> : <Download className="w-4 h-4" />}
    </button>
  );
};
