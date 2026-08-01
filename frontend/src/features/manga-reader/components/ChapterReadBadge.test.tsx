import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChapterReadBadge } from './ChapterReadBadge';

describe('ChapterReadBadge', () => {
  it('shows a read state and toggles back to unread', async () => {
    const onToggleRead = vi.fn();
    render(
      <ChapterReadBadge
        progress={{ number: 1, is_read: true, last_page_read: 82, page_count: 83 }}
        onToggleRead={onToggleRead}
      />,
    );

    const button = screen.getByRole('button', { name: /marquer comme non lu/i });
    await userEvent.click(button);
    expect(onToggleRead).toHaveBeenCalledWith(false);
  });

  it('shows page progress for a chapter in progress', () => {
    render(
      <ChapterReadBadge
        progress={{ number: 1, is_read: false, last_page_read: 11, page_count: 83 }}
        onToggleRead={vi.fn()}
      />,
    );
    expect(screen.getByText('12/83')).toBeInTheDocument();
  });

  it('hides the counter when the page count is unknown', () => {
    render(
      <ChapterReadBadge
        progress={{ number: 1, is_read: false, last_page_read: 0, page_count: 0 }}
        onToggleRead={vi.fn()}
      />,
    );
    expect(screen.queryByText(/\//)).not.toBeInTheDocument();
  });
});
