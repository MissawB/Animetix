import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TachideskExplorerPage from '../TachideskExplorerPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('TachideskExplorerPage', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.restoreAllMocks();
    vi.stubGlobal('fetch', vi.fn());
  });

  const mockSources = [
    { id: '1', name: 'MangaDex', lang: 'en' },
    { id: '2', name: 'Manganato', lang: 'en' },
  ];

  const mockExtensions = [
    {
      pkgName: 'com.mangadex',
      name: 'MangaDex',
      versionName: '1.4.15',
      isInstalled: true,
      hasUpdate: false,
      lang: 'en',
      iconUrl: '/icon/mangadex.png',
      isNsfw: false,
      isObsolete: false,
    },
    {
      pkgName: 'com.manganato',
      name: 'Manganato',
      versionName: '1.3.0',
      isInstalled: true,
      hasUpdate: true,
      lang: 'en',
      iconUrl: '/icon/manganato.png',
      isNsfw: false,
      isObsolete: false,
    },
    {
      pkgName: 'com.mangafox',
      name: 'MangaFox',
      versionName: '1.2.0',
      isInstalled: false,
      hasUpdate: false,
      lang: 'en',
      iconUrl: '/icon/mangafox.png',
      isNsfw: true,
      isObsolete: true,
    },
  ];

  it('renders the explorer and defaults to the Catalogue tab', async () => {
    vi.mocked(global.fetch).mockImplementation(async (url) => {
      if (typeof url === 'string' && url.includes('/sources/')) {
        return {
          ok: true,
          json: async () => mockSources,
        } as Response;
      }
      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TachideskExplorerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Tachidesk Explorer/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Catalogue/i })).toHaveClass('bg-blue-600');
    expect(screen.getByRole('button', { name: /Extensions/i })).not.toHaveClass('bg-blue-600');

    await waitFor(() => {
      expect(screen.getByLabelText(/Source Suwayomi/i)).toBeInTheDocument();
    });
  });

  it('switches to the Extensions tab and lists extensions grouped by category', async () => {
    vi.mocked(global.fetch).mockImplementation(async (url) => {
      if (typeof url === 'string' && url.includes('/sources/')) {
        return {
          ok: true,
          json: async () => mockSources,
        } as Response;
      }
      if (typeof url === 'string' && url.includes('/extensions/')) {
        return {
          ok: true,
          json: async () => mockExtensions,
        } as Response;
      }
      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TachideskExplorerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to extensions tab
    const extensionsButton = screen.getByRole('button', { name: /Extensions/i });
    fireEvent.click(extensionsButton);

    // Wait for extensions data to render
    await waitFor(() => {
      expect(screen.getByText(/Total : 3 \/ 3 extensions/i)).toBeInTheDocument();
    });

    // Check Categories are displayed
    expect(screen.getByText(/Mises à jour disponibles/i)).toBeInTheDocument();
    expect(screen.getByText(/Extensions Installées/i)).toBeInTheDocument();
    expect(screen.getByText(/Extensions Disponibles/i)).toBeInTheDocument();

    // Check correct extensions rendered under appropriate sections
    expect(screen.getByText('MangaDex')).toBeInTheDocument();
    expect(screen.getByText('Manganato')).toBeInTheDocument();
    expect(screen.getByText('MangaFox')).toBeInTheDocument();

    // NSFW and Obsolete badges
    expect(screen.getByText('18+')).toBeInTheDocument();
    expect(screen.getByText('Obsolète')).toBeInTheDocument();
  });

  it('filters extensions using the search bar input', async () => {
    vi.mocked(global.fetch).mockImplementation(async (url) => {
      if (typeof url === 'string' && url.includes('/sources/')) {
        return {
          ok: true,
          json: async () => mockSources,
        } as Response;
      }
      if (typeof url === 'string' && url.includes('/extensions/')) {
        return {
          ok: true,
          json: async () => mockExtensions,
        } as Response;
      }
      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TachideskExplorerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /Extensions/i }));

    await waitFor(() => {
      expect(screen.getByText(/Total : 3 \/ 3 extensions/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Rechercher une extension/i);
    fireEvent.change(searchInput, { target: { value: 'Dex' } });

    // Only MangaDex matches "Dex"
    expect(screen.queryByText('MangaDex')).toBeInTheDocument();
    expect(screen.queryByText('Manganato')).not.toBeInTheDocument();
    expect(screen.queryByText('MangaFox')).not.toBeInTheDocument();
    expect(screen.getByText(/Total : 1 \/ 3 extensions/i)).toBeInTheDocument();
  });

  it('calls extension action endpoint on install, uninstall, or update clicks', async () => {
    let actionPayload: any = null;

    vi.mocked(global.fetch).mockImplementation(async (url, options) => {
      if (typeof url === 'string' && url.includes('/sources/')) {
        return {
          ok: true,
          json: async () => mockSources,
        } as Response;
      }
      if (typeof url === 'string' && url.includes('/extensions/action/')) {
        if (options && options.body) {
          actionPayload = JSON.parse(options.body as string);
        }
        return {
          ok: true,
          json: async () => [{ pkgName: 'com.mangafox', name: 'MangaFox', isInstalled: true }],
        } as Response;
      }
      if (typeof url === 'string' && url.includes('/extensions/')) {
        return {
          ok: true,
          json: async () => mockExtensions,
        } as Response;
      }
      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TachideskExplorerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /Extensions/i }));

    await waitFor(() => {
      expect(screen.getByText('MangaFox')).toBeInTheDocument();
    });

    // Find and click the install button for MangaFox (which is not installed)
    const installBtn = screen.getByTitle("Installer l'extension");
    fireEvent.click(installBtn);

    await waitFor(() => {
      expect(actionPayload).toEqual({
        ids: ['com.mangafox'],
        action: 'install',
      });
    });
  });

  it('displays an error panel when loading extensions fails', async () => {
    vi.mocked(global.fetch).mockImplementation(async (url) => {
      if (typeof url === 'string' && url.includes('/sources/')) {
        return {
          ok: true,
          json: async () => mockSources,
        } as Response;
      }
      if (typeof url === 'string' && url.includes('/extensions/')) {
        return {
          ok: false,
          status: 500,
          statusText: 'Server Error',
        } as Response;
      }
      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TachideskExplorerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /Extensions/i }));

    await waitFor(() => {
      expect(screen.getByText(/Erreur lors du chargement des extensions/i)).toBeInTheDocument();
    });

    // Close/dismiss the error
    const dismissBtn = screen.getByRole('button', { name: /×/i });
    fireEvent.click(dismissBtn);

    expect(screen.queryByText(/Erreur lors du chargement des extensions/i)).not.toBeInTheDocument();
  });
});
