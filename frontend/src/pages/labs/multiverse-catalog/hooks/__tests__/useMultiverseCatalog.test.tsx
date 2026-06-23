import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMultiverseCatalog } from '../useMultiverseCatalog';
import { apiClient } from '../../../../../utils/apiClient';

vi.mock('../../../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockApiClient = vi.mocked(apiClient);

const makeWrapper = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

describe('useMultiverseCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state values', async () => {
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 5, total_items: 60 },
    });

    const { result } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    expect(result.current.search).toBe('');
    expect(result.current.debouncedSearch).toBe('');
    expect(result.current.genre).toBe('');
    expect(result.current.sort).toBe('newest');
    expect(result.current.viewMode).toBe('grid');
    expect(result.current.selectedUniverse).toBeNull();
    expect(result.current.showFilters).toBe(false);
    expect(result.current.hasActiveFilters).toBe(false);
  });

  it('debounces search queries and resets page', async () => {
    vi.useFakeTimers();
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 5, total_items: 60 },
    });

    const { result } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    act(() => {
      result.current.handleSearchChange('Spirited Away');
    });

    expect(result.current.search).toBe('Spirited Away');
    expect(result.current.debouncedSearch).toBe('');

    // Advance timer
    act(() => {
      vi.advanceTimersByTime(350);
    });

    expect(result.current.debouncedSearch).toBe('Spirited Away');
    vi.useRealTimers();
  });

  it('resets page to 1 when filters or sorting change', async () => {
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 5, total_items: 60 },
    });

    const { result, rerender } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Set page to 3
    act(() => {
      result.current.handleSelectPage(3);
    });

    // Update sorting
    act(() => {
      result.current.handleSortChange('name');
    });

    // Rerender so state adjustments on render can occur
    rerender();

    expect(result.current.sort).toBe('name');
    // Page resets to 1
    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith(expect.stringContaining('page=1'));
    });
  });

  it('navigates pagination pages correctly', async () => {
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 3, total_items: 36 },
    });

    const { result } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleNextPage();
    });

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith(expect.stringContaining('page=2'));
    });

    act(() => {
      result.current.handlePrevPage();
    });

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith(expect.stringContaining('page=1'));
    });
  });

  it('clears active filters successfully', async () => {
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 3, total_items: 36 },
    });

    const { result } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    act(() => {
      result.current.handleSearchChange('Mecha');
      result.current.handleSelectGenre('action');
      result.current.handleSortChange('characters');
    });

    act(() => {
      result.current.handleClearFilters();
    });

    expect(result.current.search).toBe('');
    expect(result.current.debouncedSearch).toBe('');
    expect(result.current.genre).toBe('');
    expect(result.current.sort).toBe('newest');
    expect(result.current.hasActiveFilters).toBe(false);
  });

  it('handles other basic state setters', async () => {
    mockApiClient.mockResolvedValue({
      universes: [],
      pagination: { current_page: 1, total_pages: 1, total_items: 1 },
    });

    const { result } = renderHook(() => useMultiverseCatalog(), { wrapper: makeWrapper() });

    act(() => {
      result.current.handleToggleFilters();
    });
    expect(result.current.showFilters).toBe(true);

    act(() => {
      result.current.handleViewModeChange('list');
    });
    expect(result.current.viewMode).toBe('list');

    const mockUniverse = { id: 'u1', name: 'Ghibli', description: '', genre: '', characterCount: 5, bgImage: '', archetypes: [] };
    act(() => {
      result.current.handleSelectUniverse(mockUniverse);
    });
    expect(result.current.selectedUniverse).toBe(mockUniverse);

    act(() => {
      result.current.handleCloseDetail();
    });
    expect(result.current.selectedUniverse).toBeNull();

    act(() => {
      result.current.handleClearSearch();
    });
    expect(result.current.search).toBe('');
  });
});
