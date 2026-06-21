import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import HealthPage from '../HealthPage';

interface HealthPayload {
  brain_status?: string;
  cache_status?: string;
  celery_status?: string;
}

const mockUseHealth = vi.fn<() => { data: HealthPayload | undefined; isLoading: boolean }>();
vi.mock('../../../features/admin/hooks/useHealth', () => ({
  useHealth: () => mockUseHealth(),
}));

const mockApiClient = vi.fn();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: (url: string, init?: RequestInit) => mockApiClient(url, init),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <HealthPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('HealthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders skeletons while health data is loading', () => {
    mockUseHealth.mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(screen.getByText('BRAIN API')).toBeInTheDocument();
    expect(screen.getByText('POSTGRES')).toBeInTheDocument();
    // No status badges resolved in loading state.
    expect(screen.queryByText('ONLINE')).not.toBeInTheDocument();
  });

  it('renders statuses when data is loaded', () => {
    mockUseHealth.mockReturnValue({
      data: { brain_status: 'Online', cache_status: 'Online', celery_status: 'Offline' },
      isLoading: false,
    });
    renderPage();
    expect(screen.getByText('REDIS CACHE')).toBeInTheDocument();
    expect(screen.getByText('CELERY')).toBeInTheDocument();
    // Postgres is hardcoded "Connected".
    expect(screen.getByText('CONNECTED')).toBeInTheDocument();
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
    expect(screen.getAllByText('ONLINE').length).toBeGreaterThan(0);
  });

  it('fires the pipeline mutation and shows the success banner', async () => {
    mockUseHealth.mockReturnValue({
      data: { brain_status: 'Online' },
      isLoading: false,
    });
    mockApiClient.mockResolvedValue({ status: 'Scraper lancé' });
    renderPage();

    fireEvent.click(screen.getByText('Run Scrapers'));

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith(
        '/api/v1/admin/pipelines/control/run_scraper/',
        { method: 'POST' },
      );
      expect(screen.getByText('Scraper lancé')).toBeInTheDocument();
    });
  });

  it('shows the error banner when the pipeline mutation fails', async () => {
    mockUseHealth.mockReturnValue({
      data: { brain_status: 'Online' },
      isLoading: false,
    });
    mockApiClient.mockRejectedValue(new Error('Boom failure'));
    renderPage();

    fireEvent.click(screen.getByText('Sync Neo4j'));

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith(
        '/api/v1/admin/pipelines/control/sync_neo4j/',
        { method: 'POST' },
      );
      expect(screen.getByText('Boom failure')).toBeInTheDocument();
    });
  });
});
