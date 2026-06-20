import { useCallback, useEffect, useState } from 'react';
import {
  downloadChapter,
  isChapterDownloaded,
  deleteChapter,
  type ChapterMeta,
  type DownloadablePage,
} from './offlineLibrary';

export type DownloadStatus = 'idle' | 'downloading' | 'downloaded' | 'error';

export function useChapterDownload(meta: ChapterMeta, pages: DownloadablePage[]) {
  const [status, setStatus] = useState<DownloadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    isChapterDownloaded(meta.mediaId, meta.chapterNumber).then((has) => {
      if (active) setStatus(has ? 'downloaded' : 'idle');
    });
    return () => {
      active = false;
    };
  }, [meta.mediaId, meta.chapterNumber]);

  const download = useCallback(async () => {
    setStatus('downloading');
    setProgress(0);
    setError(null);
    try {
      await downloadChapter(meta, pages, setProgress);
      setStatus('downloaded');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec du téléchargement.');
      setStatus('error');
    }
  }, [meta, pages]);

  const remove = useCallback(async () => {
    await deleteChapter(meta.mediaId, meta.chapterNumber);
    setProgress(0);
    setError(null);
    setStatus('idle');
  }, [meta.mediaId, meta.chapterNumber]);

  return { status, progress, error, download, remove };
}
