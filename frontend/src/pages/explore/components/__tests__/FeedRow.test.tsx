import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { FeedRow, FeedRowData } from '../FeedRow';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const row: FeedRowData = {
  kind: 'top',
  title: 'Les mieux notés',
  reason: '',
  seed: null,
  items: [
    { id: '1', title: 'A', media_type: 'Anime', image: '' },
    { id: '2', title: 'B', media_type: 'Anime', image: '' },
  ],
};

const renderRow = () =>
  render(
    <MemoryRouter>
      <FeedRow row={row} rowId="feed-row-0" />
    </MemoryRouter>,
  );

it('renders every item in the row', () => {
  renderRow();
  expect(screen.getByText('A')).toBeInTheDocument();
  expect(screen.getByText('B')).toBeInTheDocument();
});

// Regression: the row wrapper carries a `group` marker only for its scroll
// arrows. A bare `group` on the wrapper collides with each MediaCard's own
// `group`, so `group-hover:` inside every card fires when the row is hovered —
// hovering one card lit up all of them. The wrapper must use a SCOPED named
// group (`group/row`) so it never triggers the cards' unnamed `group-hover:`.
it('scopes the row hover group so it cannot trigger the cards', () => {
  renderRow();
  const scrollContainer = document.getElementById('feed-row-0')!;
  const wrapper = scrollContainer.parentElement!;

  const classes = wrapper.className.split(/\s+/);
  expect(classes).toContain('group/row');
  // a bare `group` token would re-introduce the collision
  expect(classes).not.toContain('group');
});

it('drives the scroll arrows off the scoped row group', () => {
  renderRow();
  const leftArrow = screen.getByRole('button', { name: /défiler à gauche/i });
  expect(leftArrow.className).toContain('group-hover/row:opacity-100');
  expect(leftArrow.className).not.toContain('group-hover:opacity-100');
});
