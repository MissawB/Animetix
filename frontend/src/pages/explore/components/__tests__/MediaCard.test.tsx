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
  // note et année présentes dans la bande persistante ET l'overlay de survol
  expect(screen.getAllByText('8.5').length).toBeGreaterThan(0);
  expect(screen.getAllByText('2021').length).toBeGreaterThan(0);
  expect(screen.getByText('ANIME')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /fiche/i })).toHaveAttribute('href', '/media/Anime/1/');
});

it('shows the original title in the overlay when it differs from the display title', () => {
  renderCard({ id: '1', title: 'Demon Slayer', title_native: '鬼滅の刃', media_type: 'Anime' });
  expect(screen.getByText('鬼滅の刃')).toBeInTheDocument();
});

it('shows BOTH native and english titles when they differ from the display title', () => {
  renderCard({
    id: '1',
    title: 'Sousou no Frieren',
    title_native: '葬送のフリーレン',
    title_english: "Frieren: Beyond Journey's End",
    media_type: 'Anime',
    studios: ['MADHOUSE'],
  });
  expect(screen.getByText('葬送のフリーレン')).toBeInTheDocument();
  expect(screen.getByText("Frieren: Beyond Journey's End")).toBeInTheDocument();
  expect(screen.getByText('MADHOUSE')).toBeInTheDocument();
});

it('falls back to the english title and hides it when identical to the display title', () => {
  renderCard({
    id: '1',
    title: 'Berserk',
    title_native: '',
    title_english: 'Berserk',
    media_type: 'Manga',
  });
  // english identique au titre affiché -> pas de doublon
  expect(screen.getAllByText('Berserk')).toHaveLength(1);
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
