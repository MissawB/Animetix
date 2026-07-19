import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { DetailHero } from '../DetailHero';
import type { MediaDetail } from '../../../../types';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

const baseItem = {
  id: '38000',
  title: 'Kimetsu no Yaiba',
  media_type: 'Anime',
  image: 'poster.jpg',
  genres: ['Action', 'Drama'],
  title_english: 'Demon Slayer',
  title_native: '鬼滅の刃',
  year: '2019',
  popularity: 3,
} as unknown as MediaDetail;

const renderHero = (item: MediaDetail, mediaType = 'Anime', itemId = '38000') =>
  render(
    <MemoryRouter>
      <DetailHero item={item} mediaType={mediaType} itemId={itemId} />
    </MemoryRouter>,
  );

it('renders title, genres, meta and native/english sub-line', () => {
  renderHero(baseItem);
  expect(screen.getByRole('heading', { level: 1, name: /kimetsu no yaiba/i })).toBeInTheDocument();
  expect(screen.getByText('Action')).toBeInTheDocument();
  expect(screen.getByText('2019')).toBeInTheDocument();
  expect(screen.getByText('#3')).toBeInTheDocument();
  expect(screen.getByText('鬼滅の刃 · Demon Slayer')).toBeInTheDocument();
});

it('hides the sub-line when native and english titles are absent', () => {
  renderHero({ ...baseItem, title_english: undefined, title_native: undefined } as MediaDetail);
  expect(screen.queryByText(/·/)).toBeNull();
});

it('shows VOIR for anime and LIRE LE MANGA link for manga', () => {
  const { unmount } = renderHero(baseItem);
  expect(screen.getByRole('button', { name: /voir/i })).toBeInTheDocument();
  unmount();
  renderHero({ ...baseItem, media_type: 'Manga' } as MediaDetail, 'Manga', '99');
  expect(screen.getByRole('link', { name: /lire le manga/i })).toHaveAttribute(
    'href',
    '/media/manga/99/1/',
  );
});

it('renders N/A for missing popularity', () => {
  renderHero({ ...baseItem, popularity: undefined } as unknown as MediaDetail);
  expect(screen.getByText('#N/A')).toBeInTheDocument();
});

it('renders hero background image', () => {
  renderHero(baseItem);
  const bgImage = screen.getByRole('img', { hidden: true });
  expect(bgImage).toHaveAttribute('src', baseItem.image);
});

it('renders action buttons as decorative (no handlers)', () => {
  renderHero(baseItem);
  expect(screen.getByRole('button', { name: /ajouter/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /favoris/i })).toBeInTheDocument();
});

it('renders share button', () => {
  renderHero(baseItem);
  expect(screen.getByRole('button', { name: /partager/i })).toBeInTheDocument();
});
