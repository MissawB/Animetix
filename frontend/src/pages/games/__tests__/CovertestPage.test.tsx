import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import CovertestPage from '../CovertestPage';
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

describe('CovertestPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ 
            cover_url: '', 
            gameOver: false, 
            guesses: [], 
            best_score: 0 
        }),
      }) as Promise<Response>
    );
  });

  it('affiche le titre du jeu', async () => {
    render(<CovertestPage />, { wrapper });
    const title = await screen.findByText(/DEVINER/i);
    expect(title).toBeInTheDocument();
  });
});



