import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ExplorePage from '../ExplorePage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('ExplorePage', () => {
  it('renders the explore page title and sections', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExplorePage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Tendances Actuelles/i)).toBeInTheDocument();
  });

  it('renders media type filters', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExplorePage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Animes/i)).toBeInTheDocument();
    expect(screen.getByText(/Mangas/i)).toBeInTheDocument();
  });
});
