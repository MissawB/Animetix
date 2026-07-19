import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PricingPage from '../PricingPage';
import { useAuthStore } from '../../../store/authStore';

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

describe('PricingPage (Espace Sponsors)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  const mockGuest = () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      checkAuth: vi.fn(),
    } as unknown as ReturnType<typeof useAuthStore>);
  };

  it('renders correctly for guests', () => {
    mockGuest();

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>,
    );

    expect(screen.getByText(/Sponsoring & Boost/i)).toBeInTheDocument();
    expect(screen.getByText(/Recharge Quota/i)).toBeInTheDocument();
    expect(screen.getByText(/Boost Cyber-Nexus/i)).toBeInTheDocument();
  });

  it('redirects to login when standard user tries to boost without login', () => {
    vi.stubEnv('VITE_SPONSOR_AD_TAG', 'https://ads.example.com/vast.xml');
    mockGuest();

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>,
    );

    const boostButton = screen.getByText('ACTIVER LE BOOST');
    fireEvent.click(boostButton);

    expect(mockNavigate).toHaveBeenCalledWith('/login?redirect=/pricing/');
  });

  // Audit dette 2026-07-19 : tant qu'aucun vrai sponsor (VITE_SPONSOR_AD_TAG)
  // n'est configuré, le flux pub récompensée reste dormant — aucun contenu de
  // démo Google ne doit tourner en prod.
  it('disables both sponsor CTAs when no ad tag is configured', () => {
    mockGuest();

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>,
    );

    const soonButtons = screen.getAllByText(/SPONSORS BIENTÔT DISPONIBLES/i);
    expect(soonButtons).toHaveLength(2);
    soonButtons.forEach((label) => {
      expect(label.closest('button')).toBeDisabled();
    });
  });

  it('never opens the sponsor modal when no ad tag is configured', () => {
    mockGuest();

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>,
    );

    const soonButtons = screen.getAllByText(/SPONSORS BIENTÔT DISPONIBLES/i);
    soonButtons.forEach((label) => {
      const btn = label.closest('button');
      if (btn) fireEvent.click(btn);
    });

    expect(mockNavigate).not.toHaveBeenCalled();
    expect(screen.queryByText(/Pub récompensée/i)).not.toBeInTheDocument();
  });

  it('keeps the sponsor CTAs active when an ad tag is configured', () => {
    vi.stubEnv('VITE_SPONSOR_AD_TAG', 'https://ads.example.com/vast.xml');
    mockGuest();

    render(
      <BrowserRouter>
        <PricingPage />
      </BrowserRouter>,
    );

    expect(screen.getByText('RECHARGER MON QUOTA').closest('button')).toBeEnabled();
    expect(screen.getByText('ACTIVER LE BOOST').closest('button')).toBeEnabled();
    expect(screen.queryByText(/SPONSORS BIENTÔT DISPONIBLES/i)).not.toBeInTheDocument();
  });
});
