import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import AdminGoldDatasetPage from '../AdminGoldDatasetPage';
import type { GoldDatasetEntry } from '../../../types';

const getList = vi.fn<() => Promise<GoldDatasetEntry[]>>();
const validateEntry = vi.fn<(id: number) => Promise<unknown>>();
const syncPositiveFeedback = vi.fn<() => Promise<unknown>>();
const deleteEntry = vi.fn<(id: number) => Promise<unknown>>();

vi.mock('../../../features/admin/services/goldDatasetService', () => ({
  goldDatasetService: {
    getList: () => getList(),
    validateEntry: (id: number) => validateEntry(id),
    syncPositiveFeedback: () => syncPositiveFeedback(),
    deleteEntry: (id: number) => deleteEntry(id),
  },
}));

// The page imports the shared queryClient singleton for invalidation.
vi.mock('../../../utils/queryClient', () => ({
  queryClient: {
    invalidateQueries: vi.fn().mockResolvedValue(undefined),
  },
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AdminGoldDatasetPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const makeEntry = (over: Partial<GoldDatasetEntry>): GoldDatasetEntry => ({
  id: 1,
  entry_type: 'qa',
  context: 'Some context input',
  instruction: 'Some instruction',
  response: 'The ideal response',
  metadata: {},
  is_validated: false,
  ai_validation_score: 0.9,
  ai_critique: null,
  confidence_score: 0.8,
  is_safe: true,
  created_at: '2024-03-01T00:00:00Z',
  ...over,
});

describe('AdminGoldDatasetPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the loading skeleton initially', () => {
    getList.mockReturnValue(new Promise(() => {}));
    const { container } = renderPage();
    // Loading branch renders only a centered skeleton, no header heading.
    expect(screen.queryByText('GOLD')).not.toBeInTheDocument();
    expect(container.querySelector('.p-20')).toBeInTheDocument();
  });

  it('renders the empty state when there are no entries', async () => {
    getList.mockResolvedValue([]);
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/Aucune donnée Gold en attente de curation/i),
      ).toBeInTheDocument();
    });
  });

  it('renders entry cards when data is loaded', async () => {
    getList.mockResolvedValue([
      makeEntry({ id: 7, response: 'Validated answer', is_validated: true }),
      makeEntry({ id: 8, response: 'Pending answer', is_validated: false }),
    ]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Validated answer')).toBeInTheDocument();
    });
    expect(screen.getByText('Pending answer')).toBeInTheDocument();
    expect(screen.getByText('#G-7')).toBeInTheDocument();
    expect(screen.getByText('#G-8')).toBeInTheDocument();
    expect(screen.getByText('VALIDÉ')).toBeInTheDocument();
    expect(screen.getByText('À CURER')).toBeInTheDocument();
  });

  it('triggers the validate mutation for a pending entry', async () => {
    getList.mockResolvedValue([makeEntry({ id: 8, is_validated: false })]);
    validateEntry.mockResolvedValue({});
    renderPage();

    await waitFor(() => expect(screen.getByText('APPROUVER')).toBeInTheDocument());
    fireEvent.click(screen.getByText('APPROUVER'));
    await waitFor(() => expect(validateEntry).toHaveBeenCalledWith(8));
  });

  it('triggers the sync mutation from the header button', async () => {
    getList.mockResolvedValue([]);
    syncPositiveFeedback.mockResolvedValue({});
    renderPage();

    await waitFor(() =>
      expect(screen.getByText(/Sync Positive Feedback/i)).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByText(/Sync Positive Feedback/i));
    await waitFor(() => expect(syncPositiveFeedback).toHaveBeenCalled());
  });

  it('deletes an entry only after the confirm dialog is accepted', async () => {
    getList.mockResolvedValue([makeEntry({ id: 8 })]);
    deleteEntry.mockResolvedValue({});
    const confirmMock = vi.fn().mockReturnValue(true);
    vi.stubGlobal('confirm', confirmMock);
    renderPage();

    await waitFor(() => expect(screen.getByText('SUPPRIMER')).toBeInTheDocument());
    fireEvent.click(screen.getByText('SUPPRIMER'));

    expect(confirmMock).toHaveBeenCalled();
    await waitFor(() => expect(deleteEntry).toHaveBeenCalledWith(8));
  });
});
