import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import GenreSidebar from '../GenreSidebar';
import type { GenreOption } from '../../types';

const genres: GenreOption[] = [
  { name: 'Cyberpunk', count: 12 },
  { name: 'Fantasy', count: 7 },
];

interface Overrides {
  showFilters?: boolean;
  genre?: string;
  total?: number | undefined;
  availableGenres?: GenreOption[] | undefined;
}

const renderSidebar = (overrides: Overrides = {}) => {
  const onSelectGenre = vi.fn();
  render(
    <MemoryRouter>
      <GenreSidebar
        showFilters={overrides.showFilters ?? true}
        genre={overrides.genre ?? ''}
        total={'total' in overrides ? overrides.total : 19}
        availableGenres={'availableGenres' in overrides ? overrides.availableGenres : genres}
        onSelectGenre={onSelectGenre}
      />
    </MemoryRouter>,
  );
  return { onSelectGenre };
};

describe('GenreSidebar', () => {
  it('renders the "all genres" entry with the total count', () => {
    renderSidebar();
    expect(screen.getByText('Tous les genres')).toBeInTheDocument();
    expect(screen.getByText('19')).toBeInTheDocument();
  });

  it('renders 0 when total is undefined', () => {
    renderSidebar({ total: undefined });
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders each available genre with its count', () => {
    renderSidebar();
    expect(screen.getByText('Cyberpunk')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Fantasy')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('handles an undefined genre list without crashing', () => {
    renderSidebar({ availableGenres: undefined });
    expect(screen.queryByText('Cyberpunk')).not.toBeInTheDocument();
    expect(screen.getByText('Tous les genres')).toBeInTheDocument();
  });

  it('calls onSelectGenre with an empty string when "all genres" is clicked', () => {
    const { onSelectGenre } = renderSidebar({ genre: 'Cyberpunk' });
    fireEvent.click(screen.getByText('Tous les genres'));
    expect(onSelectGenre).toHaveBeenCalledWith('');
  });

  it('calls onSelectGenre with the genre name when a genre is clicked', () => {
    const { onSelectGenre } = renderSidebar();
    fireEvent.click(screen.getByText('Cyberpunk'));
    expect(onSelectGenre).toHaveBeenCalledWith('Cyberpunk');
  });

  it('links to the Nexus map', () => {
    renderSidebar();
    const link = screen.getByText('Nexus Map').closest('a');
    expect(link).toHaveAttribute('href', '/lab/multiverse/');
  });
});
