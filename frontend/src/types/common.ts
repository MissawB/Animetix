export interface AppConfig {
  version: string;
  maintenance_mode: boolean;
  maintenance_message?: string | null;
  maintenance_until?: string | null;
  features: Record<string, boolean>;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface ApiResponse<T> {
  status: string;
  results: T;
  message?: string;
}

export interface SearchItem {
  id?: number | string;
  title?: string;
  title_english?: string | null;
  title_native?: string | null;
  name?: string;
  image_url?: string;
  type?: string;
  year?: number | null;
  rating?: number | null;
}

export interface PlotlyEvent {
  points: Array<{
    customdata: unknown;
    pointNumber: number;
  }>;
}
