import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { EmojiState } from '../../../types';
import EmojiPage from '../EmojiPage';

interface EmojiHook {
  gameState: EmojiState | undefined;
  starting: boolean;
  handleGuess: (arg: { guess: string }) => Promise<void>;
  giveUp: () => void;
  start: (mediaType?: string, difficulty?: string) => void;
  reset: () => void;
}

const handleGuess = vi.fn<(arg: { guess: string }) => Promise<void>>(() => Promise.resolve());
const giveUp = vi.fn();
const start = vi.fn();
const reset = vi.fn();
let hookValue: EmojiHook;

vi.mock('../../../features/games/hooks/useEmoji', () => ({
  useEmoji: () => hookValue,
}));

vi.mock('../../../features/games/services/emojiService', () => ({
  emojiService: { suggest: vi.fn(() => Promise.resolve([])) },
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EmojiPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const hook = (over: Partial<EmojiHook> = {}): EmojiHook => ({
  gameState: undefined,
  starting: false,
  handleGuess,
  giveUp,
  start,
  reset,
  ...over,
});

const baseState = (over: Partial<EmojiState> = {}): EmojiState => ({
  game_over: false,
  media_type: 'Anime',
  difficulty: 'Normal',
  is_daily: false,
  emojis: ['🏴‍☠️', '👒'],
  total_emojis: 4,
  guesses: [],
  ...over,
});

describe('EmojiPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hookValue = hook({ gameState: baseState() });
  });

  it('renders a skeleton while a game is starting', () => {
    hookValue = hook({ gameState: undefined, starting: true });
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('shows the chooser (media type + difficulty) when there is no game, and starts with the picks', () => {
    hookValue = hook({ gameState: undefined });
    renderPage();
    expect(screen.getByText('Animés')).toBeInTheDocument();
    expect(screen.getByText('Mangas')).toBeInTheDocument();
    expect(screen.getByText('Personnages')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Mangas'));
    fireEvent.click(screen.getByText('Difficile'));
    fireEvent.click(screen.getByText(/COMMENCER/i));
    expect(start).toHaveBeenCalledWith('Manga', 'Hard');
  });

  it('renders the emoji puzzle and input when active', () => {
    renderPage();
    expect(screen.getByText(/EMOJI/i)).toBeInTheDocument();
    expect(screen.getByText('🏴‍☠️')).toBeInTheDocument();
    expect(screen.getByText('👒')).toBeInTheDocument();
    expect(screen.getByText(/Indice 2 \/ 4/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Cherchez un titre/i)).toBeInTheDocument();
  });

  it('submits a guess and clears the input', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/Cherchez un titre/i), {
      target: { value: 'One Piece' },
    });
    fireEvent.click(screen.getByText(/DEVINER/i));
    await waitFor(() => expect(handleGuess).toHaveBeenCalledWith({ guess: 'One Piece' }));
  });

  it('shows rich suggestions (image + native + english) and submits the picked title', async () => {
    const { emojiService } = await import('../../../features/games/services/emojiService');
    (emojiService.suggest as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce([
      { title: 'Shingeki no Kyojin', title_english: 'Attack on Titan', title_native: '進撃の巨人', image: 'aot.jpg' },
    ]);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText(/Cherchez un titre/i), {
      target: { value: 'attack' },
    });
    const opt = await screen.findByText('Attack on Titan'); // english on top
    expect(screen.getByText('進撃の巨人')).toBeInTheDocument(); // native below
    fireEvent.mouseDown(opt);
    await waitFor(() =>
      expect(handleGuess).toHaveBeenCalledWith({ guess: 'Shingeki no Kyojin' }),
    );
  });

  it('renders prior attempts with badges', () => {
    hookValue = hook({
      gameState: baseState({
        guesses: [
          { title: 'Bleach', image: 'b.jpg', is_correct: false },
          { title: 'Naruto', title_en: 'Naruto EN', image: 'n.jpg', is_correct: true },
        ],
      }),
    });
    renderPage();
    expect(screen.getByText('Bleach')).toBeInTheDocument();
    expect(screen.getByText('Naruto EN')).toBeInTheDocument();
    expect(screen.getByText('TROUVÉ')).toBeInTheDocument();
    expect(screen.getByText('ÉCHEC')).toBeInTheDocument();
  });

  it('renders the victory state and replays with the same settings', () => {
    hookValue = hook({
      gameState: baseState({
        game_over: true,
        media_type: 'Manga',
        difficulty: 'Hard',
        secret_title: 'One Piece',
        guesses: [{ title: 'One Piece', image: 'op.jpg', is_correct: true }],
      }),
    });
    renderPage();
    expect(screen.getByText(/VICTOIRE/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/REJOUER/i));
    expect(start).toHaveBeenCalledWith('Manga', 'Hard');
  });

  it('goes back to the chooser via "Changer de mode"', () => {
    hookValue = hook({
      gameState: baseState({
        game_over: true,
        secret_title: 'One Piece',
        guesses: [{ title: 'One Piece', image: 'op.jpg', is_correct: true }],
      }),
    });
    renderPage();
    fireEvent.click(screen.getByText(/Changer de mode/i));
    expect(reset).toHaveBeenCalled();
  });

  it('triggers giveUp when clicking Abandonner', () => {
    renderPage();
    fireEvent.click(screen.getByText(/Abandonner/i));
    expect(giveUp).toHaveBeenCalled();
  });

  it('shows the abandoned state (no correct guess) instead of victory', () => {
    hookValue = hook({
      gameState: baseState({
        game_over: true,
        secret_title: 'One Piece',
        guesses: [{ title: 'Bleach', image: 'b.jpg', is_correct: false }],
      }),
    });
    renderPage();
    expect(screen.getByText(/abandonn/i)).toBeInTheDocument();
    expect(screen.queryByText(/VICTOIRE/i)).not.toBeInTheDocument();
  });
});
