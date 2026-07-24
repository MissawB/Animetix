import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PricingPage from '../PricingPage';
import { useAuthStore } from '../../../store/authStore';
import { socialService } from '../../../features/social/services/socialService';

vi.mock('../../../store/authStore');
vi.mock('../../../features/social/services/socialService', () => ({
  socialService: {
    updateAccountSettings: vi.fn().mockResolvedValue({ status: 'updated' }),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderWithQueryClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
};

describe('PricingPage (Espace Sponsors)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockGuest = () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn(),
    } as unknown as ReturnType<typeof useAuthStore>);
  };

  const mockUser = () => {
    const checkAuth = vi.fn().mockResolvedValue(undefined);
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'standard', unlocked_badges: [] },
      isAuthenticated: true,
      checkAuth,
      refetchUser: vi.fn().mockResolvedValue(undefined),
    } as unknown as ReturnType<typeof useAuthStore>);
    return { checkAuth };
  };

  it('renders correctly for guests', () => {
    mockGuest();

    renderWithQueryClient(<PricingPage />);

    expect(screen.getByText(/Sponsoring & Boost/i)).toBeInTheDocument();
    expect(screen.getByText(/Recharge Quota/i)).toBeInTheDocument();
    expect(screen.getByText(/Boost Cyber-Nexus/i)).toBeInTheDocument();
  });

  it('redirects to login when a guest tries to boost', () => {
    mockGuest();

    renderWithQueryClient(<PricingPage />);

    const boostButton = screen.getByText('ACTIVER LE BOOST');
    fireEvent.click(boostButton);

    expect(mockNavigate).toHaveBeenCalledWith('/login?redirect=/pricing/');
  });

  // Conformité AdSense : le boost est une action directe — aucune publicité
  // à visionner, aucune récompense conditionnée à une annonce.
  it('activates the boost directly for a logged-in user, without any ad gate', async () => {
    mockUser();

    renderWithQueryClient(<PricingPage />);

    fireEvent.click(screen.getByText('ACTIVER LE BOOST'));

    await waitFor(() => {
      expect(socialService.updateAccountSettings).toHaveBeenCalledWith({ tier: 'premium' });
    });
    expect(screen.queryByText(/Pub récompensée/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/VISIONNEZ LA PUB/i)).not.toBeInTheDocument();
  });
});
