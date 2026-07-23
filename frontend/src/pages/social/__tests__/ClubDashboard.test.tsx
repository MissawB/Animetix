import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ClubDashboard from '../ClubDashboard';

vi.mock('../../../features/social/hooks/useClub', () => ({
  useClub: (id: number) => ({
    club: id === 1 ? { id: 1, name: 'Otaku Club', description: 'Best club' } : null,
    isLoadingClub: false,
    events: [],
  }),
}));

vi.mock('../../../features/social/components/ClubChat', () => ({
  default: () => <div>Mocked Club Chat</div>,
}));

const renderPage = (clubId = '1') => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/clubs/${clubId}`]}>
        <Routes>
          <Route path="/clubs/:id" element={<ClubDashboard />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('ClubDashboard', () => {
  it('renders club title and chat tab when club exists', () => {
    renderPage('1');
    expect(screen.getByText('Otaku Club')).toBeInTheDocument();
    expect(screen.getByText('Mocked Club Chat')).toBeInTheDocument();
  });

  it('renders placeholder header when club data is missing', () => {
    renderPage('999');
    expect(screen.getByText(/Chargement.../i)).toBeInTheDocument();
  });
});
