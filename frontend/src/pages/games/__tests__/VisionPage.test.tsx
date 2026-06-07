import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import VisionPage from '../VisionPage';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('VisionPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          image_url: 'test.jpg',
          best_score: 50,
          guesses: [{ text: 'Guerrier', score: 50 }],
          gameOver: false
        })
      } as Response);
  });

  it('soumet une description et affiche le résultat', async () => {
    render(<VisionPage />, { wrapper });
    
    // Correction du placeholder pour correspondre au composant
    const input = await screen.findByPlaceholderText(/Un guerrier aux cheveux noirs/i);
    const button = screen.getByText(/ANALYSER L'IMAGE/i);

    fireEvent.change(input, { target: { value: 'Guerrier' } });
    fireEvent.click(button);

    await waitFor(() => {
        expect(screen.getByText('Guerrier')).toBeInTheDocument();
    });
  });
});



