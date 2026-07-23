import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PowerStationPage from '../PowerStationPage';
import { useAuthStore } from '../../../store/authStore';
import { usePassiveMiningStore } from '../../../store/passiveMiningStore';
import { apiClient } from '../../../utils/apiClient';

vi.mock('../../../store/authStore');
vi.mock('../../../store/passiveMiningStore');
vi.mock('../../../features/billing/components/PassiveAdMiner', () => ({
  PassiveAdMiner: () => null,
}));
vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

const mockedApiClient = vi.mocked(apiClient);

const mockUser = {
  id: 'USER-123',
  username: 'OtakuTester',
  wallet_balance: 1250,
  is_staff: false,
};

const mockLedgerData = {
  history: [
    {
      amount: 250,
      type: 'ad_active',
      description: 'Active Mining Reward',
      date: '2026-07-21T20:00:00Z',
    },
    {
      amount: -50,
      type: 'ai_usage',
      description: 'LLM Generation Cost',
      date: '2026-07-21T19:30:00Z',
    },
  ],
  pagination: {
    total_pages: 1,
    page: 1,
  },
};

const mockStoreState = {
  isEnabled: true,
  setEnabled: vi.fn(),
  setStatus: vi.fn(),
  setTimeLeft: vi.fn(),
  decrementTimeLeft: vi.fn(),
  addTotalMined: vi.fn(),
  incrementTotalMined: vi.fn(),
  setLastMinedAt: vi.fn(),
  timeLeft: 120,
  totalMined: 300,
  status: 'ONLINE',
};

describe('PowerStationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const authState = {
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
      refetchUser: vi.fn().mockResolvedValue(undefined),
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    vi.mocked(useAuthStore).mockImplementation((selector?: any) =>
      selector ? selector(authState) : authState,
    );

    (useAuthStore as unknown as { getState: () => typeof authState }).getState = () => authState;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    vi.mocked(usePassiveMiningStore).mockImplementation((selector?: any) =>
      selector ? selector(mockStoreState) : mockStoreState,
    );

    (
      usePassiveMiningStore as unknown as {
        getState: () => typeof mockStoreState;
      }
    ).getState = () => mockStoreState;

    mockedApiClient.mockImplementation(async (url: string) => {
      if (url.includes('watch-ad')) {
        return { earned: 250 };
      }
      return mockLedgerData;
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders header, holographic wallet, and balance', () => {
    render(
      <MemoryRouter>
        <PowerStationPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('BERRIX')).toBeInTheDocument();
    expect(screen.getByText('WALLET')).toBeInTheDocument();
    expect(screen.getByText('1 250')).toBeInTheDocument();
    expect(screen.getByText('OtakuTester')).toBeInTheDocument();
    expect(screen.getByText('USER NODE')).toBeInTheDocument();
  });

  it('renders active mining and passive mining cards', () => {
    render(
      <MemoryRouter>
        <PowerStationPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Active Mining')).toBeInTheDocument();
    expect(screen.getAllByText('Passive Mining').length).toBeGreaterThan(0);
    expect(screen.getByText('STATUS: ONLINE')).toBeInTheDocument();
    expect(screen.getAllByText('Lancer la recharge').length).toBeGreaterThan(0);
  });

  it('fetches transaction ledger and displays records', async () => {
    render(
      <MemoryRouter>
        <PowerStationPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Active Mining Reward')).toBeInTheDocument();
    });

    expect(screen.getByText('LLM Generation Cost')).toBeInTheDocument();
    expect(screen.getAllByText(/\+250/).length).toBeGreaterThan(0);
    expect(screen.getByText(/-50/)).toBeInTheDocument();
  });

  it('triggers ad watch completion and credits Bx', async () => {
    render(
      <MemoryRouter>
        <PowerStationPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Active Mining Reward')).toBeInTheDocument();
    });

    const watchBtn = screen.getByRole('button', { name: /Lancer la recharge/i });

    vi.useFakeTimers();
    fireEvent.click(watchBtn);

    act(() => {
      vi.advanceTimersByTime(16000);
    });

    vi.useRealTimers();

    await waitFor(() => {
      expect(mockedApiClient).toHaveBeenCalledWith('/api/v1/billing/wallet/watch-ad/', {
        method: 'POST',
      });
    });
  });
});
