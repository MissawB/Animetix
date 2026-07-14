import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SearchBar } from '../SearchBar';
import { searchByImage } from '../../api';

vi.mock('../../api', () => ({
  searchMedia: vi.fn(),
  searchByImage: vi.fn(),
}));

const mockedSearch = vi.mocked(searchByImage);

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

  it("annonce honnêtement un index non construit (503), sans jamais dire 'aucun résultat'", async () => {
    const error = new Error(
      "Recherche indisponible : l'index des personnages n'a pas encore été construit. Réessayez plus tard.",
    ) as Error & { status?: number };
    error.status = 503;
    mockedSearch.mockRejectedValue(error);
    renderSearchBar();

    await userEvent.click(screen.getByRole('radio', { name: /personnage/i }));
    await userEvent.upload(screen.getByLabelText(/image/i), file);

    expect(await screen.findByText(/n'a pas encore été construit/i)).toBeInTheDocument();
    expect(screen.queryByText(/aucun résultat/i)).not.toBeInTheDocument();
  });
});
