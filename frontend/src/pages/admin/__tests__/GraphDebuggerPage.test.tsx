import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GraphDebuggerPage from '../GraphDebuggerPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';

const mockApiClient = vi.fn();
vi.mock('../../../utils/apiClient', () => ({
  apiClient: (url: string, init?: RequestInit) => mockApiClient(url, init),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('GraphDebuggerPage', () => {
  beforeEach(() => {
    queryClient.clear();
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <GraphDebuggerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Auditing Knowledge Graph.../i)).toBeInTheDocument();
  });

  it('renders stats dashboard when data is fetched', async () => {
    const mockAudit = {
      status: 'success',
      isolated_nodes: 12,
      temporal_conflicts: 3,
      orphan_entities: 45,
      duplicate_entities: 14,
      details: [
        { t1: 'Sequel Anime', y1: 2024, t2: 'Prequel Anime', y2: 2025 }
      ]
    };

    mockApiClient.mockResolvedValue(mockAudit);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <GraphDebuggerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.queryByText(/Auditing Knowledge Graph.../i)).not.toBeInTheDocument();
      expect(screen.getByText('GRAPH')).toBeInTheDocument();
      expect(screen.getByText('HEALER')).toBeInTheDocument();
      
      // Check for stats counts
      expect(screen.getByText('12')).toBeInTheDocument(); // isolated nodes
      expect(screen.getByText('3')).toBeInTheDocument();  // conflicts
      expect(screen.getByText('45')).toBeInTheDocument(); // orphans
      expect(screen.getByText('14')).toBeInTheDocument(); // duplicates

      // Check conflict details
      expect(screen.getByText('Sequel Anime')).toBeInTheDocument();
      expect(screen.getByText('Prequel Anime')).toBeInTheDocument();
    });
  });

  it('triggers cleanup mutation when EXECUTE CLEANUP is clicked', async () => {
    const mockAudit = {
      status: 'success',
      isolated_nodes: 0,
      temporal_conflicts: 0,
      orphan_entities: 0,
      duplicate_entities: 0,
      details: []
    };

    mockApiClient.mockResolvedValue(mockAudit);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <GraphDebuggerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('EXECUTE CLEANUP')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('EXECUTE CLEANUP'));

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith('/api/v1/graph/debugger/', {
        method: 'POST',
        body: JSON.stringify({ action: 'cleanup' })
      });
    });
  });

  it('triggers merge duplicates mutation when MERGE DUPLICATES is clicked', async () => {
    const mockAudit = {
      status: 'success',
      isolated_nodes: 0,
      temporal_conflicts: 0,
      orphan_entities: 0,
      duplicate_entities: 5,
      details: []
    };

    mockApiClient.mockResolvedValue(mockAudit);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <GraphDebuggerPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('MERGE DUPLICATES')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('MERGE DUPLICATES'));

    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith('/api/v1/graph/debugger/', {
        method: 'POST',
        body: JSON.stringify({ action: 'merge_duplicates' })
      });
    });
  });
});
