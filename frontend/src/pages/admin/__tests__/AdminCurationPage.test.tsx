import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminCurationPage from '../AdminCurationPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('AdminCurationPage', () => {
  it('renders the curation center title', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AdminCurationPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    // Target the page heading specifically: /CURATION/i also matches raw i18n
    // keys elsewhere (the test i18n mock returns keys verbatim).
    expect(
      screen.getByRole('heading', { name: /CURATION CENTER/i }),
    ).toBeInTheDocument();
  });

  it('renders the tab buttons', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AdminCurationPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(screen.getByText(/DPO Feedback/i)).toBeInTheDocument();
    expect(screen.getByText(/Graph Healer/i)).toBeInTheDocument();
  });
});
