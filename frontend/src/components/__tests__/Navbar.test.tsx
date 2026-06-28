import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Navbar from '../Navbar';

// Mock the stores
vi.mock('../../store/uiStore', () => ({
  useUIStore: vi.fn((selector) => selector({ toggleSidebar: vi.fn() })),
}));

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    logout: vi.fn(),
  })),
}));

vi.mock('../../store/personalizationStore', () => ({
  usePersonalizationStore: vi.fn(() => ({
    isPersonalizationEnabled: false,
    setPersonalizationEnabled: vi.fn(),
  })),
}));

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(() => ({
    unreadCount: 0,
    clearUnread: vi.fn(),
  })),
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the sidebar toggle button', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('nav.toggle_sidebar')).toBeInTheDocument();
  });

  it('shows auth links when logged out', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    const registerLink = screen.getByText(/auth\.register/i).closest('a');
    expect(registerLink).toHaveAttribute('href', '/auth/register/');
  });
});
