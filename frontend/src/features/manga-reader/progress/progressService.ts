import { apiClient } from '../../../utils/apiClient';

export interface ChapterProgress {
  number: number;
  is_read: boolean;
  last_page_read: number;
  page_count: number;
}

export interface MangaProgress {
  chapters: ChapterProgress[];
  resume: { chapter_number: number; last_page_read: number } | null;
  read_count: number;
  total_count: number;
}

const base = (mediaId: string) => `/api/v1/media/Manga/${mediaId}`;

/** `null` quand le manga n'est pas dans le catalogue (204) : rien n'a été lu. */
export const fetchMangaProgress = (mediaId: string): Promise<MangaProgress | null> =>
  apiClient(`${base(mediaId)}/progress/`, { skipToast: true });

export const putChapterProgress = (
  mediaId: string,
  chapterNumber: number | string,
  body: { last_page_read: number; is_read: boolean },
) =>
  apiClient(`${base(mediaId)}/chapters/${chapterNumber}/progress/`, {
    method: 'PUT',
    body: JSON.stringify(body),
    skipToast: true,
  });

export const markChaptersRead = (mediaId: string, chapterNumbers: number[], isRead: boolean) =>
  apiClient(`${base(mediaId)}/progress/mark-read/`, {
    method: 'POST',
    body: JSON.stringify({ chapter_numbers: chapterNumbers, is_read: isRead }),
  });
