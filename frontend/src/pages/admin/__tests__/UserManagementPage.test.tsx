import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import UserManagementPage from '../UserManagementPage';

interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  level: number;
  tier: string;
}

const getUsers = vi.fn<() => Promise<AdminUser[]>>();
const toggleStaff = vi.fn<(id: number) => Promise<unknown>>();
const toggleActive = vi.fn<(id: number) => Promise<unknown>>();

vi.mock('../../../features/admin/services/adminService', () => ({
  adminService: {
    getUsers: () => getUsers(),
    toggleStaff: (id: number) => toggleStaff(id),
    toggleActive: (id: number) => toggleActive(id),
  },
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <UserManagementPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const sampleUsers: AdminUser[] = [
  {
    id: 1,
    username: 'alice',
    email: 'alice@example.com',
    is_staff: true,
    is_active: true,
    date_joined: '2024-01-01T00:00:00Z',
    level: 12,
    tier: 'premium',
  },
  {
    id: 2,
    username: 'bob',
    email: 'bob@example.com',
    is_staff: false,
    is_active: false,
    date_joined: '2024-02-01T00:00:00Z',
    level: 3,
    tier: 'free',
  },
];

describe('UserManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the loading row while fetching', () => {
    getUsers.mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/Chargement des archives/i)).toBeInTheDocument();
  });

  it('renders user rows when data is loaded', async () => {
    getUsers.mockResolvedValue(sampleUsers);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument();
    });
    expect(screen.getByText('bob')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    // Staff badge for alice + banned badge for inactive bob.
    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.getByText('Banni')).toBeInTheDocument();
    expect(screen.getByText('PREMIUM')).toBeInTheDocument();
  });

  it('filters the user list by the search term', async () => {
    getUsers.mockResolvedValue(sampleUsers);
    renderPage();

    await waitFor(() => expect(screen.getByText('alice')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Rechercher un utilisateur'), {
      target: { value: 'bob' },
    });

    expect(screen.queryByText('alice')).not.toBeInTheDocument();
    expect(screen.getByText('bob')).toBeInTheDocument();
  });

  it('shows the empty state when no user matches the search', async () => {
    getUsers.mockResolvedValue(sampleUsers);
    renderPage();

    await waitFor(() => expect(screen.getByText('alice')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Rechercher un utilisateur'), {
      target: { value: 'zzz-nobody' },
    });

    expect(screen.getByText('Aucun utilisateur trouvé')).toBeInTheDocument();
  });

  it('triggers the toggle-staff and toggle-active mutations', async () => {
    getUsers.mockResolvedValue(sampleUsers);
    toggleStaff.mockResolvedValue({});
    toggleActive.mockResolvedValue({});
    renderPage();

    await waitFor(() => expect(screen.getByText('alice')).toBeInTheDocument());

    // alice is staff -> "Retirer les droits Admin"
    fireEvent.click(screen.getAllByLabelText('Retirer les droits Admin')[0]);
    await waitFor(() => expect(toggleStaff).toHaveBeenCalledWith(1));

    // alice is active -> "Désactiver le compte"
    fireEvent.click(screen.getAllByLabelText('Désactiver le compte')[0]);
    await waitFor(() => expect(toggleActive).toHaveBeenCalledWith(1));
  });
});
