import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ProfilePage from '../ProfilePage';
import { useAuthStore } from '../../../store/authStore';
import { useProfile } from '../../../features/social/hooks/useProfile';
import { socialService } from '../../../features/social/services/socialService';

vi.mock('../../../store/authStore');
vi.mock('../../../features/social/hooks/useProfile');
vi.mock('../../../features/social/services/socialService', () => ({
  socialService: {
    getTrackerConnections: vi.fn(),
    linkTracker: vi.fn(),
    unlinkTracker: vi.fn(),
  },
}));

const mockProfileData = {
  id: 'USER-1',
  username: 'KiritoMaster',
  rank: 'Épiste Noir',
  level: 42,
  xp: 15400,
  achievements_count: 8,
  collection_count: 24,
  unlocked_badges: ['Sponsor Or'],
  recent_achievements: [
    {
      name: 'Premier Sang',
      description: 'Gagner votre premier duel.',
    },
  ],
  top_fusions: [
    {
      title_a: 'SAO',
      title_b: 'Solo Leveling',
      image_url: 'https://example.com/fusion.jpg',
    },
  ],
};

const renderPage = (username = 'KiritoMaster') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/profile/${username}`]}>
        <Routes>
          <Route path="/profile/:username" element={<ProfilePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useProfile).mockReturnValue({
      data: mockProfileData,
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useProfile>);

    vi.mocked(socialService.getTrackerConnections).mockResolvedValue([
      { id: 1, tracker: 'myanimelist', username: 'KiritoMAL', created_at: '2026-01-01T00:00:00Z' },
    ]);
  });

  it('renders user profile header, rank, level, and stats', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
    } as unknown as ReturnType<typeof useAuthStore>);

    renderPage('KiritoMaster');

    expect(screen.getByText('KiritoMaster')).toBeInTheDocument();
    expect(screen.getByText(/15400/)).toBeInTheDocument();
    expect(screen.getByText('Premier Sang')).toBeInTheDocument();
    expect(screen.getByText(/SAO x Solo Leveling/i)).toBeInTheDocument();
    expect(screen.getByText('SPONSOR OR')).toBeInTheDocument();
  });

  it('renders tracker synchronization panel for own profile', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { username: 'KiritoMaster' },
    } as unknown as ReturnType<typeof useAuthStore>);

    renderPage('KiritoMaster');

    await waitFor(() => {
      expect(screen.getByText(/Synchronisation des Trackers/i)).toBeInTheDocument();
      expect(screen.getByText('KiritoMAL')).toBeInTheDocument();
      expect(screen.getByText('Associer AniList')).toBeInTheDocument();
    });
  });

  it('opens tracker linking modal and submits connection form', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { username: 'KiritoMaster' },
    } as unknown as ReturnType<typeof useAuthStore>);

    renderPage('KiritoMaster');

    await waitFor(() => {
      expect(screen.getByText('Associer AniList')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Associer AniList'));

    expect(screen.getByRole('heading', { name: /Associer AniList/i })).toBeInTheDocument();

    const usernameInput = screen.getByLabelText(/Nom d'utilisateur/i);
    const tokenInput = screen.getByLabelText(/Jeton d'accès/i);

    fireEvent.change(usernameInput, { target: { value: 'AniKirito' } });
    fireEvent.change(tokenInput, { target: { value: 'token12345' } });

    vi.mocked(socialService.linkTracker).mockResolvedValue({ success: true });

    const submitBtn = screen.getByRole('button', { name: /Enregistrer la connexion/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(socialService.linkTracker).toHaveBeenCalledWith('anilist', 'AniKirito', 'token12345');
    });
  });
});
