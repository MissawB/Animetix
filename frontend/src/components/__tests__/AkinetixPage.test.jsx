import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import AkinetixPage from '../AkinetixPage';

describe('AkinetixPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          history: [],
          current_question: "Est-ce un personnage masculin ?",
          game_over: false
        })
      });
  });

  it('gère une réponse OUI', async () => {
    render(<AkinetixPage />);
    
    // Attendre que le composant se charge
    const question = await screen.findByText(/Est-ce un personnage masculin/i);
    expect(question).toBeInTheDocument();

    // Mock pour la réponse suivante
    global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
            history: [{ q: "Est-ce un personnage masculin ?", a: "OUI" }],
            current_question: "A-t-il les cheveux blonds ?",
            game_over: false
        })
    });

    const yesButton = screen.getByText('OUI');
    fireEvent.click(yesButton);

    await waitFor(() => {
        expect(screen.getByText(/A-t-il les cheveux blonds/i)).toBeInTheDocument();
    });
  });
});
