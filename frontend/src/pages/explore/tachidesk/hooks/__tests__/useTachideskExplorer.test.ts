import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTachideskExplorer } from '../useTachideskExplorer';
import { apiClient } from '../../../../../utils/apiClient';

vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}));

vi.mock('../../../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockApiClient = vi.mocked(apiClient);

const mockSources = [
  { id: 'src-1', name: 'Source 1', lang: 'fr', iconUrl: '', supportsLatest: true, isConfigured: true },
  { id: 'src-2', name: 'Source 2', lang: 'en', iconUrl: '', supportsLatest: true, isConfigured: true },
];

const mockMangas = [
  { id: 'manga-1', title: 'One Piece', thumbnailUrl: '', url: '', status: 'ongoing', artist: '', author: '', description: '', genre: [], inLibrary: false }
];

const mockChapters = [
  { id: 'chap-1', name: 'Chapter 1', chapterNumber: 1, read: false, scanlator: '', dateUpload: '' }
];

describe('useTachideskExplorer', () => {
  beforeEach(() => {
    mockApiClient.mockReset();
    // Default mock implementation to avoid unhandled promise rejections
    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/extensions/')) return [];
      if (url.includes('/search/')) return mockMangas;
      if (url.includes('/favorite/')) return { is_favorite: false, status: null };
      if (url.includes('/chapters/')) return mockChapters;
      return [];
    });
  });

  it('initializes with default states', async () => {
    mockApiClient.mockResolvedValue([]);
    const { result } = renderHook(() => useTachideskExplorer());

    expect(result.current.activeTab).toBe('catalog');
    expect(result.current.sources).toEqual([]);
    expect(result.current.selectedSource).toBe('');
    expect(result.current.searchQuery).toBe('');
    expect(result.current.mangas).toEqual([]);
    expect(result.current.selectedManga).toBeNull();
    expect(result.current.chapters).toEqual([]);
    expect(result.current.extensions).toEqual([]);
    expect(result.current.loadingSources).toBe(false); // Starts as false per implementation
  });

  it('fetches sources on mount and selects the first one', async () => {
    const { result } = renderHook(() => useTachideskExplorer());

    await waitFor(() => {
      expect(result.current.sources).toEqual(mockSources);
    });

    expect(result.current.selectedSource).toBe('src-1');
    expect(mockApiClient).toHaveBeenCalledWith('/api/v1/explore/suwayomi/sources/', { skipToast: true });
  });

  it('handles fetch sources failure', async () => {
    mockApiClient.mockRejectedValue(new Error('Fetch failed'));

    const { result } = renderHook(() => useTachideskExplorer());

    await waitFor(() => {
      expect(result.current.error).toBe('Impossible de charger les sources Suwayomi');
    });
  });

  it('fetches extensions when switching to extensions tab', async () => {
    const { result } = renderHook(() => useTachideskExplorer());

    act(() => {
      result.current.setActiveTab('extensions');
    });

    expect(result.current.activeTab).toBe('extensions');
    
    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith('/api/v1/explore/suwayomi/extensions/', { skipToast: true });
    });
  });

  it('performs catalog search successfully', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    
    await waitFor(() => {
      expect(result.current.sources).toEqual(mockSources);
    });

    act(() => {
      result.current.setSearchQuery('One Piece');
    });

    await act(async () => {
      await result.current.handleSearch();
    });

    expect(result.current.mangas).toEqual(mockMangas);
    expect(mockApiClient).toHaveBeenCalledWith(
      '/api/v1/explore/suwayomi/search/?source_id=src-1&q=One%20Piece',
      { skipToast: true }
    );
  });

  it('selects a manga and loads details/chapters successfully', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    await waitFor(() => expect(result.current.sources).toEqual(mockSources));

    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/favorite/')) return { is_favorite: true, status: 'reading' };
      if (url.includes('/chapters/')) return mockChapters;
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/search/')) return mockMangas;
      return [];
    });

    await act(async () => {
      await result.current.selectManga(mockMangas[0]);
    });

    expect(result.current.selectedManga).toBe(mockMangas[0]);
    expect(result.current.isFavorited).toBe(true);
    expect(result.current.favoriteStatus).toBe('reading');
    expect(result.current.chapters).toEqual(mockChapters);
  });

  it('selects a manga, fails to load chapters, triggers import, and retries chapter load', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    await waitFor(() => expect(result.current.sources).toEqual(mockSources));

    let chaptersCalled = 0;
    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/favorite/')) return { is_favorite: false, status: null };
      if (url.includes('/chapters/')) {
        chaptersCalled++;
        if (chaptersCalled === 1) throw new Error('Not imported yet');
        return mockChapters;
      }
      if (url.includes('/import/')) return {};
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/search/')) return mockMangas;
      return [];
    });

    await act(async () => {
      await result.current.selectManga(mockMangas[0]);
    });

    expect(result.current.chapters).toEqual(mockChapters);
    expect(mockApiClient).toHaveBeenCalledWith('/api/v1/explore/suwayomi/import/', {
      method: 'POST',
      body: JSON.stringify({ source_id: 'src-1', suwayomi_manga_id: 'manga-1' }),
      skipToast: true,
    });
  });

  it('toggles favorite status successfully', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    await waitFor(() => expect(result.current.sources).toEqual(mockSources));

    await act(async () => {
      await result.current.selectManga(mockMangas[0]);
    });

    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/favorite/')) {
        return { is_favorite: true, status: 'reading' };
      }
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/search/')) return mockMangas;
      return [];
    });

    await act(async () => {
      await result.current.toggleFavorite();
    });

    expect(result.current.isFavorited).toBe(true);
    expect(result.current.favoriteStatus).toBe('reading');
  });

  it('updates favorite status with specific value successfully', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    await waitFor(() => expect(result.current.sources).toEqual(mockSources));

    await act(async () => {
      await result.current.selectManga(mockMangas[0]);
    });

    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/favorite/')) {
        return { is_favorite: true, status: 'completed' };
      }
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/search/')) return mockMangas;
      return [];
    });

    await act(async () => {
      await result.current.updateFavoriteStatus('completed');
    });

    expect(result.current.isFavorited).toBe(true);
    expect(result.current.favoriteStatus).toBe('completed');
  });

  it('triggers extension actions and refreshes extension/source list', async () => {
    const { result } = renderHook(() => useTachideskExplorer());
    await waitFor(() => expect(result.current.sources).toEqual(mockSources));

    mockApiClient.mockImplementation(async (url) => {
      if (url.includes('/extensions/action/')) return {};
      if (url.includes('/extensions/')) return [];
      if (url.includes('/sources/')) return mockSources;
      if (url.includes('/search/')) return mockMangas;
      return [];
    });

    await act(async () => {
      await result.current.handleExtensionAction('pkg.name', 'install');
    });

    expect(result.current.error).toBeNull();
  });

  it('computes correct proxied image URL', async () => {
    const { result } = renderHook(() => useTachideskExplorer());

    expect(result.current.getProxiedImageUrl('')).toBe('https://via.placeholder.com/300x450');
    expect(result.current.getProxiedImageUrl('/api/v1/test')).toBe('/api/v1/test');
    expect(result.current.getProxiedImageUrl('https://example.com/cover.jpg')).toContain('/api/v1/media/Manga/suwayomi-image/?page_url=');
  });
});
