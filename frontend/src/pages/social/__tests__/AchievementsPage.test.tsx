import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import AchievementsPage from '../AchievementsPage';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('AchievementsPage', () => {
  beforeAll(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      }) as Promise<Response>
    );
  });

  it('affiche le titre du grimoire', async () => {
    render(<AchievementsPage />, { wrapper });
    const titleElement = await screen.findByText(/Grimoire des Hauts Faits/i);
    expect(titleElement).toBeInTheDocument();
  });
});



