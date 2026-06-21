import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { BlindtestState } from '../../../types';
import BlindtestPage from '../BlindtestPage';

interface BlindtestStoreValue {
  gameState: BlindtestState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  restartGame: () => Promise<void>;
  submitGuess: (guess: string) => Promise<void>;
}

const loadGame = vi.fn<() => Promise<void>>(() => Promise.resolve());
const restartGame = vi.fn<() => Promise<void>>(() => Promise.resolve());
const submitGuess = vi.fn<(guess: string) => Promise<void>>(() => Promise.resolve());
let storeValue: BlindtestStoreValue;

vi.mock('../../../features/games/stores/blindtestStore', () => ({
  useBlindtestStore: () => storeValue,
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <BlindtestPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const baseState = (over: Partial<BlindtestState> = {}): BlindtestState => ({
  gameOver: false,
  mediaType: 'anime',
  isDaily: false,
  guesses: [],
  ...over,
});

describe('BlindtestPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    storeValue = {
      gameState: baseState(),
      isLoading: false,
      error: null,
      loadGame,
      restartGame,
      submitGuess,
    };
  });

  it('loads the game on mount', () => {
    renderPage();
    expect(loadGame).toHaveBeenCalled();
  });

  it('renders the loading message', () => {
    storeValue = { ...storeValue, gameState: null, isLoading: true };
    renderPage();
    expect(screen.getByText(/Récupération de l'audio/i)).toBeInTheDocument();
  });

  it('renders the error state and reconnects', () => {
    storeValue = { ...storeValue, gameState: null, error: 'signal lost' };
    renderPage();
    expect(screen.getByText(/SIGNAL PERDU/i)).toBeInTheDocument();
    expect(screen.getByText('signal lost')).toBeInTheDocument();
    fireEvent.click(screen.getByText(/RECONNEXION/i));
    expect(restartGame).toHaveBeenCalled();
  });

  it('renders nothing without game state when idle', () => {
    storeValue = { ...storeValue, gameState: null };
    const { container } = renderPage();
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the guess input and submits', () => {
    renderPage();
    expect(screen.getByText(/DÉCOUVREZ L'ANIMÉ/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Titre de l'animé/i), {
      target: { value: 'Bleach' },
    });
    fireEvent.click(screen.getByText(/VALIDER MA RÉPONSE/i));
    expect(submitGuess).toHaveBeenCalledWith('Bleach');
  });

  it('renders previous attempts', () => {
    storeValue = {
      ...storeValue,
      gameState: baseState({
        guesses: [
          { title: 'Wrong', is_correct: false },
          { title: 'Right', is_correct: true },
        ],
      }),
    };
    renderPage();
    expect(screen.getByText('Wrong')).toBeInTheDocument();
    expect(screen.getByText('Right')).toBeInTheDocument();
  });

  it('renders the win state with video and replays', () => {
    storeValue = {
      ...storeValue,
      gameState: baseState({ gameOver: true, secret_title: 'Naruto', video_url: 'clip.mp4' }),
    };
    renderPage();
    expect(screen.getByText(/BIEN JOUÉ/i)).toBeInTheDocument();
    expect(screen.getByText(/Naruto/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Lecteur vidéo/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/REJOUER/i));
    expect(restartGame).toHaveBeenCalled();
  });
});
