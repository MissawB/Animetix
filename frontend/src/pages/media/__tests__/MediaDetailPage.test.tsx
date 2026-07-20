import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import MediaDetailPage from '../MediaDetailPage';
import { useMediaDetail } from '../../../features/media/hooks/useMediaDetail';
import { useMediaCharacters } from '../../../features/media/hooks/useMediaCharacters';
import { useAuthStore } from '../../../store/authStore';

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
vi.mock('../../../features/media/hooks/useMediaDetail', () => ({ useMediaDetail: vi.fn() }));
vi.mock('../../../features/media/hooks/useMediaCharacters', () => ({
  useMediaCharacters: vi.fn(),
}));
vi.mock('../../../features/manga-reader/components/ChapterList', () => ({
  ChapterList: () => <div data-testid="chapter-list" />,
}));
vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const mockedUseMediaDetail = vi.mocked(useMediaDetail);
const mockedUseMediaCharacters = vi.mocked(useMediaCharacters);

const item = {
  id: '38000',
  title: 'Kimetsu no Yaiba',
  media_type: 'Anime',
  image: 'poster.jpg',
  genres: ['Action'],
  title_native: '鬼滅の刃',
  year: '2019',
  popularity: 3,
  description: 'Tanjiro devient pourfendeur de démons.',
  studios: ['ufotable'],
  seiyuu: [{ id: 1, name: 'Natsuki Hanae', sample_url: '', role: 'Tanjiro' }],
  related_items: [{ id: '40000', title: 'Saison 2', image: '' }],
};

const renderPage = (mediaType = 'Anime', itemId = '38000') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/media/${mediaType}/${itemId}/`]}>
        <Routes>
          <Route path="/media/:mediaType/:itemId/" element={<MediaDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ isAuthenticated: false });
  mockedUseMediaDetail.mockReturnValue({
    data: item,
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
  mockedUseMediaCharacters.mockReturnValue({
    data: { characters: [] },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaCharacters>);
});

it('hides the micro-tags section when micro_tags is empty', () => {
  renderPage();
  expect(screen.queryByText(/micro-tags ia/i)).toBeNull();
  expect(screen.queryByText(/analyse en cours/i)).toBeNull();
});

it('shows the micro-tags section when micro_tags has entries', () => {
  mockedUseMediaDetail.mockReturnValue({
    data: { ...item, micro_tags: ['revenge', 'sibling-bond'] },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
  renderPage();
  expect(screen.getByText(/micro-tags ia/i)).toBeInTheDocument();
  expect(screen.getByText('revenge')).toBeInTheDocument();
});

it('renders the loading skeleton while fetching', () => {
  mockedUseMediaDetail.mockReturnValue({
    data: undefined,
    isLoading: true,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
  const { container } = renderPage();
  expect(container.querySelector('.animate-pulse')).toBeTruthy();
});

it('renders the not-found state on error', () => {
  mockedUseMediaDetail.mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: true,
  } as unknown as ReturnType<typeof useMediaDetail>);
  renderPage();
  expect(screen.getByText(/œuvre introuvable/i)).toBeInTheDocument();
});

it('renders hero title, synopsis and studio', () => {
  renderPage();
  expect(screen.getByRole('heading', { level: 1, name: /kimetsu no yaiba/i })).toBeInTheDocument();
  expect(screen.getByText(/pourfendeur de démons/i)).toBeInTheDocument();
  expect(screen.getByText('ufotable')).toBeInTheDocument();
});

it('renders the seiyuu section when present and hides it when absent', () => {
  renderPage();
  expect(screen.getByText('Natsuki Hanae')).toBeInTheDocument();
  mockedUseMediaDetail.mockReturnValue({
    data: { ...item, seiyuu: [] },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
  renderPage();
  expect(screen.queryAllByText('Natsuki Hanae')).toHaveLength(1); // only the first render's copy
});

it('links related items with the capitalized media type', () => {
  renderPage();
  expect(screen.getByRole('link', { name: /saison 2/i })).toHaveAttribute(
    'href',
    '/media/Anime/40000/',
  );
});

it('shows the chapter list only for manga', () => {
  renderPage();
  expect(screen.queryByTestId('chapter-list')).toBeNull();
  mockedUseMediaDetail.mockReturnValue({
    data: { ...item, media_type: 'Manga' },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
  renderPage('Manga', '99');
  expect(screen.getByTestId('chapter-list')).toBeInTheDocument();
});

it('shows the characters section when characters exist', () => {
  mockedUseMediaCharacters.mockReturnValue({
    data: { characters: [{ id: '126071', name: 'Tanjirou Kamado', image: '' }] },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaCharacters>);
  renderPage();
  expect(screen.getByText(/personnages/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /tanjirou kamado/i })).toHaveAttribute(
    'href',
    '/media/Character/126071/',
  );
});

it('hides the characters section when empty', () => {
  renderPage();
  expect(screen.queryByText(/personnages/i)).toBeNull();
});
