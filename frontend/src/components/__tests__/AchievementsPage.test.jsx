import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import AchievementsPage from '../AchievementsPage';

describe('AchievementsPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      })
    );
  });

  it('affiche le titre du grimoire', async () => {
    render(<AchievementsPage />);
    const titleElement = await screen.findByText(/Grimoire des Hauts Faits/i);
    expect(titleElement).toBeInTheDocument();
  });
});
