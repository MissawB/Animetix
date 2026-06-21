import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LogitLensHeatmap from '../LogitLensHeatmap';

interface LayerTrajectory {
  layer: number;
  top_tokens: string[];
  internal_probabilities: number[];
}

const trajectory: LayerTrajectory[] = [
  { layer: 0, top_tokens: ['the', 'a'], internal_probabilities: [0.9, 0.1] },
  { layer: 12, top_tokens: ['cat'], internal_probabilities: [0.6] },
];

describe('LogitLensHeatmap', () => {
  it('renders a zero-padded layer label for each layer', () => {
    render(<LogitLensHeatmap trajectory={trajectory} />);
    expect(screen.getByText('L00')).toBeInTheDocument();
    expect(screen.getByText('L12')).toBeInTheDocument();
  });

  it('renders the top tokens (including duplicated tooltip text)', () => {
    render(<LogitLensHeatmap trajectory={trajectory} />);
    // "the" appears both as the cell label and inside the hover tooltip.
    expect(screen.getAllByText('the').length).toBeGreaterThan(0);
    expect(screen.getAllByText('a').length).toBeGreaterThan(0);
    expect(screen.getAllByText('cat').length).toBeGreaterThan(0);
  });

  it('renders confidence percentages in the tooltip', () => {
    render(<LogitLensHeatmap trajectory={trajectory} />);
    expect(screen.getByText('90.0%')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
  });

  it('renders nothing in the grid for an empty trajectory', () => {
    render(<LogitLensHeatmap trajectory={[]} />);
    expect(screen.queryByText(/^L\d{2}$/)).not.toBeInTheDocument();
  });
});
