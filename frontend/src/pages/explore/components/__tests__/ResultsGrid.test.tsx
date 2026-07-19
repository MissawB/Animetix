import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { ResultsGrid } from '../ResultsGrid';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const renderGrid = (items: Parameters<typeof ResultsGrid>[0]['items'], onClear = vi.fn()) =>
  render(
    <MemoryRouter>
      <ResultsGrid items={items} onClear={onClear} />
    </MemoryRouter>,
  );

it('shows the result count and renders each item', () => {
  renderGrid([
    { id: '1', title: 'Naruto', media_type: 'Anime' },
    { id: '2', title: 'Bleach', media_type: 'Anime' },
  ]);
  expect(screen.getByText(/2 résultats/i)).toBeInTheDocument();
  expect(screen.getByText('Naruto')).toBeInTheDocument();
  expect(screen.getByText('Bleach')).toBeInTheDocument();
});

it('shows an empty message when there are no results', () => {
  renderGrid([]);
  expect(screen.getByText(/aucun résultat/i)).toBeInTheDocument();
});

it('calls onClear when the clear button is clicked', () => {
  const onClear = vi.fn();
  renderGrid([{ id: '1', title: 'Naruto', media_type: 'Anime' }], onClear);
  fireEvent.click(screen.getByRole('button', { name: /effacer/i }));
  expect(onClear).toHaveBeenCalledTimes(1);
});
