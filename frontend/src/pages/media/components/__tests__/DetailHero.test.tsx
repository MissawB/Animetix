import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { DetailHero } from '../DetailHero';
import { useAuthStore } from '../../../../store/authStore';
import type { MediaDetail } from '../../../../types';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
  // authStore.ts (imported for real below so the test can call
  // useAuthStore.setState) pulls in src/i18n/config.ts, which calls
  // i18n.use(initReactI18next) at module load. Without this export the
  // per-file mock above shadows the global setup.ts mock and that call
  // throws on import.
  initReactI18next: { type: '3rdParty', init: () => {} },
}));
vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

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

const renderHero = (item: MediaDetail, mediaType = 'Anime', itemId = '38000') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DetailHero item={item} mediaType={mediaType} itemId={itemId} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ isAuthenticated: false });
});

it('renders title, genres, meta and native/english sub-line', () => {
  renderHero(baseItem);
  expect(screen.getByRole('heading', { level: 1, name: /kimetsu no yaiba/i })).toBeInTheDocument();
  expect(screen.getByText('Action')).toBeInTheDocument();
  expect(screen.getByText('2019')).toBeInTheDocument();
  expect(screen.getByTitle('Popularité')).toHaveTextContent('3');
  expect(screen.getByText('鬼滅の刃 · Demon Slayer')).toBeInTheDocument();
});

it('hides the sub-line when native and english titles are absent', () => {
  renderHero({ ...baseItem, title_english: undefined, title_native: undefined } as MediaDetail);
  expect(screen.queryByText(/·/)).toBeNull();
});

it('shows LIRE LE MANGA link for manga and no watch button', () => {
  renderHero({ ...baseItem, media_type: 'Manga' } as MediaDetail, 'Manga', '99');
  expect(screen.getByRole('link', { name: /lire le manga/i })).toHaveAttribute(
    'href',
    '/media/manga/99/1/',
  );
  expect(screen.queryByText(/où regarder/i)).toBeNull();
});

it('shows a JustWatch watch link for anime without platform data', () => {
  renderHero(baseItem);
  expect(screen.getByRole('link', { name: /où regarder/i })).toHaveAttribute(
    'href',
    expect.stringContaining('justwatch.com'),
  );
});

it('shows the library button only for manga', () => {
  const { unmount } = renderHero(
    { ...baseItem, media_type: 'Manga' } as MediaDetail,
    'Manga',
    '99',
  );
  expect(screen.getByRole('button', { name: /bibliothèque/i })).toBeInTheDocument();
  unmount();
  renderHero(baseItem);
  expect(screen.queryByRole('button', { name: /bibliothèque/i })).toBeNull();
});

it('shows the share button', () => {
  renderHero(baseItem);
  expect(screen.getByRole('button', { name: /partager/i })).toBeInTheDocument();
});

it('omits the popularity chip when popularity is missing', () => {
  renderHero({ ...baseItem, popularity: undefined } as unknown as MediaDetail);
  expect(screen.queryByTitle('Popularité')).toBeNull();
});

it('renders hero background image', () => {
  renderHero(baseItem);
  const bgImage = screen.getByRole('img', { hidden: true });
  expect(bgImage).toHaveAttribute('src', baseItem.image);
});
