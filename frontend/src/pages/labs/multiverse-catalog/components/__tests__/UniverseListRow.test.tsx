import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import UniverseListRow from '../UniverseListRow';
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
    { name: 'Echo', role: 'extra', power_level: 60 },
  ],
  created_at: null,
};

describe('UniverseListRow', () => {
  it('renders the universe name, genre and entity count', () => {
    render(<UniverseListRow universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('Cyber Nexus')).toBeInTheDocument();
    expect(screen.getByText('cyberpunk')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('renders the description when present', () => {
    render(<UniverseListRow universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('A neon dystopia')).toBeInTheDocument();
  });

  it('falls back to cosmology when description is empty', () => {
    const universe: Universe = { ...baseUniverse, description: '' };
    render(<UniverseListRow universe={universe} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('Layered grids')).toBeInTheDocument();
  });

  it('falls back to default text when description and cosmology are empty', () => {
    const universe: Universe = { ...baseUniverse, description: '', cosmology: '' };
    render(<UniverseListRow universe={universe} index={0} onSelect={vi.fn()} />);
    expect(screen.getByText('Univers généré par intelligence artificielle')).toBeInTheDocument();
  });

  it('shows at most 4 character avatars', () => {
    render(<UniverseListRow universe={baseUniverse} index={0} onSelect={vi.fn()} />);
    expect(screen.getByTitle('Alpha')).toBeInTheDocument();
    expect(screen.getByTitle('Delta')).toBeInTheDocument();
    expect(screen.queryByTitle('Echo')).not.toBeInTheDocument();
  });

  it('calls onSelect with the universe when clicked', () => {
    const onSelect = vi.fn();
    render(<UniverseListRow universe={baseUniverse} index={0} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('Cyber Nexus'));
    expect(onSelect).toHaveBeenCalledWith(baseUniverse);
  });
});
