import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import VsBattlePage from '../VsBattlePage';

// Characterization test written BEFORE the decomposition of the 647-line page
// (it had none) — locks the observable behaviour so the extraction of
// FighterSlot / roster / result / arena / how-it-works stays behaviour-neutral.

const mockGetCharacters = vi.fn();
const mockGetArenaFeed = vi.fn();
vi.mock('../../../features/games/services/vsBattleService', () => ({
  vsBattleService: {
    getCharacters: () => mockGetCharacters(),
    getArenaFeed: () => mockGetArenaFeed(),
    runBattle: vi.fn(),
    likeBattle: vi.fn(),
  },
}));

// The page imports the app's queryClient singleton (persister-wired with
// idb-keyval, which needs indexedDB — absent in jsdom). Stub it.
vi.mock('../../../utils/queryClient', () => ({
  queryClient: { invalidateQueries: vi.fn() },
}));

const CHARS = [
  { name: 'Goku', franchise: 'Dragon Ball', image: 'g.png', source: 'wiki' as const },
  { name: 'Saitama', franchise: 'One Punch Man', image: 's.png', source: 'synthetic' as const },
];

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <VsBattlePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('VsBattlePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetCharacters.mockResolvedValue(CHARS);
    mockGetArenaFeed.mockResolvedValue([]);
  });

  it('renders the arena header and the two empty challenger slots', () => {
    renderPage();
    expect(screen.getByText(/ULTIMATUM/i)).toBeInTheDocument();
    expect(screen.getByText(/Challenger A/i)).toBeInTheDocument();
    expect(screen.getByText(/Challenger B/i)).toBeInTheDocument();
  });

  it('renders the "how it works" explainer', () => {
    renderPage();
    expect(screen.getByText(/Comment fonctionne l.Arène/i)).toBeInTheDocument();
  });

  it('loads the roster and fills slot A when a character is picked', async () => {
    const user = userEvent.setup();
    renderPage();

    // Roster button carries a title "name — franchise".
    const gokuCard = await screen.findByTitle('Goku — Dragon Ball');
    await user.click(gokuCard);

    // Slot A now shows the picked fighter (name appears in the slot too).
    expect(screen.getAllByText('Goku').length).toBeGreaterThan(0);
    // The synthetic character carries the AI badge in the roster.
    expect(screen.getByText(/^IA$/)).toBeInTheDocument();
  });
});
