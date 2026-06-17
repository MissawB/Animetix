import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ExplorePage from '../ExplorePage';
import { vi } from 'vitest';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

// Mock fetch
global.fetch = vi.fn();

describe('ExplorePage', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('renders the explore page title and sections', () => {
    vi.mocked(global.fetch).mockResolvedValue({
      json: async () => ({ trending: [] })
    } as unknown as Response);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExplorePage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Tendances Actuelles/i)).toBeInTheDocument();
  });

  it('renders media type filters', () => {
    vi.mocked(global.fetch).mockResolvedValue({
      json: async () => ({ trending: [] })
    } as unknown as Response);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExplorePage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Animes/i)).toBeInTheDocument();
    expect(screen.getByText(/Mangas/i)).toBeInTheDocument();
  });

  it('renders recommendations row when data is present', async () => {
    const mockData = {
      recommendations: [
        { id: 1, title: 'Recommended Item 1', image: '' }
      ],
      trending: []
    };

    vi.mocked(global.fetch).mockResolvedValue({
      json: async () => mockData
    } as unknown as Response);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExplorePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Choisi pour vous/i)).toBeInTheDocument();
      expect(screen.getByText(/IA : SUGGESTION/i)).toBeInTheDocument();
      expect(screen.getByText(/Recommended Item 1/i)).toBeInTheDocument();
    });
  });
});



