import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SocialDashboard from '../SocialDashboard';

// Mock du fetch global
global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ following: [], followers: [] }),
  })
);

describe('SocialDashboard', () => {
  it('affiche le titre du dashboard', async () => {
    render(<SocialDashboard />);
    const title = await screen.findByText(/Mes Abonnements/i);
    expect(title).toBeInTheDocument();
  });
});
