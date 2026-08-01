import { apiClient } from '../../../utils/apiClient';

export type TrackerName = 'anilist' | 'myanimelist';

export interface TrackerLink {
  tracker: TrackerName;
  status: 'suggested' | 'confirmed';
  remote_id: string;
  remote_title: string;
  remote_progress: number | null;
}

export interface TrackerCandidate {
  remote_id: string;
  title: string;
  chapters: number | null;
}

const base = (mediaId: string) => `/api/v1/media/Manga/${mediaId}/trackers`;

export interface TrackerLinksResponse {
  links: TrackerLink[];
  /** Trackers dont l'utilisateur a une connexion. Toujours servi par le
   *  backend (api/core/manga.py) — indispensable pour distinguer les deux cas
   *  qui donnent tous deux `links: []` : `connected: []` = l'utilisateur n'a
   *  lié aucun compte (rien à afficher) ; `connected: ['anilist']` = un
   *  compte est lié mais aucune correspondance trouvée (recherche manuelle).
   *  Un `links` non vide ne dispense jamais de le lire : c'est aussi ce champ
   *  qui dit si la connexion source d'une liaison confirmée existe encore. */
  connected: TrackerName[];
}

/** `null` quand le manga n'est pas au catalogue (204). */
export const fetchTrackerLinks = (mediaId: string): Promise<TrackerLinksResponse | null> =>
  apiClient(`${base(mediaId)}/`, { skipToast: true });

export const searchTracker = (
  mediaId: string,
  tracker: TrackerName,
  query: string,
): Promise<{ results: TrackerCandidate[] }> =>
  apiClient(`${base(mediaId)}/search/`, {
    method: 'POST',
    body: JSON.stringify({ tracker, query }),
  });

export const linkTracker = (
  mediaId: string,
  tracker: TrackerName,
  remoteId: string,
): Promise<TrackerLink> =>
  apiClient(`${base(mediaId)}/link/`, {
    method: 'POST',
    body: JSON.stringify({ tracker, remote_id: remoteId }),
  });

export const unlinkTracker = (
  mediaId: string,
  tracker: TrackerName,
): Promise<{ success: boolean }> => apiClient(`${base(mediaId)}/${tracker}/`, { method: 'DELETE' });
