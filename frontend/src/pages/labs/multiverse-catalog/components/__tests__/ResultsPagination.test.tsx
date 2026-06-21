import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ResultsPagination from '../ResultsPagination';
import type { Pagination } from '../../types';

const makePagination = (overrides: Partial<Pagination> = {}): Pagination => ({
  page: 1,
  page_size: 20,
  total: 200,
  total_pages: 10,
  has_next: true,
  has_previous: false,
  ...overrides,
});

describe('ResultsPagination', () => {
  it('renders prev/next labels', () => {
    render(
      <ResultsPagination
        pagination={makePagination()}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={vi.fn()}
      />,
    );
    expect(screen.getByText('Précédent')).toBeInTheDocument();
    expect(screen.getByText('Suivant')).toBeInTheDocument();
  });

  it('renders all pages when total_pages <= 7', () => {
    render(
      <ResultsPagination
        pagination={makePagination({ total_pages: 5, has_next: false })}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '5' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '6' })).not.toBeInTheDocument();
  });

  it('renders a windowed range when current page is in the middle', () => {
    render(
      <ResultsPagination
        pagination={makePagination({ page: 6, total_pages: 12 })}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={vi.fn()}
      />,
    );
    // currentPage 6 => window 3..9
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '9' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '1' })).not.toBeInTheDocument();
  });

  it('disables the previous button when has_previous is false', () => {
    render(
      <ResultsPagination
        pagination={makePagination({ has_previous: false })}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={vi.fn()}
      />,
    );
    expect(screen.getByText('Précédent').closest('button')).toBeDisabled();
  });

  it('disables the next button when has_next is false', () => {
    render(
      <ResultsPagination
        pagination={makePagination({ has_next: false })}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={vi.fn()}
      />,
    );
    expect(screen.getByText('Suivant').closest('button')).toBeDisabled();
  });

  it('fires onPrev / onNext on enabled navigation clicks', () => {
    const onPrev = vi.fn();
    const onNext = vi.fn();
    render(
      <ResultsPagination
        pagination={makePagination({ page: 2, has_previous: true, has_next: true })}
        onPrev={onPrev}
        onNext={onNext}
        onSelectPage={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText('Précédent'));
    fireEvent.click(screen.getByText('Suivant'));
    expect(onPrev).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it('fires onSelectPage with the page number when a page button is clicked', () => {
    const onSelectPage = vi.fn();
    render(
      <ResultsPagination
        pagination={makePagination({ total_pages: 5, has_next: false })}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSelectPage={onSelectPage}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: '3' }));
    expect(onSelectPage).toHaveBeenCalledWith(3);
  });
});
