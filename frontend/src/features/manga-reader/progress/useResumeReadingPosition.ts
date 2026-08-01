import { useEffect, useRef } from 'react';
import { useMangaProgress } from './useMangaProgress';

interface Options {
  mediaId: string | undefined;
  chapterId: string | undefined;
  isAuthenticated: boolean;
  readerPagesLength: number;
  setCurrentPageIndex: (index: number) => void;
}

/** Reprend la lecture à la page enregistrée pour ce chapitre — une seule
 *  fois par chapitre. La garde ne doit se consommer QUE lorsqu'on sait
 *  vraiment ce qu'il y a (ou pas) à reprendre : `byChapter` vient d'une
 *  requête React Query indépendante de celle qui charge les pages. Si les
 *  pages arrivent avant la réponse de /progress/ (Suwayomi répond avant
 *  Django), figer la garde sur un `byChapter` encore vide ferait échouer la
 *  reprise pour de bon — l'effet se relancerait bien quand la progression
 *  arrive, mais sortirait aussitôt au premier `if`. On distingue donc
 *  « pas encore chargé » (on attend, la garde reste ouverte) de « chargé,
 *  rien à reprendre » (on consomme la garde, sans reprise). */
export function useResumeReadingPosition({
  mediaId,
  chapterId,
  isAuthenticated,
  readerPagesLength,
  setCurrentPageIndex,
}: Options) {
  const { byChapter, isFetched: progressFetched } = useMangaProgress(mediaId, isAuthenticated);
  const resumedRef = useRef<string | null>(null);

  useEffect(() => {
    const key = `${mediaId}:${chapterId}`;
    if (resumedRef.current === key || readerPagesLength === 0) return;
    // Anonymous visitors never run the /progress/ query (see useMangaProgress),
    // so it would never "settle" — nothing to wait for in that case.
    if (isAuthenticated && !progressFetched) return;

    resumedRef.current = key;
    const saved = chapterId ? byChapter.get(Number(chapterId)) : undefined;
    if (saved && !saved.is_read && saved.last_page_read > 0) {
      setCurrentPageIndex(Math.min(saved.last_page_read, readerPagesLength - 1));
    }
  }, [
    mediaId,
    chapterId,
    byChapter,
    readerPagesLength,
    setCurrentPageIndex,
    isAuthenticated,
    progressFetched,
  ]);
}
