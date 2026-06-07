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

  it('renders the Games link', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    
    const gamesLink = screen.getByText(/Games/i);
    expect(gamesLink).toBeInTheDocument();
    expect(gamesLink.closest('a')).toHaveAttribute('href', '/games/');
  });
});
