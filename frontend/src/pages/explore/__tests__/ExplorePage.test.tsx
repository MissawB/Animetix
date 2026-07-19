import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ExplorePage from '../ExplorePage';
import { vi } from 'vitest';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApiClient = vi.mocked(apiClient);

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const renderPage = () =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ExplorePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe('ExplorePage', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('requests the versioned explore endpoint with the media type', async () => {
    mockedApiClient.mockResolvedValue({ rows: [], personalized: false });
    renderPage();
    await waitFor(() =>
      expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/explore/?media_type=Anime'),
    );
  });

  it('renders a because_you_liked row with its reason chip', async () => {
    mockedApiClient.mockResolvedValue({
      personalized: true,
      rows: [
        {
          kind: 'because_you_liked',
          title: 'Parce que tu as aimé One Piece',
          reason: 'Basé sur tes favoris et tes duels',
          seed: { id: '1', title: 'One Piece' },
          items: [{ id: '10', title: 'Neighbour', media_type: 'Anime', image: '' }],
        },
      ],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Parce que tu as aimé One Piece/i)).toBeInTheDocument();
      expect(screen.getByText(/Basé sur tes favoris/i)).toBeInTheDocument();
      expect(screen.getByText(/Neighbour/i)).toBeInTheDocument();
    });
  });

  it('shows the cold-start banner when the feed is not personalized', async () => {
    mockedApiClient.mockResolvedValue({
      personalized: false,
      rows: [
        {
          kind: 'top_rated',
          title: 'Les mieux notés',
          reason: 'Populaire',
          seed: null,
          items: [{ id: '1', title: 'Top', media_type: 'Anime', image: '' }],
        },
      ],
    });
    renderPage();
    await waitFor(() => expect(screen.getByText(/personnalise/i)).toBeInTheDocument());
  });

  it('does not render fake streaming buttons', async () => {
    mockedApiClient.mockResolvedValue({
      personalized: false,
      rows: [
        {
          kind: 'top_rated',
          title: 'Les mieux notés',
          reason: 'Populaire',
          seed: null,
          items: [{ id: '1', title: 'Top', media_type: 'Anime', image: '' }],
        },
      ],
    });
    renderPage();
    await waitFor(() => expect(screen.getByText(/Top/i)).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /commencer/i })).toBeNull();
  });

  it('shows a skeleton while the feed is loading', () => {
    let resolve: (value: unknown) => void = () => {};
    mockedApiClient.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    renderPage();
    expect(screen.getByTestId('feed-skeleton')).toBeInTheDocument();
    resolve({ rows: [], personalized: true });
  });

  it('shows an error state with a retry button on failure', async () => {
    mockedApiClient.mockRejectedValue(new Error('boom'));
    renderPage();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /réessayer/i })).toBeInTheDocument(),
    );
  });

  it('switches to results mode and filters when a query is typed', async () => {
    mockedApiClient.mockResolvedValue({
      personalized: true,
      rows: [
        {
          kind: 'top',
          title: 'Top',
          reason: '',
          seed: null,
          items: [
            { id: '1', title: 'Naruto', media_type: 'Anime' },
            { id: '2', title: 'Bleach', media_type: 'Anime' },
          ],
        },
      ],
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Top')).toBeInTheDocument());
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'naruto' } });
    await waitFor(() => expect(screen.getByText(/1 résultat/i)).toBeInTheDocument());
    expect(screen.queryByText('Bleach')).toBeNull();
  });
});
