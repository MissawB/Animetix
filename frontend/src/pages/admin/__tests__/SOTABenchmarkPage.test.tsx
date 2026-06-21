import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import SOTABenchmarkPage from '../SOTABenchmarkPage';
import type { BenchmarkData, ModelBenchmark } from '../../../types';

const mockApiClient = vi.fn();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: (url: string) => mockApiClient(url),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SOTABenchmarkPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const model = (over: Partial<ModelBenchmark>): ModelBenchmark => ({
  model_id: 'gpt-x',
  provider: 'OpenAI',
  elo_score: 1200,
  mmlu_score: 88,
  context_window: 128000,
  is_open_source: false,
  license: 'proprietary',
  ...over,
});

const data: BenchmarkData = {
  benchmarks: [
    model({ model_id: 'claude-apex', elo_score: 1400, mmlu_score: 91, is_open_source: false }),
    model({ model_id: 'llama-oss', elo_score: 1300, mmlu_score: 85, is_open_source: true, provider: 'Meta' }),
  ],
  top_model: model({ model_id: 'claude-apex', provider: 'Anthropic', elo_score: 1400, mmlu_score: 91 }),
  best_open_source: model({
    model_id: 'llama-oss',
    provider: 'Meta',
    license: 'apache-2.0',
    is_open_source: true,
    context_window: 256000,
  }),
};

describe('SOTABenchmarkPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the loading spinner state', () => {
    mockApiClient.mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/Syncing SOTA Metrics/i)).toBeInTheDocument();
  });

  it('renders the error state on fetch failure', async () => {
    mockApiClient.mockRejectedValue(new Error('network down'));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Sync Failure/i)).toBeInTheDocument();
    });
  });

  it('renders spotlight models and the comparison matrix when loaded', async () => {
    mockApiClient.mockResolvedValue(data);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('APEX MODEL')).toBeInTheDocument();
    });
    expect(mockApiClient).toHaveBeenCalledWith('/api/v1/mlops/sota/benchmarks/');
    expect(screen.getByText('BEST OPEN SOURCE')).toBeInTheDocument();
    // top_model spotlight values
    expect(screen.getByText('Provider: Anthropic')).toBeInTheDocument();
    // 91% appears in both the spotlight and the comparison matrix row.
    expect(screen.getAllByText('91%').length).toBeGreaterThan(0);
    // best_open_source: 256000 -> 256k
    expect(screen.getByText('256k')).toBeInTheDocument();
    expect(screen.getByText('License: apache-2.0')).toBeInTheDocument();
    // Comparison matrix rows (rank #01 -> highest ELO = claude-apex)
    expect(screen.getByText('#01')).toBeInTheDocument();
    expect(screen.getByText('#02')).toBeInTheDocument();
    expect(screen.getByText('Open Weights')).toBeInTheDocument();
    expect(screen.getAllByText('Proprietary').length).toBeGreaterThan(0);
  });
});
