import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import VisionPage from '../VisionPage';

describe('VisionPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          image_url: 'test.jpg',
          best_score: 50,
          guesses: [{ text: 'Guerrier', score: 50 }],
          game_over: false
        })
      });
  });

  it('soumet une description et affiche le résultat', async () => {
    render(<VisionPage />);
    
    const input = await screen.findByPlaceholderText(/Décrivez l'image/i);
    const button = screen.getByText(/Analyser/i);

    fireEvent.change(input, { target: { value: 'Guerrier' } });
    fireEvent.click(button);

    await waitFor(() => {
        expect(screen.getByText('Guerrier')).toBeInTheDocument();
    });
  });
});
