import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import CovertestPage from '../CovertestPage';

// Mock du fetch global
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ 
        cover_url: '', 
        game_over: false, 
        guesses: [], 
        best_score: 0 
    }),
  })
);

describe('CovertestPage', () => {
  it('affiche le titre du jeu', async () => {
    render(<CovertestPage />);
    const title = await screen.findByText(/Deviner/i); // Adaptation du texte du composant
    expect(title).toBeInTheDocument();
  });
});
