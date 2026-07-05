import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { OfflineMangaPage } from '../OfflineMangaPage';
import * as lib from '../../../features/manga-reader/offline/offlineLibrary';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('OfflineMangaPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockNavigate.mockClear();
    
    // Mock navigator.storage.estimate
    if (global.navigator) {
      Object.defineProperty(global.navigator, 'storage', {
        value: {
          estimate: vi.fn().mockResolvedValue({ usage: 2048, quota: 10000 }),
        },
        configurable: true,
      });
    }
  });

  it('renders loading state initially and then empty state if no downloads exist', async () => {
    vi.spyOn(lib, 'listDownloads').mockResolvedValue([]);

    render(
      <MemoryRouter>
        <OfflineMangaPage />
      </MemoryRouter>
    );

    // Shows loading indicator first
    expect(screen.getByText(/Initialisation du système.../i)).toBeInTheDocument();

    // Waits for the data load and renders the empty state
    await waitFor(() => {
      expect(screen.queryByText(/Initialisation du système.../i)).not.toBeInTheDocument();
      expect(screen.getByText('Aucun chapitre téléchargé')).toBeInTheDocument();
      expect(screen.getByText('Parcourir les mangas')).toBeInTheDocument();
    });
  });

  it('renders downloaded chapters when they are present', async () => {
    const mockChapters: lib.DownloadedChapter[] = [
      {
        mediaId: 'manga-1',
        mediaTitle: 'Chainsaw Man',
        chapterNumber: 15,
        chapterTitle: 'Ch 15 Title',
        pageCount: 19,
        pageKeys: ['img:manga-1:15:1', 'img:manga-1:15:2'],
        downloadedAt: Date.now() - 3600000, // 1 hour ago
        totalBytes: 5242880, // 5 MB
      },
    ];

    vi.spyOn(lib, 'listDownloads').mockResolvedValue(mockChapters);

    render(
      <MemoryRouter>
        <OfflineMangaPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Chainsaw Man')).toBeInTheDocument();
      expect(screen.getByText(/Chapter 15/i)).toBeInTheDocument();
      expect(screen.getByText(/: Ch 15 Title/i)).toBeInTheDocument();
      expect(screen.getByText('Lire')).toBeInTheDocument();
      expect(screen.getByText('Supprimer')).toBeInTheDocument();
    });
  });

  it('navigates to the reader page when read button is clicked', async () => {
    const mockChapters: lib.DownloadedChapter[] = [
      {
        mediaId: 'manga-1',
        mediaTitle: 'Chainsaw Man',
        chapterNumber: 15,
        chapterTitle: 'Ch 15 Title',
        pageCount: 19,
        pageKeys: ['img:manga-1:15:1'],
        downloadedAt: Date.now(),
        totalBytes: 1024,
      },
    ];

    vi.spyOn(lib, 'listDownloads').mockResolvedValue(mockChapters);

    render(
      <MemoryRouter>
        <OfflineMangaPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const readBtn = screen.getByText('Lire');
      fireEvent.click(readBtn);
      expect(mockNavigate).toHaveBeenCalledWith('/media/manga/manga-1/15/');
    });
  });

  it('deletes a chapter and refreshes list when delete button is clicked', async () => {
    const mockChapters: lib.DownloadedChapter[] = [
      {
        mediaId: 'manga-1',
        mediaTitle: 'Chainsaw Man',
        chapterNumber: 15,
        chapterTitle: 'Ch 15 Title',
        pageCount: 19,
        pageKeys: ['img:manga-1:15:1'],
        downloadedAt: Date.now(),
        totalBytes: 1024,
      },
    ];

    vi.spyOn(lib, 'listDownloads')
      .mockResolvedValueOnce(mockChapters) // first load
      .mockResolvedValueOnce([]); // second load after deletion

    const deleteSpy = vi.spyOn(lib, 'deleteChapter').mockResolvedValue();

    render(
      <MemoryRouter>
        <OfflineMangaPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Chainsaw Man')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByText('Supprimer');
    fireEvent.click(deleteBtn);

    expect(deleteSpy).toHaveBeenCalledWith('manga-1', 15);

    await waitFor(() => {
      expect(screen.queryByText('Chainsaw Man')).not.toBeInTheDocument();
      expect(screen.getByText('Aucun chapitre téléchargé')).toBeInTheDocument();
    });
  });

  it('deletes all chapters when clear all button is clicked and confirmed', async () => {
    const mockChapters: lib.DownloadedChapter[] = [
      {
        mediaId: 'manga-1',
        mediaTitle: 'Manga 1',
        chapterNumber: 1,
        chapterTitle: '',
        pageCount: 10,
        pageKeys: [],
        downloadedAt: Date.now(),
        totalBytes: 1000,
      },
      {
        mediaId: 'manga-2',
        mediaTitle: 'Manga 2',
        chapterNumber: 2,
        chapterTitle: '',
        pageCount: 10,
        pageKeys: [],
        downloadedAt: Date.now(),
        totalBytes: 2000,
      },
    ];

    vi.spyOn(lib, 'listDownloads')
      .mockResolvedValueOnce(mockChapters)
      .mockResolvedValueOnce([]);

    const deleteSpy = vi.spyOn(lib, 'deleteChapter').mockResolvedValue();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <MemoryRouter>
        <OfflineMangaPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Manga 1')).toBeInTheDocument();
    });

    const clearAllBtn = screen.getByText('Tout supprimer');
    fireEvent.click(clearAllBtn);

    expect(confirmSpy).toHaveBeenCalled();

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith('manga-1', 1);
      expect(deleteSpy).toHaveBeenCalledWith('manga-2', 2);
      expect(screen.queryByText('Manga 1')).not.toBeInTheDocument();
      expect(screen.getByText('Aucun chapitre téléchargé')).toBeInTheDocument();
    });
  });
});
