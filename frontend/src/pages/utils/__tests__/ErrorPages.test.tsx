import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ForbiddenPage from '../ForbiddenPage';
import ServerErrorPage from '../ServerErrorPage';
import NotFoundPage from '../NotFoundPage';
import { RequireStaff } from '../../../components/RequireStaff';
import type { User } from '../../../types';

// Store zustand mocké : `mockAuth` pilote l'état vu par RequireStaff.
let mockAuth: { user: Partial<User> | null; isLoading: boolean } = {
  user: null,
  isLoading: false,
};
vi.mock('../../../store/authStore', () => ({
  useAuthStore: (selector: (s: typeof mockAuth) => unknown) => selector(mockAuth),
}));

const renderWithRouter = (ui: React.ReactElement) => render(<MemoryRouter>{ui}</MemoryRouter>);

describe('Error pages', () => {
  it('ForbiddenPage renders the 403 shell', () => {
    renderWithRouter(<ForbiddenPage />);
    expect(screen.getByText('403')).toBeInTheDocument();
    expect(screen.getByText(/réservée aux administrateurs/i)).toBeInTheDocument();
  });

  it('ServerErrorPage renders the 500 shell with a reload action', () => {
    renderWithRouter(<ServerErrorPage />);
    expect(screen.getByText('500')).toBeInTheDocument();
    expect(screen.getByText(/Recharger/i)).toBeInTheDocument();
  });

  it('NotFoundPage still renders the 404 universe', () => {
    renderWithRouter(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText(/trou noir narratif/i)).toBeInTheDocument();
  });
});

describe('RequireStaff', () => {
  const renderGuarded = () =>
    render(
      <MemoryRouter initialEntries={['/admin/']}>
        <Routes>
          <Route element={<RequireStaff />}>
            <Route path="/admin/" element={<div>ADMIN CONTENT</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

  beforeEach(() => {
    mockAuth = { user: null, isLoading: false };
  });

  it('shows the 403 page to visitors', () => {
    renderGuarded();
    expect(screen.getByText('403')).toBeInTheDocument();
    expect(screen.queryByText('ADMIN CONTENT')).not.toBeInTheDocument();
  });

  it('shows the 403 page to authenticated non-staff users', () => {
    mockAuth = { user: { is_staff: false }, isLoading: false };
    renderGuarded();
    expect(screen.getByText('403')).toBeInTheDocument();
  });

  it('renders the admin subtree for staff users', () => {
    mockAuth = { user: { is_staff: true }, isLoading: false };
    renderGuarded();
    expect(screen.getByText('ADMIN CONTENT')).toBeInTheDocument();
  });

  it('renders nothing while the session is resolving', () => {
    mockAuth = { user: null, isLoading: true };
    renderGuarded();
    expect(screen.queryByText('403')).not.toBeInTheDocument();
    expect(screen.queryByText('ADMIN CONTENT')).not.toBeInTheDocument();
  });
});
