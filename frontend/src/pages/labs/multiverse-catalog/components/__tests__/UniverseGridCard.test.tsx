import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import UniverseGridCard from '../UniverseGridCard';
import type { Universe } from '../../types';

const baseUniverse: Universe = {
  id: 'u1',
  name: 'Cyber Nexus',
  description: 'A neon dystopia',
  cosmology: 'Layered grids',
  genre: 'cyberpunk',
  is_synthetic: true,
  character_count: 5,
  characters: [
    { name: 'Alpha', role: 'hero', power_level: 100 },
    { name: 'Bravo', role: 'villain', power_level: 90 },
    { name: 'Charlie', role: 'ally', power_level: 80 },
    { name: 'Delta', role: 'ally', power_level: 70 },
  ],
  created_at: null,
};

describe('UniverseGridCard', () => {
  it('renders the name, genre and entity count', () => {
    render(<UniverseGridCard universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('Cyber Nexus')).toBeInTheDocument();
    expect(screen.getByText('cyberpunk')).toBeInTheDocument();
    expect(screen.getByText('5 entités')).toBeInTheDocument();
  });

  it('renders the description when present', () => {
    render(<UniverseGridCard universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('A neon dystopia')).toBeInTheDocument();
  });

  it('falls back to default text when no description or cosmology', () => {
    const universe: Universe = { ...baseUniverse, description: '', cosmology: '' };
    render(<UniverseGridCard universe={universe} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('Univers synthétique généré par IA')).toBeInTheDocument();
  });

  it('shows the first 3 avatars and a +N overflow indicator', () => {
    render(<UniverseGridCard universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByTitle('Alpha')).toBeInTheDocument();
    expect(screen.getByTitle('Charlie')).toBeInTheDocument();
    expect(screen.queryByTitle('Delta')).not.toBeInTheDocument();
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('omits the avatar block when there are no characters', () => {
    const universe: Universe = { ...baseUniverse, characters: [], character_count: 0 };
    render(<UniverseGridCard universe={universe} index={0} onSelect={vi.fn()} />);
    expect(screen.queryByTitle('Alpha')).not.toBeInTheDocument();
    expect(screen.queryByText(/^\+/)).not.toBeInTheDocument();
  });

  it('calls onSelect when the card is clicked', () => {
    const onSelect = vi.fn();
    render(<UniverseGridCard universe={baseUniverse} index={0} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('Cyber Nexus'));
    expect(onSelect).toHaveBeenCalledWith(baseUniverse);
  });
});
