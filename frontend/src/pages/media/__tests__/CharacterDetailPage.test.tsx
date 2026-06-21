import '@testing-library/jest-dom';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import CharacterDetailPage from '../CharacterDetailPage';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockedApiClient = vi.mocked(apiClient);

const renderAt = (path = '/character/5/') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/character/:characterId/" element={<CharacterDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CharacterDetailPage', () => {
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
    expect(await screen.findByText(/Personnage introuvable/i)).toBeInTheDocument();
  });

  it('renders populated character with fallback placeholders', async () => {
    mockedApiClient.mockResolvedValue({
      title: 'Spike Spiegel',
      image: 'http://img/spike.jpg',
      description: 'A laid-back bounty hunter.',
      popularity: 1,
      metadata: {},
    });
    renderAt();
    expect(await screen.findByText('Spike Spiegel')).toBeInTheDocument();
    expect(screen.getByText('A laid-back bounty hunter.')).toBeInTheDocument();
    // default trait fallback badge
    expect(screen.getByText('Personnage Nexus')).toBeInTheDocument();
  });

  it('renders appearances and seiyuu sections from metadata', async () => {
    mockedApiClient.mockResolvedValue({
      title: 'Edward',
      image: 'http://img/ed.jpg',
      description: 'Hacker.',
      metadata: {
        traits: ['Genius'],
        appearances: [{ id: '10', title: 'Bebop Session 9' }],
        seiyuu: [{ id: 20, name: 'Aoi Tada' }],
      },
    });
    renderAt();
    expect(await screen.findByText('Edward')).toBeInTheDocument();
    expect(screen.getByText('Genius')).toBeInTheDocument();
    expect(screen.getByText('Bebop Session 9')).toBeInTheDocument();
    expect(screen.getByText('Aoi Tada')).toBeInTheDocument();
  });
});
