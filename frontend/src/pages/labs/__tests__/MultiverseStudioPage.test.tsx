import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import MultiverseStudioPage from '../MultiverseStudioPage';

// react-query: provide a resolved, empty graph so the page renders its shell
// without hitting the network.
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: { nodes: [], links: [] },
    isLoading: false,
    isFetching: false,
  })),
  useMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

// Stub the heavy canvas/force-graph children — out of scope for a page smoke test.
vi.mock('../../../features/labs/components/Multiverse/NexusMap', () => ({
  NexusMap: () => <div data-testid="nexus-map" />,
}));
vi.mock('../../../features/labs/components/Multiverse/GenesisToolbox', () => ({
  GenesisToolbox: () => <div data-testid="genesis-toolbox" />,
}));

// Mock framer-motion to avoid animation issues in tests.
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => <div {...props}>{children}</div>,
    h2: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLHeadingElement>>) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLParagraphElement>>) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren<unknown>) => <>{children}</>,
}));

describe('MultiverseStudioPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the Nexus map studio shell', () => {
    render(
      <MemoryRouter>
        <MultiverseStudioPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/Nexus Map/i)).toBeInTheDocument();
    expect(screen.getByTestId('nexus-map')).toBeInTheDocument();
  });
});
