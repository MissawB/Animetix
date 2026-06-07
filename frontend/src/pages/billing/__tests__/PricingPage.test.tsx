import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PricingPage from '../PricingPage';

const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the store
vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    checkAuth: vi.fn(),
  })),
}));

// Mock the API
vi.mock('../../api', () => ({
  updateAccountSettings: vi.fn(),
}));

// Mock the toast store
vi.mock('../../store/toastStore', () => ({
  useToastStore: vi.fn(() => ({
    addToast: vi.fn(),
  })),
}));

describe('PricingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all pricing tiers', () => {
    render(
      <MemoryRouter>
        <PricingPage />
      </MemoryRouter>
    );
    
    expect(screen.getByText(/Explorateur/i)).toBeInTheDocument();
    expect(screen.getByText(/Premium/i)).toBeInTheDocument();
    expect(screen.getByText(/Expert API/i)).toBeInTheDocument();
  });

  it('redirects to login when a tier is selected by an anonymous user', () => {
    render(
      <MemoryRouter>
        <PricingPage />
      </MemoryRouter>
    );
    
    const selectButtons = screen.getAllByText(/SÉLECTIONNER/i);
    fireEvent.click(selectButtons[0]);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login?redirect=/pricing/');
  });
});



