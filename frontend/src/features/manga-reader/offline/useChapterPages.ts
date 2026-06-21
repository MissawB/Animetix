import { useEffect, useState } from 'react';
import { apiClient } from '../../../utils/apiClient';
import { isChapterDownloaded, getChapterPageBlobs } from './offlineLibrary';

export type PageSource = 'loading' | 'offline' | 'network' | 'unavailable';
interface ReaderPage {
  url: string;
  index: number;
}

export function useChapterPages(mediaId: string, chapterNumber: string) {
  const [pages, setPages] = useState<ReaderPage[]>([]);
  const [source, setSource] = useState<PageSource>('loading');

  // Reset to the loading state synchronously when the chapter changes by adjusting
  // state during render (React's "storing previous value" pattern). Doing this here
  // instead of in the effect avoids a cascading-render and guarantees the new
  // chapter never briefly shows the previous chapter's pages.
  const chapterKey = `${mediaId}:${chapterNumber}`;
  const [prevChapterKey, setPrevChapterKey] = useState(chapterKey);
  if (prevChapterKey !== chapterKey) {
    setPrevChapterKey(chapterKey);
    setSource('loading');
    setPages([]);
  }

  useEffect(() => {
    let active = true;

    // Object URLs created by THIS effect run only, so a Strict-Mode double-invoke
    // (or rapid chapter change) never revokes URLs a later run still uses.
    const created: string[] = [];

    (async () => {
      const num = Number(chapterNumber);
      if (await isChapterDownloaded(mediaId, num)) {
        const blobs = await getChapterPageBlobs(mediaId, num);
        if (!active) return;
        const offlinePages = blobs.map((blob, index) => {
          const url = URL.createObjectURL(blob);
          created.push(url);
          return { url, index };
        });
        setPages(offlinePages);
        setSource('offline');
        return;
      }

      try {
        // skipToast: this hook owns error presentation (the "unavailable" state);
        // letting apiClient pop a global error toast would contradict that UI.
        const chapter = await apiClient(
          `/api/v1/media/Manga/${mediaId}/chapters/${chapterNumber}/`,
          { skipToast: true },
        );
        if (!active) return;
        const networkPages: ReaderPage[] = (chapter?.pages ?? []).map(
          (p: { image_url: string; number: number }) => ({ url: p.image_url, index: p.number }),
        );
        setPages(networkPages);
        setSource('network');
      } catch {
        if (!active) return;
        setSource('unavailable');
      }
    })();

    return () => {
      active = false;
      created.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [mediaId, chapterNumber]);

  return { pages, source };
}
