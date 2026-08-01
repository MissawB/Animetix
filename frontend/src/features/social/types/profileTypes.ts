import type { components } from '../../../types/api';
import type { TrackerConnection } from '../../../types';

export type ApiAchievement = components['schemas']['Achievement'];
export type ApiCreativeFusion = components['schemas']['CreativeFusion'];
export type { TrackerConnection };

/** Une liaison manga <-> tracker, telle que renvoyée par
 *  `GET /api/v1/profile/trackers/links/` (toutes les œuvres, tous trackers
 *  confondus). Voir `TrackerLinkListView` (backend/api/animetix/api/core/manga.py). */
export interface TrackerLinkSummary {
  tracker: 'myanimelist' | 'anilist';
  manga_id: string;
  manga_title: string;
  remote_id: string;
  remote_title: string;
  remote_progress: number | null;
  status: 'suggested' | 'confirmed';
}
