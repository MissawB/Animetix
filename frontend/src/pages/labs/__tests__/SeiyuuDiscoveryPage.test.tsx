import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { apiClient } from '../../../utils/apiClient';
import SeiyuuDiscoveryPage from '../SeiyuuDiscoveryPage';

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));
const mockedApiClient = vi.mocked(apiClient);

const mockSeiyuuData = {
  query: '',
  results: [
    {
      id: 1,
      name: 'Rie Takahashi',
      language: 'japanese',
      origin: 'dataset',
      definition: 'Famous voice actor for Megumin and Emilia.',
      roles: 'Megumin, Emilia, Hu Tao',
      impact: 'Top Tier',
      origin_detail: 'https://huggingface.co/datasets/seiyuu',
      sample_url: 'https://example.com/samples/rie.mp3',
    },
    {
      id: 2,
      name: 'Donald Reignoux',
      language: 'french',
      origin: 'youtube',
      definition: 'Voix française iconique de Titeuf et Sora.',
      roles: 'Titeuf, Sora, Spider-Man',
      impact: 'High',
      origin_detail: 'https://youtube.com/watch?v=123',
      sample_url: 'https://example.com/samples/donald.mp3',
    },
  ],
};

const renderPage = () => {
  const qc = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SeiyuuDiscoveryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('SeiyuuDiscoveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders title and fetches seiyuu profiles on mount', async () => {
    mockedApiClient.mockResolvedValue(mockSeiyuuData);

    renderPage();

    expect(screen.getByText('SEIYUU')).toBeInTheDocument();
    expect(screen.getByText('DISCOVERY')).toBeInTheDocument();

    expect(await screen.findByText('Rie Takahashi')).toBeInTheDocument();
    expect(screen.getByText('Donald Reignoux')).toBeInTheDocument();
    expect(screen.getByText('Megumin')).toBeInTheDocument();
    expect(screen.getByText('Emilia')).toBeInTheDocument();
  });

  it('opens and submits YouTube ingestion form', async () => {
    mockedApiClient.mockImplementation((url: string) => {
      if (url.includes('/ingest/')) {
        return Promise.resolve({
          profile: { name: 'Donald Reignoux' },
        });
      }
      return Promise.resolve(mockSeiyuuData);
    });

    renderPage();

    // Toggle Ingestion panel
    const toggleBtn = screen.getByRole('button', { name: /Ingestion YouTube/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByText(/Ingestion et extraction vocale/i)).toBeInTheDocument();

    // Fill form
    const nameInput = screen.getByLabelText(/Nom du doubleur ou seiyuu/i);
    const sourceInput = screen.getByLabelText(/URL YouTube ou requête de recherche/i);

    fireEvent.change(nameInput, { target: { value: 'Donald Reignoux' } });
    fireEvent.change(sourceInput, { target: { value: 'https://youtube.com/watch?v=123' } });

    const submitBtn = screen.getByRole('button', { name: /Lancer l'ingestion/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/labs/audio/seiyuu/ingest/', {
        method: 'POST',
        body: JSON.stringify({
          name: 'Donald Reignoux',
          language: 'japanese',
          query: 'https://youtube.com/watch?v=123',
          definition: '',
          roles: '',
        }),
      });
    });
  });

  it('filters results by language when language filter button is clicked', async () => {
    mockedApiClient.mockResolvedValue(mockSeiyuuData);

    renderPage();

    expect(await screen.findByText('Rie Takahashi')).toBeInTheDocument();

    const frFilterBtn = screen.getByRole('button', { name: /Français \(Doubleur\)/i });
    fireEvent.click(frFilterBtn);

    await waitFor(() => {
      expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/labs/audio/seiyuu/?q=&language=french');
    });
  });
});
