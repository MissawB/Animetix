import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import MediaDetailPage from '../MediaDetailPage';
import { useMediaDetail } from '../../../features/media/hooks/useMediaDetail';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));
vi.mock('../../../features/media/hooks/useMediaDetail', () => ({ useMediaDetail: vi.fn() }));
vi.mock('../../../features/manga-reader/components/ChapterList', () => ({
  ChapterList: () => <div data-testid="chapter-list" />,
}));

const mockedUseMediaDetail = vi.mocked(useMediaDetail);

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

const renderPage = (mediaType = 'Anime', itemId = '38000') =>
  render(
    <MemoryRouter initialEntries={[`/media/${mediaType}/${itemId}/`]}>
      <Routes>
        <Route path="/media/:mediaType/:itemId/" element={<MediaDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

beforeEach(() => {
  vi.clearAllMocks();
  mockedUseMediaDetail.mockReturnValue({
    data: item,
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useMediaDetail>);
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
