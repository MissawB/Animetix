import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import AdminNavbar from '../AdminNavbar';

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <AdminNavbar />
    </MemoryRouter>,
  );

describe('AdminNavbar', () => {
  it('renders the admin panel label', () => {
    renderAt('/admin/dashboard/');
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders all navigation links with correct hrefs', () => {
    renderAt('/admin/dashboard/');
    expect(screen.getByText('Hub').closest('a')).toHaveAttribute('href', '/admin/dashboard/');
    expect(screen.getByText('Users').closest('a')).toHaveAttribute('href', '/admin/users/');
    expect(screen.getByText('SOTA').closest('a')).toHaveAttribute('href', '/admin/sota-benchmark/');
  });

  it('marks the active route with the active classes', () => {
    renderAt('/admin/users/');
    const active = screen.getByText('Users').closest('a');
    expect(active).toHaveClass('bg-blue-600');
    const inactive = screen.getByText('Hub').closest('a');
    expect(inactive).not.toHaveClass('bg-blue-600');
  });
});
