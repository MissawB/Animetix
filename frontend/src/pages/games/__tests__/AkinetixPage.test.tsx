import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import type { MockInstance } from 'vitest';
import AkinetixPage from '../AkinetixPage';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <MemoryRouter>{children}</MemoryRouter>
  </QueryClientProvider>
);

describe('AkinetixPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        // The real API returns snake_case (the service normalizes it).
        json: () => Promise.resolve({
          history: [],
          current_question: "Est-ce un personnage masculin ?",
          game_over: false
        })
      } as Response);
  });

  it('gère une réponse OUI', async () => {
    render(<AkinetixPage />, { wrapper });
    
    // Attendre que le composant se charge
    const question = await screen.findByText(/Est-ce un personnage masculin/i);
    expect(question).toBeInTheDocument();

    // Mock pour la réponse suivante
    (global.fetch as unknown as MockInstance<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
            history: [{ q: "Est-ce un personnage masculin ?", a: "OUI" }],
            current_question: "A-t-il les cheveux blonds ?",
            game_over: false
        })
    } as Response);

    const yesButton = screen.getByText('common.yes');
    fireEvent.click(yesButton);

    await waitFor(() => {
        expect(screen.getByText(/A-t-il les cheveux blonds/i)).toBeInTheDocument();
    });
  });
});



