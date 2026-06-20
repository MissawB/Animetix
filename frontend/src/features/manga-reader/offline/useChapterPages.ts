import { useEffect, useRef, useState } from 'react';
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
  const objectUrls = useRef<string[]>([]);

  useEffect(() => {
    let active = true;
    setSource('loading');
    setPages([]);

    const revoke = () => {
      objectUrls.current.forEach((u) => URL.revokeObjectURL(u));
      objectUrls.current = [];
    };

    (async () => {
      const num = Number(chapterNumber);
      if (await isChapterDownloaded(mediaId, num)) {
        const blobs = await getChapterPageBlobs(mediaId, num);
        if (!active) return;
        const offlinePages = blobs.map((blob, index) => {
          const url = URL.createObjectURL(blob);
          objectUrls.current.push(url);
          return { url, index };
        });
        setPages(offlinePages);
        setSource('offline');
        return;
      }

      try {
        const chapter = await apiClient(`/api/v1/media/Manga/${mediaId}/chapters/${chapterNumber}/`);
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
      revoke();
    };
  }, [mediaId, chapterNumber]);

  return { pages, source };
}
