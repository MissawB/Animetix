import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CurationDashboard from '../CurationDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('CurationDashboard', () => {
  it('renders the curation dashboard title', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CurationDashboard />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Data/i)).toBeInTheDocument();
    expect(screen.getByText(/Curation/i)).toBeInTheDocument();
  });

  it('shows empty state when no ticket is selected', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CurationDashboard />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/Select a ticket to inspect/i)).toBeInTheDocument();
  });
});



