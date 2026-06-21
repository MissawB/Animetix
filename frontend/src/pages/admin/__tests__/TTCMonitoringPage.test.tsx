import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TTCMonitoringPage from '../TTCMonitoringPage';

interface TTCLog {
  id: number;
  engine: string;
  allocated: number;
  consumed: number;
}
interface TTCMonitoringData {
  summary: { total_allocated: number; total_consumed: number; efficiency: number };
  logs: TTCLog[];
}

const mockApiClient = vi.fn<() => Promise<TTCMonitoringData>>();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: () => mockApiClient(),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TTCMonitoringPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('TTCMonitoringPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the loading spinner initially', () => {
    mockApiClient.mockReturnValue(new Promise(() => {}));
    const { container } = renderPage();
    expect(container.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('renders KPI summary and log rows when data is loaded', async () => {
    mockApiClient.mockResolvedValue({
      summary: { total_allocated: 5000, total_consumed: 4200, efficiency: 84 },
      logs: [
        { id: 1, engine: 'vllm', allocated: 1000, consumed: 800 },
        { id: 2, engine: 'ollama', allocated: 500, consumed: 700 },
      ],
    });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('5000')).toBeInTheDocument();
    });
    expect(screen.getByText('4200')).toBeInTheDocument();
    expect(screen.getByText('84%')).toBeInTheDocument();
    expect(screen.getByText('vllm')).toBeInTheDocument();
    expect(screen.getByText('ollama')).toBeInTheDocument();
    // engine 2 is over budget, engine 1 optimal.
    expect(screen.getByText(/Over Budget/i)).toBeInTheDocument();
    expect(screen.getByText(/Optimal/i)).toBeInTheDocument();
  });

  it('falls back to default summary and empty logs when data is missing', async () => {
    mockApiClient.mockResolvedValue(undefined as unknown as TTCMonitoringData);
    renderPage();

    await waitFor(() => {
      // default efficiency = 100%
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
    expect(screen.getByRole('heading')).toHaveTextContent(/DYNAMIC/i);
    expect(screen.queryByText(/Over Budget/i)).not.toBeInTheDocument();
  });
});
