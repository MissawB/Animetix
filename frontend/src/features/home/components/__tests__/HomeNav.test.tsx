import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { HomeNav } from '../HomeNav';
import type { User } from '../../../../types';

const toggleSidebar = vi.fn();

interface UIState {
  toggleSidebar: () => void;
}

vi.mock('../../../../store/uiStore', () => ({
  useUIStore: (selector: (state: UIState) => unknown) => selector({ toggleSidebar }),
}));

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

let authState: AuthState = { user: null, isAuthenticated: false };

vi.mock('../../../../store/authStore', () => ({
  useAuthStore: () => authState,
}));

const renderNav = () =>
  render(
    <MemoryRouter>
      <HomeNav />
    </MemoryRouter>,
  );

describe('HomeNav', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState = { user: null, isAuthenticated: false };
  });

  it('renders the navigation links', () => {
    renderNav();
    expect(screen.getByText('Défi Quotidien').closest('a')).toHaveAttribute('href', '/daily-challenge/');
    expect(screen.getByText('Classement').closest('a')).toHaveAttribute('href', '/leaderboard/');
    expect(screen.getByText('Latent Space').closest('a')).toHaveAttribute('href', '/latent-space/');
  });

  it('toggles the sidebar when the menu button is clicked', () => {
    renderNav();
    fireEvent.click(screen.getByRole('button'));
    expect(toggleSidebar).toHaveBeenCalledTimes(1);
  });

  it('does not show user info when unauthenticated', () => {
    renderNav();
    expect(screen.queryByText('Standard')).not.toBeInTheDocument();
    expect(screen.queryByText('Boosté')).not.toBeInTheDocument();
  });

  it('shows the username and standard tier when authenticated', () => {
    authState = {
      isAuthenticated: true,
      user: {
        id: 1,
        username: 'otaku',
        email: 'o@x.com',
        is_authenticated: true,
        tier: 'free',
      },
    };
    renderNav();
    expect(screen.getByText('otaku')).toBeInTheDocument();
    expect(screen.getByText('Standard')).toBeInTheDocument();
  });

  it('shows the boosted tier label for premium users', () => {
    authState = {
      isAuthenticated: true,
      user: {
        id: 2,
        username: 'pro',
        email: 'p@x.com',
        is_authenticated: true,
        tier: 'premium',
      },
    };
    renderNav();
    expect(screen.getByText('Boosté')).toBeInTheDocument();
  });
});
