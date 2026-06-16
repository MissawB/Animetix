import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GenesisToolbox } from '../GenesisToolbox';

describe('GenesisToolbox', () => {
  it('renders all seeds', () => {
    render(<GenesisToolbox />);
    expect(screen.getByText(/Cyberpunk/i)).toBeInTheDocument();
    expect(screen.getByText(/Fantasy/i)).toBeInTheDocument();
    expect(screen.getByText(/Sci-Fi/i)).toBeInTheDocument();
    expect(screen.getByText(/Steampunk/i)).toBeInTheDocument();
  });

  it('sets dataTransfer seed on drag start', () => {
    render(<GenesisToolbox />);
    
    const seed = screen.getByText(/Cyberpunk/i).closest('div');
    const dataTransfer = {
      setData: vi.fn(),
    };

    fireEvent.dragStart(seed!, { dataTransfer });

    expect(dataTransfer.setData).toHaveBeenCalledWith('seed', 'Cyberpunk');
  });
});
