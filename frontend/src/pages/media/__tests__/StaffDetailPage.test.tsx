import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import StaffDetailPage from '../StaffDetailPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockedApiClient = vi.mocked(apiClient);

const renderAt = (path = '/staff/3/') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/staff/:staffId/" element={<StaffDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('StaffDetailPage', () => {
  beforeEach(() => {
    mockedApiClient.mockReset();
  });

  it('renders loading state', () => {
    mockedApiClient.mockReturnValue(new Promise(() => {}));
    const { container } = renderAt();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders not-found state on error', async () => {
    mockedApiClient.mockRejectedValue(new Error('404'));
    renderAt();
    expect(await screen.findByText(/Artiste introuvable/i)).toBeInTheDocument();
  });

  it('renders populated staff with fallbacks when metadata is empty', async () => {
    mockedApiClient.mockResolvedValue({
      title: 'Shinichiro Watanabe',
      image: undefined,
      description: 'Renowned anime director.',
      metadata: undefined,
    });
    renderAt();
    expect(await screen.findByText('Shinichiro Watanabe')).toBeInTheDocument();
    expect(screen.getByText('Renowned anime director.')).toBeInTheDocument();
    expect(screen.getByText(/Professionnel de l'industrie/i)).toBeInTheDocument();
    expect(screen.getByText(/Indexation de la filmographie/i)).toBeInTheDocument();
  });

  it('renders roles and notable works from metadata', async () => {
    mockedApiClient.mockResolvedValue({
      title: 'Yoko Kanno',
      image: 'http://img/yk.jpg',
      description: 'Composer.',
      metadata: {
        roles: ['Composer'],
        notable_works: [
          { id: '1', title: 'Bebop OST', type: 'Anime', role: 'Music' },
        ],
      },
    });
    renderAt();
    expect(await screen.findByText('Yoko Kanno')).toBeInTheDocument();
    expect(screen.getByText('Composer')).toBeInTheDocument();
    expect(screen.getByText('Bebop OST')).toBeInTheDocument();
  });
});
