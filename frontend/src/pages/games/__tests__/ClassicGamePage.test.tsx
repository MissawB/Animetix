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
  isGuessing: boolean;
  revealHint: (key: string) => Promise<void>;
  revealingHint: boolean;
  startGame: (arg: unknown) => Promise<void>;
  starting: boolean;
  restart: () => void;
}

const handleGuess = vi.fn<(arg: { guess: string }) => Promise<void>>(() => Promise.resolve());
const revealHint = vi.fn<(key: string) => Promise<void>>(() => Promise.resolve());
const startGame = vi.fn<(arg: unknown) => Promise<void>>(() => Promise.resolve());
const restart = vi.fn();
let hookValue: ClassicGameHook;

const makeHook = (over: Partial<ClassicGameHook> = {}): ClassicGameHook => ({
  gameState: baseState(),
  loading: false,
  handleGuess,
  isGuessing: false,
  revealHint,
  revealingHint: false,
  startGame,
  starting: false,
  restart,
  ...over,
});

// Catalogue des titres : évite un appel réseau pendant le rendu de test.
vi.mock('../../../features/games/services/classicService', () => ({
  classicGameService: { getTitles: () => Promise.resolve([]) },
}));

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
    hookValue = makeHook();
  });

  it('renders a skeleton while loading', () => {
    hookValue = makeHook({ gameState: undefined, loading: true });
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders nothing when there is no game state', () => {
    hookValue = makeHook({ gameState: undefined });
    const { container } = renderPage();
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the guess form and empty trail when active', () => {
    renderPage();
    expect(screen.getByText(/CLASSIC/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Entrez un titre/i)).toBeInTheDocument();
    expect(screen.getByText(/Aucune piste/i)).toBeInTheDocument();
  });

  it('submits a guess and clears the input', async () => {
    renderPage();
    const input = screen.getByPlaceholderText(/Entrez un titre/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Naruto' } });
    fireEvent.click(screen.getByText(/ENVOYER/i));
    await waitFor(() => expect(handleGuess).toHaveBeenCalledWith({ guess: 'Naruto' }));
  });

  it('renders previous guesses with proximity heat and a found marker', () => {
    hookValue = makeHook({
      gameState: baseState({
        guesses: [
          { title: 'One Piece', is_correct: false, score: 35, color: 'secondary' },
          { title: 'Bleach', is_correct: true, score: 100, color: 'danger' },
        ],
      }),
    });
    renderPage();
    expect(screen.getByText('One Piece')).toBeInTheDocument();
    expect(screen.getByText('35%')).toBeInTheDocument();
    expect(screen.getByText(/Trouvé/i)).toBeInTheDocument();
  });

  it('reveals a hint once it is unlockable', () => {
    hookValue = makeHook({
      gameState: baseState({
        guess_count: 5,
        hints: {
          origin: {
            label: 'Origine / Année',
            unlocks_at: 5,
            can_reveal: true,
            revealed: false,
            value: null,
          },
          tags: { label: 'Tags', unlocks_at: 10, can_reveal: false, revealed: false, value: null },
          studio: {
            label: 'Studio',
            unlocks_at: 15,
            can_reveal: false,
            revealed: false,
            value: null,
          },
          desc: {
            label: 'Description',
            unlocks_at: 20,
            can_reveal: false,
            revealed: false,
            value: null,
          },
        },
      }),
    });
    renderPage();
    fireEvent.click(screen.getByText(/Révéler/i));
    expect(revealHint).toHaveBeenCalledWith('origin');
  });

  it('renders the victory state and replays on demand', () => {
    hookValue = makeHook({ gameState: baseState({ gameOver: true, secret_title: 'Death Note' }) });
    renderPage();
    expect(screen.getByText(/Œuvre démasquée/i)).toBeInTheDocument();
    expect(screen.getByText(/Death Note/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Rejouer/i));
    expect(startGame).toHaveBeenCalled();
  });

  it('affiche ce qui a rapproché une proposition chaude', () => {
    hookValue = makeHook({
      gameState: baseState({
        guesses: [
          {
            title: 'MONSTER',
            score: 92.3,
            color: 'success',
            is_correct: false,
            reasons: [
              { kind: 'public', label: "C'est le public qui vous rapproche", detail: [] },
              { kind: 'tags', label: '2 tag(s) partagé(s)', detail: ['Detective', 'Philosophy'] },
            ],
          },
        ],
      }),
    });
    renderPage();
    expect(screen.getByText(/le public qui vous rapproche/i)).toBeInTheDocument();
    expect(screen.getByText(/Detective/)).toBeInTheDocument();
  });

  it("n'affiche rien pour une proposition froide", () => {
    hookValue = makeHook({
      gameState: baseState({
        guesses: [
          {
            title: 'Kimetsu no Yaiba',
            score: 12,
            color: 'secondary',
            is_correct: false,
            reasons: [],
          },
        ],
      }),
    });
    renderPage();
    expect(screen.getByText('Kimetsu no Yaiba')).toBeInTheDocument();
    expect(screen.queryByText(/rapproche/i)).not.toBeInTheDocument();
  });

  it('survit à une charge utile sans le champ reasons', () => {
    hookValue = makeHook({
      gameState: baseState({
        guesses: [{ title: 'BLEACH', score: 40, color: 'warning', is_correct: false }],
      }),
    });
    renderPage();
    expect(screen.getByText('BLEACH')).toBeInTheDocument();
  });
});
