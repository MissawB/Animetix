import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { ExploreToolbar } from '../ExploreToolbar';

const baseProps = {
  mediaType: 'Anime',
  onMediaTypeChange: vi.fn(),
  query: '',
  onQueryChange: vi.fn(),
  genres: ['Action', 'Romance'],
  selectedGenres: new Set<string>(),
  onToggleGenre: vi.fn(),
};

const renderToolbar = (props = baseProps) =>
  render(
    <MemoryRouter>
      <ExploreToolbar {...props} />
    </MemoryRouter>,
  );

beforeEach(() => vi.clearAllMocks());

it('changes media type when a tab is clicked', () => {
  renderToolbar();
  fireEvent.click(screen.getByRole('button', { name: 'Mangas' }));
  expect(baseProps.onMediaTypeChange).toHaveBeenCalledWith('Manga');
});

it('emits query changes as the user types', () => {
  renderToolbar();
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'naruto' } });
  expect(baseProps.onQueryChange).toHaveBeenCalledWith('naruto');
});

it('toggles a genre chip', () => {
  renderToolbar();
  fireEvent.click(screen.getByRole('button', { name: 'Action' }));
  expect(baseProps.onToggleGenre).toHaveBeenCalledWith('Action');
});
