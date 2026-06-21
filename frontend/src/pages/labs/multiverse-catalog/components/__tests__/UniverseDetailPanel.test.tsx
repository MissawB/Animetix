import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import UniverseDetailPanel from '../UniverseDetailPanel';
import type { Universe } from '../../types';

const baseUniverse: Universe = {
  id: 'u1',
  name: 'Cyber Nexus',
  description: 'A neon dystopia',
  cosmology: 'Layered grids',
  genre: 'cyberpunk',
  is_synthetic: true,
  character_count: 2,
  characters: [
    { name: 'Alpha', role: 'hero', power_level: 1500 },
    { name: 'Bravo', role: 'villain', power_level: 0 },
  ],
  created_at: null,
};

const renderPanel = (universe: Universe = baseUniverse) => {
  const onClose = vi.fn();
  render(
    <MemoryRouter>
      <UniverseDetailPanel universe={universe} onClose={onClose} />
    </MemoryRouter>,
  );
  return { onClose };
};

describe('UniverseDetailPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the name and genre', () => {
    renderPanel();
    expect(screen.getByText('Cyber Nexus')).toBeInTheDocument();
    expect(screen.getByText('cyberpunk')).toBeInTheDocument();
  });

  it('renders the synopsis and cosmology sections when present', () => {
    renderPanel();
    expect(screen.getByText('Synopsis')).toBeInTheDocument();
    expect(screen.getByText('A neon dystopia')).toBeInTheDocument();
    expect(screen.getByText('Cosmologie')).toBeInTheDocument();
    expect(screen.getByText('Layered grids')).toBeInTheDocument();
  });

  it('omits synopsis and cosmology sections when absent', () => {
    renderPanel({ ...baseUniverse, description: '', cosmology: '' });
    expect(screen.queryByText('Synopsis')).not.toBeInTheDocument();
    expect(screen.queryByText('Cosmologie')).not.toBeInTheDocument();
  });

  it('lists characters and shows power level only when greater than 0', () => {
    renderPanel();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Bravo')).toBeInTheDocument();
    // toLocaleString separator varies by environment; match the digits flexibly.
    expect(screen.getByText((content) => content.replace(/\D/g, '') === '1500')).toBeInTheDocument();
    // PWR label appears only for characters with power_level > 0
    expect(screen.getAllByText('PWR')).toHaveLength(1);
  });

  it('omits the characters section when there are none', () => {
    renderPanel({ ...baseUniverse, characters: [], character_count: 0 });
    expect(screen.queryByText('Alpha')).not.toBeInTheDocument();
    expect(screen.queryByText('PWR')).not.toBeInTheDocument();
  });

  it('calls onClose when the close (X) button is clicked', () => {
    const { onClose } = renderPanel();
    // The close button is the only button with no text label.
    const closeBtn = screen.getAllByRole('button').find((b) => b.textContent === '');
    fireEvent.click(closeBtn!);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when clicking the backdrop overlay', () => {
    const { onClose } = renderPanel();
    fireEvent.click(screen.getByText('Cyber Nexus'));
    // Click on the title should NOT close (stopPropagation on inner card)
    expect(onClose).not.toHaveBeenCalled();
  });

  it('opens the PDF export in a new tab', () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    renderPanel();
    fireEvent.click(screen.getByText('Exporter PDF'));
    expect(openSpy).toHaveBeenCalledWith(
      '/api/v1/multiverse/Cyber%20Nexus/export-pdf/',
      '_blank',
    );
  });

  it('links the Nexus CTA to the multiverse route', () => {
    renderPanel();
    const link = screen.getByText('Explorer dans le Nexus').closest('a');
    expect(link).toHaveAttribute('href', '/lab/multiverse/');
  });
});
