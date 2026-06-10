import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PricingPage from '../PricingPage';
import { useAuthStore } from '../../../store/authStore';

vi.mock('../../../store/authStore');
vi.mock('../../../api', () => ({
  updateAccountSettings: vi.fn().mockResolvedValue({ status: 'updated' }),
  apiClient: vi.fn().mockResolvedValue({ status: 'refilled' })
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

describe('PricingPage (Espace Sponsors)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly for guests', () => {
    (useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn()
    });

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Sponsoring & Boost/i)).toBeInTheDocument();
    expect(screen.getByText(/Recharge Quota/i)).toBeInTheDocument();
    expect(screen.getByText(/Boost Cyber-Nexus/i)).toBeInTheDocument();
  });

  it('redirects to login when standard user tries to boost without login', () => {
    (useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn()
    });

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>
    );

    const boostButton = screen.getByText('ACTIVER LE BOOST');
    fireEvent.click(boostButton);

    expect(mockNavigate).toHaveBeenCalledWith('/login?redirect=/pricing/');
  });
});
