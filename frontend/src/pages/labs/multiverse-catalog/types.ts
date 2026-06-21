// ─── Types ───────────────────────────────────────────────────────────
export interface UniverseCharacter {
  name: string;
  role: string;
  power_level: number;
}

export interface Universe {
  id: string;
  name: string;
  description: string;
  cosmology: string;
  genre: string;
  is_synthetic: boolean;
  character_count: number;
  characters: UniverseCharacter[];
  created_at: string | null;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface GenreOption {
  name: string;
  count: number;
}

export interface CatalogResponse {
  results: Universe[];
  pagination: Pagination;
  filters: {
    search: string;
    genre: string;
    sort: string;
  };
  available_genres: GenreOption[];
}

export type ViewMode = 'grid' | 'list';

export interface SortOption {
  value: string;
  label: string;
}
