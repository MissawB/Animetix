import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { EmojiState } from '../../../types';
import EmojiPage from '../EmojiPage';

interface EmojiHook {
  gameState: EmojiState | undefined;
  loading: boolean;
  handleGuess: (arg: { guess: string }) => Promise<void>;
  restart: () => void;
}

const handleGuess = vi.fn<(arg: { guess: string }) => Promise<void>>(() => Promise.resolve());
const restart = vi.fn();
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

const baseState = (over: Partial<EmojiState> = {}): EmojiState => ({
  game_over: false,
  media_type: 'anime',
  is_daily: false,
  emojis: ['🏴‍☠️', '👒'],
  total_emojis: 4,
  guesses: [],
  ...over,
});

describe('EmojiPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hookValue = { gameState: baseState(), loading: false, handleGuess, restart };
  });

  it('renders a skeleton while loading', () => {
    hookValue = { gameState: undefined, loading: true, handleGuess, restart };
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders nothing when there is no game state', () => {
    hookValue = { gameState: undefined, loading: false, handleGuess, restart };
    const { container } = renderPage();
    expect(container).toBeEmptyDOMElement();
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
    const opt = await screen.findByText('Attack on Titan');
    expect(screen.getByText('進撃の巨人')).toBeInTheDocument();
    expect(screen.getByText('Shingeki no Kyojin')).toBeInTheDocument();
    fireEvent.mouseDown(opt);
    await waitFor(() =>
      expect(handleGuess).toHaveBeenCalledWith({ guess: 'Shingeki no Kyojin' }),
    );
  });

  it('renders prior attempts with badges', () => {
    hookValue = {
      gameState: baseState({
        guesses: [
          { title: 'Bleach', image: 'b.jpg', is_correct: false },
          { title: 'Naruto', title_en: 'Naruto EN', image: 'n.jpg', is_correct: true },
        ],
      }),
      loading: false,
      handleGuess,
      restart,
    };
    renderPage();
    expect(screen.getByText('Bleach')).toBeInTheDocument();
    expect(screen.getByText('Naruto EN')).toBeInTheDocument();
    expect(screen.getByText('TROUVÉ')).toBeInTheDocument();
    expect(screen.getByText('ÉCHEC')).toBeInTheDocument();
  });

  it('renders the victory state and triggers restart', () => {
    hookValue = {
      gameState: baseState({ game_over: true, secret_title: 'One Piece' }),
      loading: false,
      handleGuess,
      restart,
    };
    renderPage();
    expect(screen.getByText(/VICTOIRE/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/REJOUER/i));
    expect(restart).toHaveBeenCalled();
  });
});
