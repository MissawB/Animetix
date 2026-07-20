import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { LibraryButton } from '../LibraryButton';
import { apiClient } from '../../../../utils/apiClient';
import { useAuthStore } from '../../../../store/authStore';

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
const mockedApiClient = vi.mocked(apiClient);

const renderBtn = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <LibraryButton mediaId="42" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ isAuthenticated: true });
});

it('adds the manga to the library on click when authenticated', async () => {
  mockedApiClient.mockResolvedValue({ is_favorite: false, status: null });
  renderBtn();
  await waitFor(() =>
    expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/media/Manga/42/favorite/'),
  );
  mockedApiClient.mockResolvedValue({ success: true, is_favorite: true, status: 'plan_to_read' });
  fireEvent.click(screen.getByRole('button', { name: /bibliothèque/i }));
  await waitFor(() =>
    expect(mockedApiClient).toHaveBeenCalledWith(
      '/api/v1/media/Manga/42/favorite/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ status: 'plan_to_read' }),
      }),
    ),
  );
});

it('does not fetch state and prompts login when anonymous', () => {
  useAuthStore.setState({ isAuthenticated: false });
  renderBtn();
  expect(mockedApiClient).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: /bibliothèque/i }));
  expect(screen.getByRole('link', { name: /connexion/i })).toHaveAttribute('href', '/auth/login/');
});
