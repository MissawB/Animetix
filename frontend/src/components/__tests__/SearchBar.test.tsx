import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SearchBar } from '../SearchBar';
import { searchService } from '../../features/search/services/searchService';

vi.mock('../../features/search/services/searchService', () => ({
  searchService: {
    searchMedia: vi.fn(),
    searchByImage: vi.fn(),
  },
}));

const mockedSearch = vi.mocked(searchService.searchByImage);

const file = new File([new Uint8Array([1, 2, 3])], 'cover.png', { type: 'image/png' });

function renderSearchBar() {
  return render(
    <MemoryRouter>
      <SearchBar />
    </MemoryRouter>,
  );
}

describe('SearchBar — recherche visuelle', () => {
  beforeEach(() => vi.clearAllMocks());

  it('laisse choisir entre une jaquette et un personnage', () => {
    renderSearchBar();
    expect(screen.getByRole('radio', { name: /jaquette/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /personnage/i })).toBeInTheDocument();
  });

  it("cherche par jaquette (l'œuvre) par défaut", () => {
    renderSearchBar();
    expect(screen.getByRole('radio', { name: /jaquette/i })).toBeChecked();
    expect(screen.getByRole('radio', { name: /personnage/i })).not.toBeChecked();
  });

  it('envoie la cible choisie au serveur', async () => {
    mockedSearch.mockResolvedValue([]);
    renderSearchBar();

    await userEvent.click(screen.getByRole('radio', { name: /personnage/i }));
    await userEvent.upload(screen.getByLabelText(/image/i), file);

    expect(mockedSearch).toHaveBeenCalledWith(expect.any(File), 'character');
  });

  it("ne promet pas de retrouver un anime depuis une capture d'écran", () => {
    renderSearchBar();
    expect(screen.queryByText(/capture|screenshot|scène/i)).not.toBeInTheDocument();
  });

  /** Une erreur telle que `apiClient` la produit : un statut HTTP porté par l'Error. */
  const httpError = (status: number, serverProse = 'peu importe ce que dit le serveur') => {
    const error = new Error(serverProse) as Error & { status?: number };
    error.status = status;
    return error;
  };

  async function uploadWith(error: unknown, target: RegExp = /personnage/i) {
    mockedSearch.mockRejectedValue(error);
    renderSearchBar();
    await userEvent.click(screen.getByRole('radio', { name: target }));
    await userEvent.upload(screen.getByLabelText(/image/i), file);
  }

  it("annonce honnêtement un index non construit (503), sans jamais dire 'aucun résultat'", async () => {
    await uploadWith(httpError(503));

    expect(await screen.findByText(/n'a pas encore été construit/i)).toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });

  it('classe le 503 sur le STATUT, pas sur la prose du serveur', async () => {
    // Le backend renvoie ici un texte qui ne dit rien d'un index : si le
    // composant se fiait au message, la propriété d'honnêteté disparaîtrait
    // en silence le jour où le backend reformule.
    await uploadWith(httpError(503, 'Service Unavailable'));

    expect(await screen.findByText(/n'a pas encore été construit/i)).toBeInTheDocument();
    expect(screen.queryByText(/Service Unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });

  it('annonce une requête invalide (400)', async () => {
    await uploadWith(httpError(400));

    expect(await screen.findByText(/requête invalide/i)).toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });

  it("sur un 500, ne prétend pas que la recherche a tourné et n'a rien trouvé", async () => {
    await uploadWith(httpError(500));

    expect(await screen.findByText(/la recherche a échoué/i)).toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });

  it("sur une panne réseau (aucun statut), n'affiche jamais l'exception brute", async () => {
    // Ce que fetch() jette quand il n'y a aucune réponse : pas de `status`.
    await uploadWith(new TypeError('Failed to fetch'));

    expect(await screen.findByText(/serveur injoignable/i)).toBeInTheDocument();
    expect(screen.queryByText(/Failed to fetch/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });
});
