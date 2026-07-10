import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MaintenanceGate } from '../MaintenanceGate';
import MaintenancePage from '../../pages/utils/MaintenancePage';
import { apiClient } from '../../utils/apiClient';
import type { User } from '../../types';

vi.mock('../../utils/apiClient', () => ({ apiClient: vi.fn() }));

// Store zustand mocké : `mockUser` pilote le user vu par la garde.
let mockUser: Partial<User> | null = null;
vi.mock('../../store/authStore', () => ({
  useAuthStore: (selector: (s: { user: Partial<User> | null }) => unknown) =>
    selector({ user: mockUser }),
}));

const mocked = vi.mocked(apiClient);

const renderGate = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MaintenanceGate>
        <div>APP CONTENT</div>
      </MaintenanceGate>
    </QueryClientProvider>,
  );
};

describe('MaintenanceGate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUser = null;
  });

  it('renders the app when maintenance is off', async () => {
    mocked.mockResolvedValue({ maintenance_mode: false });
    renderGate();
    expect(await screen.findByText('APP CONTENT')).toBeInTheDocument();
  });

  it('renders the app when the config endpoint fails (fail-open)', async () => {
    mocked.mockRejectedValue(new Error('boom'));
    renderGate();
    expect(await screen.findByText('APP CONTENT')).toBeInTheDocument();
  });

  it('replaces the app with the maintenance page for visitors', async () => {
    mocked.mockResolvedValue({
      maintenance_mode: true,
      maintenance_message: 'Migration de la base en cours',
    });
    renderGate();
    expect(await screen.findByText('Migration de la base en cours')).toBeInTheDocument();
    expect(screen.queryByText('APP CONTENT')).not.toBeInTheDocument();
  });

  it('keeps the app with a banner for staff users', async () => {
    mockUser = { is_staff: true };
    mocked.mockResolvedValue({ maintenance_mode: true });
    renderGate();
    expect(await screen.findByText(/Mode maintenance actif/i)).toBeInTheDocument();
    expect(screen.getByText('APP CONTENT')).toBeInTheDocument();
  });
});

describe('MaintenancePage', () => {
  it('shows the default copy, ETA and triggers retry', async () => {
    const onRetry = vi.fn();
    render(<MaintenancePage until="2026-07-10T18:00:00Z" onRetry={onRetry} />);

    expect(screen.getByText('503')).toBeInTheDocument();
    expect(screen.getByText(/pause technique/i)).toBeInTheDocument();
    expect(screen.getByText(/Retour estimé/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Réessayer/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('prefers the custom message over the default copy', () => {
    render(<MaintenancePage message="On revient à 18h !" />);
    expect(screen.getByText('On revient à 18h !')).toBeInTheDocument();
    expect(screen.queryByText(/pause technique/i)).not.toBeInTheDocument();
  });
});
