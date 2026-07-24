import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import AccountSettingsPage from '../AccountSettingsPage';
import { useAuthStore } from '../../../store/authStore';

vi.mock('../../../store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('AccountSettingsPage', () => {
  it('renders login prompt when unauthenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuthStore>);

    render(
      <MemoryRouter>
        <AccountSettingsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/Vous devez être connecté/i)).toBeInTheDocument();
  });

  it('renders account settings when authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: '1', username: 'TestUser', custom_username_color: '#FFD700' },
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuthStore>);

    render(
      <MemoryRouter>
        <AccountSettingsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/GESTION DU/i)).toBeInTheDocument();
  });
});
