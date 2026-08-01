import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
    });
    const link = vi.spyOn(svc, 'linkTracker').mockResolvedValue({} as never);

    wrap(<TrackerLinkCard mediaId="m1" />);

    await screen.findByText(/One Punch-Man/);
    await userEvent.click(screen.getByRole('button', { name: /lier/i }));
    await waitFor(() => expect(link).toHaveBeenCalledWith('m1', 'anilist', '30013'));
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
});
