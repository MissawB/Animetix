import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchTrackerLinks,
  linkTracker,
  searchTracker,
  unlinkTracker,
  type TrackerName,
} from './trackerLinkService';

export const trackerLinksKey = (mediaId: string) => ['manga', mediaId, 'trackers'];

/** `enabled` porte l'état de connexion : un visiteur anonyme n'émet aucun appel.
 *
 *  Le cache de l'app est persisté 24 h en IndexedDB (`utils/queryClient`) :
 *  `isFetched`/`data` peuvent donc être présents dès le premier rendu avec une
 *  copie de la veille. Ce hook ne s'en sert jamais pour décider qu'une réponse
 *  vient d'arriver — il invalide simplement la clé après chaque mutation, et
 *  le composant appelant affiche un état de chargement en attendant. */
export function useTrackerLinks(mediaId: string, enabled: boolean) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: trackerLinksKey(mediaId),
    queryFn: () => fetchTrackerLinks(mediaId),
    enabled,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: trackerLinksKey(mediaId) });

  const confirm = useMutation({
    mutationFn: ({
      tracker,
      remoteId,
      remoteTitle,
    }: {
      tracker: TrackerName;
      remoteId: string;
      remoteTitle: string;
    }) => linkTracker(mediaId, tracker, remoteId, remoteTitle),
    onSuccess: invalidate,
  });

  const unlink = useMutation({
    mutationFn: (tracker: TrackerName) => unlinkTracker(mediaId, tracker),
    onSuccess: invalidate,
  });

  const search = useMutation({
    mutationFn: ({ tracker, query: q }: { tracker: TrackerName; query: string }) =>
      searchTracker(mediaId, tracker, q),
  });

  return {
    links: query.data?.links ?? [],
    connected: query.data?.connected ?? [],
    isLoading: query.isLoading,
    confirm,
    unlink,
    search,
  };
}
