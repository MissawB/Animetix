import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchMangaProgress, type ChapterProgress } from './progressService';

export const mangaProgressKey = (mediaId: string) => ['manga', mediaId, 'progress'];

/** Les compteurs de la bibliothèque (`read_count`, `total_chapters`,
 *  `has_started`) sont servis par la liste des favoris, pas par /progress/ :
 *  toute écriture de progression doit invalider les deux clés. */
export const mangaFavoritesKey = ['manga-favorites'];

/** `enabled` porte l'état de connexion : un visiteur anonyme n'émet aucun appel. */
export function useMangaProgress(mediaId: string | undefined, enabled: boolean) {
  // Instant du montage, figé pour la durée de vie du composant. `useState`
  // avec initialiseur paresseux plutôt qu'un `useRef` : `isFresh` se calcule
  // au rendu, et lire `ref.current` au rendu est interdit (react-hooks/refs).
  const [mountedAt] = useState(() => Date.now());

  const query = useQuery({
    queryKey: mangaProgressKey(mediaId ?? ''),
    queryFn: () => {
      // Guard: if mediaId is absent, return empty progress without network call
      // (protects explicit refetch() calls even when enabled is true)
      if (!mediaId) return null;
      return fetchMangaProgress(mediaId);
    },
    enabled: Boolean(mediaId) && enabled,
    // Ces deux options ne sont PAS redondantes avec les `defaultOptions` du
    // QueryClient : elles y sont répétées parce que la correction de la
    // reprise en dépend, et qu'un défaut global reste modifiable ailleurs.
    // Le cache de l'app est persisté 24 h en IndexedDB (utils/queryClient) ;
    // la progression, elle, est réécrite en continu par le lecteur : servir
    // la copie persistée sans la revalider rouvrait le lecteur à la position
    // d'une session précédente.
    staleTime: 0,
    refetchOnMount: 'always',
  });

  const byChapter = useMemo(() => {
    const map = new Map<number, ChapterProgress>();
    query.data?.chapters?.forEach((chapter) => map.set(chapter.number, chapter));
    return map;
  }, [query.data]);

  // « Le serveur a répondu depuis que ce composant est monté ».
  //
  // `isFetched` ne répond PAS à cette question : il est déjà vrai au premier
  // rendu quand la donnée vient de la restauration IndexedDB (l'état persisté
  // embarque son `dataUpdateCount`). `isFetchedAfterMount` non plus : la
  // restauration de `persistQueryClient` est asynchrone et incrémente ce même
  // compteur APRÈS la création de l'observateur, ce qui le fait passer à vrai
  // sans le moindre appel réseau. On date donc la donnée : seule une réponse
  // horodatée après le montage fait autorité.
  //
  // `errorUpdatedAt` compte aussi : un /progress/ en échec est une réponse
  // (il n'y a plus rien à attendre), sinon la reprise resterait suspendue et
  // le lecteur n'écrirait plus jamais.
  const isFresh = query.dataUpdatedAt >= mountedAt || query.errorUpdatedAt >= mountedAt;

  return { ...query, byChapter, isFresh };
}
