import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchMangaProgress, type ChapterProgress } from './progressService';

export const mangaProgressKey = (mediaId: string) => ['manga', mediaId, 'progress'];

/** `enabled` porte l'état de connexion : un visiteur anonyme n'émet aucun appel. */
export function useMangaProgress(mediaId: string | undefined, enabled: boolean) {
  const query = useQuery({
    queryKey: mangaProgressKey(mediaId ?? ''),
    queryFn: () => fetchMangaProgress(mediaId as string),
    enabled: Boolean(mediaId) && enabled,
  });

  const byChapter = useMemo(() => {
    const map = new Map<number, ChapterProgress>();
    query.data?.chapters?.forEach((chapter) => map.set(chapter.number, chapter));
    return map;
  }, [query.data]);

  return { ...query, byChapter };
}
