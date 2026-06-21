import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import EntropyBarChart from '../EntropyBarChart';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => (
      <div {...props}>{children}</div>
    ),
  },
}));

interface TokenDiagnostic {
  token: string;
  entropy: number;
}

const data: TokenDiagnostic[] = [
  { token: 'low', entropy: 0.2 },
  { token: 'mid', entropy: 1.0 },
  { token: 'high', entropy: 2.5 },
];

describe('EntropyBarChart', () => {
  it('renders the token labels for each bar', () => {
    render(<EntropyBarChart data={data} />);
    // Each token appears as an axis label and inside the hover tooltip.
    expect(screen.getAllByText('low').length).toBeGreaterThan(0);
    expect(screen.getAllByText('mid').length).toBeGreaterThan(0);
    expect(screen.getAllByText('high').length).toBeGreaterThan(0);
  });

  it('renders the entropy value in each tooltip', () => {
    render(<EntropyBarChart data={data} />);
    expect(screen.getByText('Entropy: 0.2000 bits')).toBeInTheDocument();
    expect(screen.getByText('Entropy: 2.5000 bits')).toBeInTheDocument();
  });

  it('renders no bars for empty data', () => {
    render(<EntropyBarChart data={[]} />);
    expect(screen.queryByText(/Entropy:/)).not.toBeInTheDocument();
  });
});
