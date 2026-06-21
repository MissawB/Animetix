import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import CatalogControls from '../CatalogControls';
import type { SortOption, ViewMode } from '../../types';

const sortOptions: SortOption[] = [
  { value: 'name', label: 'Nom' },
  { value: 'recent', label: 'Récent' },
];

interface Overrides {
  search?: string;
  sort?: string;
  viewMode?: ViewMode;
  showFilters?: boolean;
  hasActiveFilters?: boolean;
}

const renderControls = (overrides: Overrides = {}) => {
  const handlers = {
    onSearchChange: vi.fn(),
    onClearSearch: vi.fn(),
    onSortChange: vi.fn(),
    onToggleFilters: vi.fn(),
    onViewModeChange: vi.fn(),
    onClearFilters: vi.fn(),
  };
  render(
    <CatalogControls
      search={overrides.search ?? ''}
      sort={overrides.sort ?? 'name'}
      viewMode={overrides.viewMode ?? 'grid'}
      showFilters={overrides.showFilters ?? false}
      hasActiveFilters={overrides.hasActiveFilters ?? false}
      sortOptions={sortOptions}
      {...handlers}
    />,
  );
  return handlers;
};

describe('CatalogControls', () => {
  it('renders the sort options', () => {
    renderControls();
    expect(screen.getByText('Nom')).toBeInTheDocument();
    expect(screen.getByText('Récent')).toBeInTheDocument();
  });

  it('fires onSearchChange when typing in the search field', () => {
    const handlers = renderControls();
    const input = screen.getByLabelText('Rechercher un univers ou une cosmologie');
    fireEvent.change(input, { target: { value: 'nexus' } });
    expect(handlers.onSearchChange).toHaveBeenCalledWith('nexus');
  });

  it('hides the clear-search button when search is empty', () => {
    renderControls({ search: '' });
    // With empty search and no active filters, only sort/filter/view buttons exist.
    const buttons = screen.getAllByRole('button');
    expect(buttons.some((b) => b.id === 'view-grid')).toBe(true);
    expect(buttons).toHaveLength(3); // mobile filter toggle + grid + list
  });

  it('shows and fires the clear-search button when search has text', () => {
    const handlers = renderControls({ search: 'nexus' });
    const clearButtons = screen.getAllByRole('button');
    // The clear (X) button sits inside the search container as the first button.
    fireEvent.click(clearButtons[0]);
    expect(handlers.onClearSearch).toHaveBeenCalled();
  });

  it('fires onSortChange when selecting a sort option', () => {
    const handlers = renderControls();
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'recent' } });
    expect(handlers.onSortChange).toHaveBeenCalledWith('recent');
  });

  it('fires onViewModeChange for grid and list buttons', () => {
    const handlers = renderControls({ viewMode: 'list' });
    const buttons = screen.getAllByRole('button');
    const gridBtn = buttons.find((b) => b.id === 'view-grid');
    const listBtn = buttons.find((b) => b.id === 'view-list');
    fireEvent.click(gridBtn!);
    fireEvent.click(listBtn!);
    expect(handlers.onViewModeChange).toHaveBeenCalledWith('grid');
    expect(handlers.onViewModeChange).toHaveBeenCalledWith('list');
  });

  it('fires onToggleFilters when the mobile filter button is clicked', () => {
    const handlers = renderControls();
    fireEvent.click(screen.getByText('Filtres'));
    expect(handlers.onToggleFilters).toHaveBeenCalled();
  });

  it('does not render the reset button when there are no active filters', () => {
    renderControls({ hasActiveFilters: false });
    expect(screen.queryByText('Réinitialiser')).not.toBeInTheDocument();
  });

  it('renders and fires the reset button when filters are active', () => {
    const handlers = renderControls({ hasActiveFilters: true });
    fireEvent.click(screen.getByText('Réinitialiser'));
    expect(handlers.onClearFilters).toHaveBeenCalled();
  });
});
