import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WorldBossPage from '../WorldBossPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('WorldBossPage', () => {
  it('renders the boss page structure', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <WorldBossPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    // Initially it might be loading or showing "No Active Boss" if fetch fails
    expect(screen.getByLabelText(/Loading Raid/i)).toBeInTheDocument();
  });
});



