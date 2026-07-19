import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { MediaCard } from '../MediaCard';
import { apiClient } from '../../../../utils/apiClient';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));
const mockedApiClient = vi.mocked(apiClient);

const renderCard = (item: Parameters<typeof MediaCard>[0]['item']) =>
  render(
    <MemoryRouter>
      <MediaCard item={item} />
    </MemoryRouter>,
  );

beforeEach(() => vi.clearAllMocks());

it('shows rating, year and a type badge when present', () => {
  renderCard({ id: '1', title: 'Neon', media_type: 'Anime', rating: 8.5, year: 2021 });
  expect(screen.getByText('8.5')).toBeInTheDocument();
  expect(screen.getByText('2021')).toBeInTheDocument();
  expect(screen.getByText('ANIME')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /fiche/i })).toBeInTheDocument();
});

it('omits the rating when absent', () => {
  renderCard({ id: '1', title: 'Neon', media_type: 'Anime', year: 2021 });
  expect(screen.queryByText(/^\d+\.\d$/)).toBeNull();
});

it('does not render a favorite button for a non-manga item', () => {
  renderCard({ id: '10', title: 'Neon', media_type: 'Anime' });
  expect(screen.queryByRole('button', { name: /favoris/i })).toBeNull();
});

it('adds a manga item to favorites with plan_to_read', async () => {
  mockedApiClient.mockResolvedValue({});
  renderCard({ id: '11', title: 'Berserk', media_type: 'Manga' });
  fireEvent.click(screen.getByRole('button', { name: /favoris/i }));
  await waitFor(() =>
    expect(mockedApiClient).toHaveBeenCalledWith(
      '/api/v1/media/Manga/11/favorite/',
      expect.objectContaining({ body: JSON.stringify({ status: 'plan_to_read' }) }),
    ),
  );
});
