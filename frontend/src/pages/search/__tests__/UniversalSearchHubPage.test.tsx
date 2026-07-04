import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import UniversalSearchHubPage from '../UniversalSearchHubPage';

vi.mock('../../../utils/apiClient', () => ({ apiClient: vi.fn().mockResolvedValue({ results: [] }) }));

const renderAt = (path: string) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <UniversalSearchHubPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('UniversalSearchHubPage', () => {
  it('exposes a reachable Expert Nexus entry point carrying the query', () => {
    // Régression : Expert Nexus n'avait aucun point d'entrée depuis le hub
    // (le seul lien vivait sur une page orpheline et pointait vers une route
    // inexistante /search/expert/). Le mode expert était donc inaccessible.
    renderAt('/search/?q=berserk');

    const link = screen.getByRole('link', { name: /Expert Nexus/i });
    expect(link).toHaveAttribute('href', '/search/expert-nexus/?q=berserk');
  });

  it('links to Expert Nexus without a query param when the box is empty', () => {
    renderAt('/search/');
    const link = screen.getByRole('link', { name: /Expert Nexus/i });
    expect(link).toHaveAttribute('href', '/search/expert-nexus/');
  });
});
