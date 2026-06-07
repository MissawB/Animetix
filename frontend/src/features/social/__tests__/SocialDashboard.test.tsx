import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SocialDashboard from '../SocialDashboard';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

// Mock du fetch global
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ following: [], followers: [] }),
  }) as Promise<Response>
);

describe('SocialDashboard', () => {
  it('affiche le titre du dashboard', async () => {
    render(<SocialDashboard />, { wrapper });
    const title = await screen.findByText('social.dashboard.following_title');
    expect(title).toBeInTheDocument();
  });
});
