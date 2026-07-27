import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import UniversalSearchHubPage from '../UniversalSearchHubPage';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn().mockResolvedValue({ results: [] }),
}));

const renderAt = (path: string) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <UniversalSearchHubPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('UniversalSearchHubPage', () => {
  it('exposes Expert Nexus as an in-page mode, not a navigation link', () => {
    // Régression UX : Expert Nexus renvoyait vers une AUTRE page (mauvaise UX,
    // incohérent avec les autres modes qui basculent sur place). C'est désormais
    // un 3e mode intégré, piloté par la même barre de recherche.
    renderAt('/search/?q=berserk');

    // Point d'entrée présent, et c'est un bouton (bascule de mode) — plus un lien.
    expect(screen.getByRole('button', { name: /Expert Nexus/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Expert Nexus/i })).toBeNull();
  });
});
