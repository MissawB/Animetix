import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as svc from './trackerLinkService';
import { TrackerLinkCard } from './TrackerLinkCard';

const wrap = (ui: React.ReactNode) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(React.createElement(QueryClientProvider, { client }, ui));
};

// Contrôle réactif de l'auth, comme le vrai store zustand : sélecteur ET
// `.getState()` doivent tous les deux fonctionner sur ce mock (cf. ChapterList.test.tsx).
// Par défaut un visiteur connecté (les scénarios de liaison le supposent) ;
// seul le test "anonyme" bascule ce flag à false.
let mockIsAuthenticated = true;
vi.mock('../../../store/authStore', () => {
  const state = () => ({ isAuthenticated: mockIsAuthenticated });
  const useAuthStore = Object.assign(
    (selector: (s: { isAuthenticated: boolean }) => unknown) => selector(state()),
    { getState: state },
  );
  return { useAuthStore };
});

beforeEach(() => {
  vi.restoreAllMocks();
  mockIsAuthenticated = true;
});

describe('TrackerLinkCard', () => {
  it('offers to confirm a suggested link', async () => {
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [
        {
          tracker: 'anilist',
          status: 'suggested',
          remote_id: '30013',
          remote_title: 'One Punch-Man',
          remote_progress: null,
        },
      ],
      connected: ['anilist'],
    });
    const link = vi.spyOn(svc, 'linkTracker').mockResolvedValue({} as never);

    wrap(<TrackerLinkCard mediaId="m1" />);

    await screen.findByText(/One Punch-Man/);
    await userEvent.click(screen.getByRole('button', { name: /lier/i }));
    await waitFor(() =>
      expect(link).toHaveBeenCalledWith('m1', 'anilist', '30013', 'One Punch-Man'),
    );
  });

  it('shows the remote progress once confirmed', async () => {
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [
        {
          tracker: 'anilist',
          status: 'confirmed',
          remote_id: '30013',
          remote_title: 'One Punch-Man',
          remote_progress: 164,
        },
      ],
      connected: ['anilist'],
    });

    wrap(<TrackerLinkCard mediaId="m1" />);

    expect(await screen.findByText(/164/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /délier/i })).toBeInTheDocument();
  });

  it('renders nothing at all when no tracker is connected', async () => {
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({ links: [], connected: [] });

    const { container } = wrap(<TrackerLinkCard mediaId="m1" />);

    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it('invites a manual search when a tracker is connected but nothing matched', async () => {
    // Les deux cas donnent `links: []` — seul `connected` les distingue.
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [],
      connected: ['anilist'],
    });

    wrap(<TrackerLinkCard mediaId="m1" />);

    expect(await screen.findByText(/aucune correspondance/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /chercher/i })).toBeInTheDocument();
  });

  it('never calls the API for an anonymous visitor', async () => {
    const fetchLinks = vi.spyOn(svc, 'fetchTrackerLinks');
    mockIsAuthenticated = false;
    wrap(<TrackerLinkCard mediaId="m1" />);
    await waitFor(() => expect(fetchLinks).not.toHaveBeenCalled());
  });

  it('links a manually-picked candidate end to end', async () => {
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [],
      connected: ['anilist'],
    });
    const search = vi.spyOn(svc, 'searchTracker').mockResolvedValue({
      results: [{ remote_id: '99999', title: 'One Punch-Man (verified)', chapters: 200 }],
    });
    const link = vi.spyOn(svc, 'linkTracker').mockResolvedValue({} as never);

    wrap(<TrackerLinkCard mediaId="m1" />);

    await userEvent.click(await screen.findByRole('button', { name: /chercher autre chose/i }));

    const input = await screen.findByLabelText(/titre à rechercher/i);
    fireEvent.change(input, { target: { value: 'One Punch' } });
    await userEvent.click(screen.getByRole('button', { name: 'Rechercher' }));

    await waitFor(() => expect(search).toHaveBeenCalledWith('m1', 'anilist', 'One Punch'));

    const candidate = await screen.findByText(/One Punch-Man \(verified\)/);
    await userEvent.click(candidate);

    // Le titre du candidat part avec la confirmation : c'est le seul moment où
    // le frontend l'a, et sans lui la liaison corrigée s'affiche sans nom.
    await waitFor(() =>
      expect(link).toHaveBeenCalledWith('m1', 'anilist', '99999', 'One Punch-Man (verified)'),
    );
  });

  it('hides a link whose tracker account is no longer connected', async () => {
    // Les liaisons survivent à une déconnexion côté backend (elles redeviennent
    // actives à la reconnexion) : c'est l'affichage qui doit les filtrer, sinon
    // la fiche œuvre contredit le panneau profil qui, lui, n'affiche plus rien.
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [
        {
          tracker: 'anilist',
          status: 'confirmed',
          remote_id: '30013',
          remote_title: 'One Punch-Man',
          remote_progress: 164,
        },
        {
          tracker: 'myanimelist',
          status: 'confirmed',
          remote_id: '44347',
          remote_title: 'Orphan MAL link',
          remote_progress: 12,
        },
      ],
      connected: ['anilist'],
    });

    wrap(<TrackerLinkCard mediaId="m1" />);

    expect(await screen.findByText(/One Punch-Man/)).toBeInTheDocument();
    expect(screen.queryByText(/Orphan MAL link/)).not.toBeInTheDocument();
    expect(screen.queryByText(/12 chapitres/)).not.toBeInTheDocument();
    // Un seul « Délier » : celui du compte encore connecté.
    expect(screen.getAllByRole('button', { name: /délier/i })).toHaveLength(1);
    // Et MyAnimeList n'apparaît pas non plus en « aucune correspondance » :
    // le compte n'est plus connecté du tout.
    expect(screen.queryByText(/MyAnimeList/)).not.toBeInTheDocument();
  });

  it('points to the profile when nothing matched, expired token included', async () => {
    // Décision produit : un seul état « aucune correspondance » plutôt que des
    // états « injoignable » / « connexion expirée » que le port ne sait pas
    // distinguer. L'indice donne une sortie à l'utilisateur au jeton expiré.
    vi.spyOn(svc, 'fetchTrackerLinks').mockResolvedValue({
      links: [],
      connected: ['anilist'],
    });

    wrap(<TrackerLinkCard mediaId="m1" />);

    expect(await screen.findByText(/aucune correspondance/i)).toBeInTheDocument();
    expect(
      screen.getByText(/vérifiez la connexion de ce compte dans votre profil/i),
    ).toBeInTheDocument();
  });
});
