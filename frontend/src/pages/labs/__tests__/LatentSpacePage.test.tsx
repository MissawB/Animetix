import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import LatentSpacePage from '../LatentSpacePage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../../../components/LazyPlot', () => ({
  default: () => <div>Mocked 3D Latent Plot</div>,
}));

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LatentSpacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('LatentSpacePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient).mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/Projection Dimensionnelle/i)).toBeInTheDocument();
  });

  it('renders plot and controls when data is loaded', async () => {
    vi.mocked(apiClient).mockResolvedValue([
      { x: 1, y: 2, z: 3, title: 'Naruto', category: 'Shonen' },
    ]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Mocked 3D Latent Plot')).toBeInTheDocument();
    });
  });
});
