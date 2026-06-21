import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ClassicGameState } from '../../../types';
import ClassicGamePage from '../ClassicGamePage';

interface ClassicGameHook {
  gameState: ClassicGameState | undefined;
  loading: boolean;
  handleGuess: (arg: { guess: string }) => Promise<void>;
  restart: () => void;
}

const handleGuess = vi.fn<(arg: { guess: string }) => Promise<void>>(() => Promise.resolve());
const restart = vi.fn();
let hookValue: ClassicGameHook;

vi.mock('../../../features/games/hooks/useClassicGame', () => ({
  useClassicGame: () => hookValue,
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ClassicGamePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const baseState = (over: Partial<ClassicGameState> = {}): ClassicGameState => ({
  gameOver: false,
  mediaType: 'anime',
  isDaily: false,
  guesses: [],
  ...over,
});

describe('ClassicGamePage', () => {
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

  it('renders the guess form and empty history when active', () => {
    renderPage();
    expect(screen.getByText(/CLASSIC/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Entrez un titre/i)).toBeInTheDocument();
    expect(screen.getByText(/Aucune tentative/i)).toBeInTheDocument();
  });

  it('submits a guess and clears the input', async () => {
    renderPage();
    const input = screen.getByPlaceholderText(/Entrez un titre/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Naruto' } });
    fireEvent.click(screen.getByText(/ENVOYER/i));
    await waitFor(() => expect(handleGuess).toHaveBeenCalledWith({ guess: 'Naruto' }));
  });

  it('renders previous guesses with correct/incorrect badges', () => {
    hookValue = {
      gameState: baseState({
        guesses: [
          { title: 'One Piece', is_correct: false },
          { title: 'Bleach', is_correct: true },
        ],
      }),
      loading: false,
      handleGuess,
      restart,
    };
    renderPage();
    expect(screen.getByText('One Piece')).toBeInTheDocument();
    expect(screen.getByText('TROUVÉ')).toBeInTheDocument();
    expect(screen.getByText('FAUX')).toBeInTheDocument();
  });

  it('renders the victory state and triggers restart', () => {
    hookValue = {
      gameState: baseState({ gameOver: true, secret_title: 'Death Note' }),
      loading: false,
      handleGuess,
      restart,
    };
    renderPage();
    expect(screen.getByText(/VICTOIRE/i)).toBeInTheDocument();
    expect(screen.getByText(/Death Note/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/REJOUER/i));
    expect(restart).toHaveBeenCalled();
  });
});
