import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ToastContainer } from '../ToastContainer';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

const removeToast = vi.fn();
let toasts: Toast[] = [];

vi.mock('../../../store/toastStore', () => ({
  useToastStore: () => ({ toasts, removeToast }),
}));

describe('ToastContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    toasts = [];
  });

  it('renders nothing visible when there are no toasts', () => {
    render(<ToastContainer />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders each toast message', () => {
    toasts = [
      { id: 'a', message: 'Saved!', type: 'success' },
      { id: 'b', message: 'Boom', type: 'error' },
      { id: 'c', message: 'FYI', type: 'info' },
    ];
    render(<ToastContainer />);
    expect(screen.getByText('Saved!')).toBeInTheDocument();
    expect(screen.getByText('Boom')).toBeInTheDocument();
    expect(screen.getByText('FYI')).toBeInTheDocument();
  });

  it('applies type-specific background classes', () => {
    toasts = [
      { id: 'a', message: 'Saved!', type: 'success' },
      { id: 'b', message: 'Boom', type: 'error' },
      { id: 'c', message: 'FYI', type: 'info' },
    ];
    render(<ToastContainer />);
    // Darkened for WCAG AA contrast with the white toast text.
    expect(screen.getByText('Saved!').parentElement).toHaveClass('bg-green-700');
    expect(screen.getByText('Boom').parentElement).toHaveClass('bg-red-600');
    expect(screen.getByText('FYI').parentElement).toHaveClass('bg-blue-600');
  });

  it('calls removeToast with the toast id when close is clicked', () => {
    toasts = [{ id: 'xyz', message: 'Dismiss me', type: 'info' }];
    render(<ToastContainer />);
    fireEvent.click(screen.getByRole('button'));
    expect(removeToast).toHaveBeenCalledWith('xyz');
  });
});
