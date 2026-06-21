import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GameHistoryPanel } from '../GameHistoryPanel';

interface GameSession {
  id: number;
  game_mode: string;
  media_type: string;
  target_item: string;
  was_won: boolean;
  history: Record<string, unknown>[];
  created_at: string;
}

interface QueryResult {
  data: GameSession[] | undefined;
  isLoading: boolean;
  isError: boolean;
}

let queryResult: QueryResult = { data: undefined, isLoading: true, isError: false };

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => queryResult,
}));

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../../../components/ui/Card', () => ({
  Card: ({ children }: React.PropsWithChildren<unknown>) => <div>{children}</div>,
}));

describe('GameHistoryPanel', () => {
  beforeEach(() => {
    queryResult = { data: undefined, isLoading: true, isError: false };
  });

  it('renders a loading skeleton while loading', () => {
    const { container } = render(<GameHistoryPanel />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders an error message on failure', () => {
    queryResult = { data: undefined, isLoading: false, isError: true };
    render(<GameHistoryPanel />);
    expect(screen.getByText(/Impossible de charger/)).toBeInTheDocument();
  });

  it('renders an empty state when there are no sessions', () => {
    queryResult = { data: [], isLoading: false, isError: false };
    render(<GameHistoryPanel />);
    expect(screen.getByText('Aucune partie jouée récemment.')).toBeInTheDocument();
  });

  it('renders session rows with target, mode and turn count', () => {
    queryResult = {
      isLoading: false,
      isError: false,
      data: [
        {
          id: 1,
          game_mode: 'CLASSIC',
          media_type: 'Anime',
          target_item: 'Naruto',
          was_won: true,
          history: [{}, {}, {}],
          created_at: '2026-01-01T00:00:00Z',
        },
        {
          id: 2,
          game_mode: 'VS',
          media_type: 'Manga',
          target_item: 'Goku',
          was_won: false,
          history: [],
          created_at: '2026-01-02T00:00:00Z',
        },
      ],
    };
    render(<GameHistoryPanel />);
    expect(screen.getByText('Naruto')).toBeInTheDocument();
    expect(screen.getByText('Goku')).toBeInTheDocument();
    expect(screen.getByText('CLASSIC')).toBeInTheDocument();
    expect(screen.getByText('3 Tours')).toBeInTheDocument();
    expect(screen.getByText('0 Tours')).toBeInTheDocument();
  });
});
