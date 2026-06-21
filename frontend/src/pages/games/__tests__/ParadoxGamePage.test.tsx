import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ParadoxState } from '../../../types';
import ParadoxGamePage from '../ParadoxGamePage';

interface ParadoxStoreValue {
  gameState: ParadoxState | null;
  isLoading: boolean;
  error: string | null;
  loadGame: () => Promise<void>;
  submitGuess: (itemId: number) => Promise<void>;
}

const loadGame = vi.fn<() => Promise<void>>(() => Promise.resolve());
const submitGuess = vi.fn<(itemId: number) => Promise<void>>(() => Promise.resolve());
let storeValue: ParadoxStoreValue;

vi.mock('../../../features/games/stores/paradoxStore', () => ({
  useParadoxStore: () => storeValue,
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ParadoxGamePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const baseState = (over: Partial<ParadoxState> = {}): ParadoxState => ({
  gameOver: false,
  mediaType: 'anime',
  isDaily: false,
  items: [
    { id: 1, title: 'Alpha', image: 'a.jpg' },
    { id: 2, title: 'Beta', image: 'b.jpg' },
  ],
  ...over,
});

describe('ParadoxGamePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    storeValue = { gameState: baseState(), isLoading: false, error: null, loadGame, submitGuess };
  });

  it('loads the game on mount', () => {
    renderPage();
    expect(loadGame).toHaveBeenCalled();
  });

  it('renders the loading message', () => {
    storeValue = { gameState: null, isLoading: true, error: null, loadGame, submitGuess };
    renderPage();
    expect(screen.getByText(/faille temporelle/i)).toBeInTheDocument();
  });

  it('renders the error state and retries', () => {
    storeValue = { gameState: null, isLoading: false, error: 'boom', loadGame, submitGuess };
    renderPage();
    expect(screen.getByText(/PARADOXE INSTABLE/i)).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    fireEvent.click(screen.getByText(/RÉINITIALISER LE FLUX/i));
    // mount call + click call
    expect(loadGame).toHaveBeenCalledTimes(2);
  });

  it('renders nothing when there is no game state and not loading/error', () => {
    storeValue = { gameState: null, isLoading: false, error: null, loadGame, submitGuess };
    const { container } = renderPage();
    expect(container).toBeEmptyDOMElement();
  });

  it('renders selectable items and submits a guess on click', () => {
    renderPage();
    expect(screen.getByText('PARADOX')).toBeInTheDocument();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Sélectionner Beta'));
    expect(submitGuess).toHaveBeenCalledWith(2);
  });

  it('submits a guess via keyboard interaction', () => {
    renderPage();
    fireEvent.keyDown(screen.getByLabelText('Sélectionner Alpha'), { key: 'Enter' });
    expect(submitGuess).toHaveBeenCalledWith(1);
  });

  it('renders the win state and replays', () => {
    storeValue = {
      gameState: baseState({ gameOver: true }),
      isLoading: false,
      error: null,
      loadGame,
      submitGuess,
    };
    renderPage();
    expect(screen.getByText(/ANOMALIE RÉSOLUE/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/REJOUER/i));
    expect(loadGame).toHaveBeenCalledTimes(2);
  });
});
