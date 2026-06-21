import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../../utils/apiClient';
import type { CatalogResponse, SortOption, Universe, ViewMode } from '../types';

const sortOptions: SortOption[] = [
  { value: 'newest', label: 'Plus récents' },
  { value: 'name', label: 'Alphabétique' },
  { value: 'characters', label: 'Plus peuplés' },
];

export const useMultiverseCatalog = () => {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [genre, setGenre] = useState('');
  const [sort, setSort] = useState('newest');
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedUniverse, setSelectedUniverse] = useState<Universe | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to first page on search
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset page on filter change. Done during render (React's "adjusting
  // state when a value changes" pattern) instead of in an effect.
  const [prevFilters, setPrevFilters] = useState({ genre, sort });
  if (prevFilters.genre !== genre || prevFilters.sort !== sort) {
    setPrevFilters({ genre, sort });
    setPage(1);
  }

  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set('search', debouncedSearch);
    if (genre) params.set('genre', genre);
    params.set('sort', sort);
    params.set('page', String(page));
    params.set('page_size', '12');
    return params.toString();
  }, [debouncedSearch, genre, sort, page]);

  const { data, isLoading, isFetching } = useQuery<CatalogResponse>({
    queryKey: ['multiverse-catalog', queryParams],
    queryFn: () => apiClient(`/api/v1/multiverse/catalog/?${queryParams}`),
    placeholderData: (prev) => prev,
  });

  const handleClearFilters = useCallback(() => {
    setSearch('');
    setDebouncedSearch('');
    setGenre('');
    setSort('newest');
    setPage(1);
  }, []);

  const hasActiveFilters = debouncedSearch || genre || sort !== 'newest';

  // ── Stable handlers for memoized children ──────────────────────────
  const handleSearchChange = useCallback((value: string) => setSearch(value), []);
  const handleClearSearch = useCallback(() => {
    setSearch('');
    setDebouncedSearch('');
  }, []);
  const handleSortChange = useCallback((value: string) => setSort(value), []);
  const handleToggleFilters = useCallback(() => setShowFilters((prev) => !prev), []);
  const handleViewModeChange = useCallback((mode: ViewMode) => setViewMode(mode), []);
  const handleSelectGenre = useCallback((value: string) => setGenre(value), []);
  const handleSelectUniverse = useCallback((u: Universe) => setSelectedUniverse(u), []);
  const handleCloseDetail = useCallback(() => setSelectedUniverse(null), []);
  const handlePrevPage = useCallback(() => setPage((p) => Math.max(1, p - 1)), []);
  const handleNextPage = useCallback(() => {
    setPage((p) => Math.min(data?.pagination.total_pages ?? p, p + 1));
  }, [data?.pagination.total_pages]);
  const handleSelectPage = useCallback((value: number) => setPage(value), []);

  return {
    // state
    search,
    debouncedSearch,
    genre,
    sort,
    viewMode,
    selectedUniverse,
    showFilters,
    // query
    data,
    isLoading,
    isFetching,
    // derived / static
    sortOptions,
    hasActiveFilters,
    // handlers
    handleClearFilters,
    handleSearchChange,
    handleClearSearch,
    handleSortChange,
    handleToggleFilters,
    handleViewModeChange,
    handleSelectGenre,
    handleSelectUniverse,
    handleCloseDetail,
    handlePrevPage,
    handleNextPage,
    handleSelectPage,
  };
};
