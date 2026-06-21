import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SidebarOverlay from '../SidebarOverlay';

describe('SidebarOverlay', () => {
  it('renders an accessible overlay button', () => {
    render(<SidebarOverlay onClose={vi.fn()} />);
    const overlay = screen.getByRole('button');
    expect(overlay).toBeInTheDocument();
    expect(overlay).toHaveAttribute('id', 'sidebar-overlay');
    expect(overlay).toHaveAttribute('tabindex', '0');
  });

  it('calls onClose when clicked', () => {
    const onClose = vi.fn();
    render(<SidebarOverlay onClose={onClose} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose on Enter key', () => {
    const onClose = vi.fn();
    render(<SidebarOverlay onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose on Space key', () => {
    const onClose = vi.fn();
    render(<SidebarOverlay onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not call onClose on unrelated key', () => {
    const onClose = vi.fn();
    render(<SidebarOverlay onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Escape' });
    expect(onClose).not.toHaveBeenCalled();
  });
});
