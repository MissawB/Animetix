import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ExplorePage from '../ExplorePage';
import { vi } from 'vitest';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApiClient = vi.mocked(apiClient);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('ExplorePage', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('renders the explore page title and sections', () => {
    mockedApiClient.mockResolvedValue({ trending: [] });

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
    mockedApiClient.mockResolvedValue({ trending: [] });

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

    mockedApiClient.mockResolvedValue(mockData);

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



