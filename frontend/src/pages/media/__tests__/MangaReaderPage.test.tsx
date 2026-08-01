import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MangaReaderPage from '../MangaReaderPage';
import { useReaderStore } from '../../../features/manga-reader/stores/useReaderStore';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
}));

const mockApiClient = vi.fn();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: (...args: unknown[]) => mockApiClient(...args),
}));

// The real store-driven reader renders <img> per page; irrelevant here and
// noisy under jsdom.
vi.mock('../../../features/manga-reader', () => ({
  MangaReader: () => <div data-testid="reader" />,
}));

// Pages come from Suwayomi/IndexedDB, not from the progress API: mocked so the
// test controls *when* they land relative to the progress response.
const mockPages = vi.fn();
vi.mock('../../../features/manga-reader/offline/useChapterPages', () => ({
  useChapterPages: (...args: unknown[]) => mockPages(...args),
}));

// Avoids pulling Firebase in; the page only reads these two flags.
let authState = { isAuthenticated: true, isLoading: false };
vi.mock('../../../store/authStore', () => ({
  useAuthStore: (selector: (state: typeof authState) => unknown) => selector(authState),
}));

const navigateSpy = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateSpy };
});

const PAGES = Array.from({ length: 83 }, (_, index) => ({ url: `p${index}`, index }));

/** Chapter 5 of m1 is finished: read, stopped on the last page. */
const FINISHED_CHAPTER_PROGRESS = {
  chapters: [{ number: 5, is_read: true, last_page_read: 82, page_count: 83 }],
  resume: null,
  read_count: 1,
  total_count: 1,
};

const progressWrites = () =>
  mockApiClient.mock.calls.filter(
    ([url, options]) =>
      typeof url === 'string' &&
      url.includes('/progress/') &&
      (options as { method?: string } | undefined)?.method === 'PUT',
  );

const renderReader = () =>
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={['/media/manga/m1/5/']}>
        <Routes>
          <Route path="/media/manga/:mediaId/:chapterId/" element={<MangaReaderPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

beforeEach(() => {
  vi.clearAllMocks();
  authState = { isAuthenticated: true, isLoading: false };
  useReaderStore.setState({ pages: [], currentPageIndex: 0 });
  mockPages.mockReturnValue({ pages: PAGES, source: 'network' });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('MangaReaderPage — reading progress wiring', () => {
  // THE regression this suite exists for: reopening a finished chapter used to
  // erase it. Pages resolve before /progress/ (Suwayomi answers before
  // Django), the writer armed `{last_page_read: 0, is_read: false}` on mount,
  // and the server read that payload as a deliberate reset — badges back to
  // grey, read_count down, and the "Resume" banner pointing at a chapter the
  // user had already finished.
  it('emits no write when simply opening an already-read chapter', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let resolveProgress: (value: unknown) => void = () => {};
    const progress = new Promise((resolve) => {
      resolveProgress = resolve;
    });
    mockApiClient.mockImplementation((url: string) =>
      url.includes('/progress/') ? progress : Promise.resolve({ title: 'OPM' }),
    );

    renderReader();
    expect(await screen.findByTestId('reader')).toBeInTheDocument();

    // Progress still in flight, well past the 1.5 s debounce: nothing may go out.
    await vi.advanceTimersByTimeAsync(5000);
    expect(progressWrites()).toHaveLength(0);

    // Progress lands: still nothing, because the user has not turned a page.
    resolveProgress(FINISHED_CHAPTER_PROGRESS);
    await vi.advanceTimersByTimeAsync(5000);
    expect(progressWrites()).toHaveLength(0);
  });

  it('still writes normally once the user actually turns a page', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockApiClient.mockImplementation((url: string) =>
      url.includes('/progress/') ? Promise.resolve(FINISHED_CHAPTER_PROGRESS) : Promise.resolve({}),
    );

    renderReader();
    await screen.findByTestId('reader');
    await vi.advanceTimersByTimeAsync(100);

    act(() => useReaderStore.getState().setCurrentPageIndex(12));
    await vi.advanceTimersByTimeAsync(2000);

    const writes = progressWrites();
    expect(writes).toHaveLength(1);
    expect(JSON.parse((writes[0][1] as { body: string }).body)).toEqual({
      last_page_read: 12,
      is_read: false,
    });
  });

  it('marks the chapter read through the progress endpoint on "next chapter"', async () => {
    mockApiClient.mockImplementation((url: string) =>
      url.includes('/progress/') ? Promise.resolve(FINISHED_CHAPTER_PROGRESS) : Promise.resolve({}),
    );

    renderReader();
    await screen.findByTestId('reader');
    await waitFor(() => expect(mockApiClient).toHaveBeenCalled());

    fireEvent.click(screen.getByText(/Chapitre Suivant/i));

    await waitFor(() => expect(progressWrites()).toHaveLength(1));
    expect(JSON.parse((progressWrites()[0][1] as { body: string }).body)).toEqual({
      last_page_read: 0,
      is_read: true,
    });
    // The legacy /sync/ endpoint is gone: the server pushes to the trackers
    // itself on the read transition, calling both would double-push.
    expect(
      mockApiClient.mock.calls.filter(([url]) => typeof url === 'string' && url.includes('/sync/')),
    ).toHaveLength(0);
    expect(navigateSpy).toHaveBeenCalledWith('/media/manga/m1/6/');
  });

  it('emits nothing at all for an anonymous visitor', async () => {
    authState = { isAuthenticated: false, isLoading: false };
    mockApiClient.mockResolvedValue({});

    renderReader();
    await screen.findByTestId('reader');
    act(() => useReaderStore.getState().setCurrentPageIndex(12));
    await new Promise((resolve) => setTimeout(resolve, 2000));

    expect(progressWrites()).toHaveLength(0);
    expect(
      mockApiClient.mock.calls.filter(
        ([url]) => typeof url === 'string' && url.includes('/progress/'),
      ),
    ).toHaveLength(0);
  });
});
