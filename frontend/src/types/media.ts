export interface MediaItem {
  id: string;
  title: string;
  media_type: 'Anime' | 'Manga' | 'Movie' | 'Game' | 'Actor';
  image?: string;
  description?: string;
  popularity?: number;
}

export interface VideoSegment {
  id: string;
  video_id: string | number;
  start: number;
  end: number;
  start_time: number;
  summary: string;
  description?: string;
  media_title?: string;
  type?: 'emotion' | 'action' | 'dialogue';
}

export interface Seiyuu {
  id: number;
  name: string;
  sample_url: string;
  image?: string;
  role?: string;
}

export interface VoiceProfile {
  id: number;
  name: string;
  language: 'japanese' | 'french' | 'other';
  origin: 'dataset' | 'youtube' | 'upload';
  definition?: string;
  roles?: string;
  impact?: string;
  origin_detail?: string;
  sample_url: string;
  created_at: string;
  updated_at: string;
}

export interface StreamingPlatform {
  platform: string;
  has_vf?: boolean;
  has_vostfr?: boolean;
  status?: string;
}

export interface Appearance {
  id: string;
  title: string;
  image?: string;
}

export interface RelatedItem {
  id: string;
  title: string;
  image?: string;
}

export interface NotableWork {
  id: string;
  title: string;
  image?: string;
  type?: string;
  role?: string;
}

export interface MediaDetail extends MediaItem {
  genres?: string[];
  title_english?: string;
  year?: string;
  rating?: number;
  studios?: string[];
  author?: string;
  micro_tags?: string[];
  related_items?: RelatedItem[];
  metadata?: Record<string, unknown>;
  title_native?: string;
  popularity?: number;
  seiyuu?: Seiyuu[];
  streaming_platforms?: StreamingPlatform[];
}

export interface FavoriteManga {
  id: number;
  manga: MediaDetail;
  status: 'reading' | 'completed' | 'plan_to_read';
  last_read_chapter: number;
  unread_chapters_count: number;
  created_at: string;
  updated_at: string;
}
