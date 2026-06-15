import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GenesisToolbox } from '../GenesisToolbox';

describe('GenesisToolbox', () => {
  it('renders all seeds', () => {
    render(<GenesisToolbox onDragStart={vi.fn()} />);
    
    expect(screen.getByText('Genesis Seeds')).toBeDefined();
    expect(screen.getByText('Cyberpunk')).toBeDefined();
    expect(screen.getByText('Fantasy')).toBeDefined();
    expect(screen.getByText('Sci-Fi')).toBeDefined();
    expect(screen.getByText('Steampunk')).toBeDefined();
  });

  it('triggers onDragStart when a seed is dragged', () => {
    const onDragStart = vi.fn();
    render(<GenesisToolbox onDragStart={onDragStart} />);
    
    const cyberpunkSeed = screen.getByText('Cyberpunk').parentElement!;
    
    const dataTransfer = {
      setData: vi.fn(),
    };
    
    fireEvent.dragStart(cyberpunkSeed, { dataTransfer });
    
    expect(dataTransfer.setData).toHaveBeenCalledWith('seed', 'Cyberpunk');
    expect(onDragStart).toHaveBeenCalledWith('Cyberpunk');
  });
});
