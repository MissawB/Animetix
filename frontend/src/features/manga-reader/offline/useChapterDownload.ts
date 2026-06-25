import { useCallback, useEffect, useRef, useState } from 'react';
import {
  downloadChapter,
  isChapterDownloaded,
  deleteChapter,
  type ChapterMeta,
  type DownloadablePage,
} from './offlineLibrary';
import { useToastStore } from '../../../store/toastStore';

export type DownloadStatus = 'idle' | 'downloading' | 'downloaded' | 'error';

export function useChapterDownload(meta: ChapterMeta, pages: DownloadablePage[]) {
  const [status, setStatus] = useState<DownloadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Destructure to primitives so the callbacks below memoise on stable values
  // even when callers pass a freshly-built `meta` object on every render.
  const { mediaId, chapterNumber, mediaTitle, chapterTitle } = meta;

  // Lives for the component's lifetime; guards against state updates after unmount.
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    isChapterDownloaded(mediaId, chapterNumber).then((has) => {
      if (active) setStatus(has ? 'downloaded' : 'idle');
    });
    return () => {
      active = false;
    };
  }, [mediaId, chapterNumber]);

  const download = useCallback(async () => {
    setStatus('downloading');
    setProgress(0);
    setError(null);
    try {
      await downloadChapter({ mediaId, chapterNumber, mediaTitle, chapterTitle }, pages, (ratio) => {
        if (mounted.current) setProgress(ratio);
      });
      if (!mounted.current) return;
      setStatus('downloaded');
    } catch (err) {
      if (!mounted.current) return;
      const msg = err instanceof Error ? err.message : 'Échec du téléchargement.';
      setError(msg);
      useToastStore.getState().addToast(msg, 'error');
      setStatus('error');
    }
  }, [mediaId, chapterNumber, mediaTitle, chapterTitle, pages]);

  const remove = useCallback(async () => {
    await deleteChapter(mediaId, chapterNumber);
    if (!mounted.current) return;
    setProgress(0);
    setError(null);
    setStatus('idle');
  }, [mediaId, chapterNumber]);

  return { status, progress, error, download, remove };
}
