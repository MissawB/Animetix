import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AdminEvalPage from '../AdminEvalPage';

interface EvalPayload {
  stats: { total: number; avg_faith: number; avg_rel: number; avg_prec: number };
}

const mockUseAdminEval = vi.fn<() => { data: EvalPayload | undefined; loading: boolean }>();
vi.mock('../../../features/admin/hooks/useAdminEval', () => ({
  useAdminEval: () => mockUseAdminEval(),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AdminEvalPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('AdminEvalPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders skeletons while loading', () => {
    mockUseAdminEval.mockReturnValue({ data: undefined, loading: true });
    const { container } = renderPage();
    // Loading branch renders skeleton grid, no heading.
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    expect(container.querySelector('.grid')).toBeInTheDocument();
  });

  it('renders the error card when there is no data', () => {
    mockUseAdminEval.mockReturnValue({ data: undefined, loading: false });
    renderPage();
    expect(screen.getByText('common.error')).toBeInTheDocument();
    expect(screen.getByText('admin.eval.error')).toBeInTheDocument();
  });

  it('renders stats when data is available', () => {
    mockUseAdminEval.mockReturnValue({
      data: { stats: { total: 42, avg_faith: 0.912, avg_rel: 0.834, avg_prec: 0.756 } },
      loading: false,
    });
    renderPage();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('0.912')).toBeInTheDocument();
    expect(screen.getByText('0.834')).toBeInTheDocument();
    expect(screen.getByText('0.756')).toBeInTheDocument();
    expect(screen.getByText('admin.eval.stats.faithfulness')).toBeInTheDocument();
    expect(screen.getByText('admin.eval.stats.relevancy')).toBeInTheDocument();
    expect(screen.getByText('admin.eval.stats.precision')).toBeInTheDocument();
  });
});
