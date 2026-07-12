import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from '../RegisterPage';
import { useAuthStore } from '../../../store/authStore';

/**
 * The sign-up page offered email/password only: Google was on the login page but
 * never on the dedicated register page, so "s'inscrire avec Google" was simply
 * impossible. With Firebase, signInWithPopup creates the account when it does not
 * exist, so the same call serves both flows.
 */

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

vi.mock('../../../store/authStore', () => ({ useAuthStore: vi.fn() }));
const mockedStore = vi.mocked(useAuthStore);

const register = vi.fn();
const loginWithGoogle = vi.fn();

const renderPage = () =>
  render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedStore.mockReturnValue({
      register,
      loginWithGoogle,
      isLoading: false,
    } as unknown as ReturnType<typeof useAuthStore>);
  });

  it('offers Google sign-up', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /s'inscrire avec google/i })).toBeInTheDocument();
  });

  it('signs up through Google and lands on the home page', async () => {
    loginWithGoogle.mockResolvedValue(undefined);
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /s'inscrire avec google/i }));

    expect(loginWithGoogle).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/'));
  });

  it('explains a blocked Google popup instead of navigating', async () => {
    loginWithGoogle.mockRejectedValue({ code: 'auth/popup-blocked' });
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /s'inscrire avec google/i }));

    // The user gets an actionable sentence, not "Firebase: Error (auth/...)".
    expect(await screen.findByText(/pop-ups/i)).toBeInTheDocument();
    expect(screen.queryByText(/firebase/i)).not.toBeInTheDocument();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('says the address is taken when the account already exists', async () => {
    register.mockRejectedValue({ code: 'auth/email-already-in-use' });
    renderPage();

    await userEvent.type(screen.getByLabelText(/pseudo/i), 'kenji');
    await userEvent.type(screen.getByLabelText(/adresse email/i), 'kenji@animetix.com');
    await userEvent.type(screen.getByLabelText(/mot de passe/i), 'hunter2!');
    await userEvent.click(screen.getByRole('button', { name: /s'inscrire$/i }));

    expect(await screen.findByText(/compte existe déjà/i)).toBeInTheDocument();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows nothing when the user closes the Google popup themselves', async () => {
    loginWithGoogle.mockRejectedValue({ code: 'auth/popup-closed-by-user' });
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /s'inscrire avec google/i }));

    // Backing out on purpose is not a failure: no error banner at all.
    await waitFor(() => expect(loginWithGoogle).toHaveBeenCalled());
    expect(screen.queryByText(/échou|incorrect|erreur/i)).not.toBeInTheDocument();
  });

  it('still registers with email and password', async () => {
    register.mockResolvedValue(undefined);
    renderPage();

    await userEvent.type(screen.getByLabelText(/pseudo/i), 'kenji');
    await userEvent.type(screen.getByLabelText(/adresse email/i), 'kenji@animetix.com');
    await userEvent.type(screen.getByLabelText(/mot de passe/i), 'hunter2!');
    await userEvent.click(screen.getByRole('button', { name: /s'inscrire$/i }));

    expect(register).toHaveBeenCalledWith({
      username: 'kenji',
      email: 'kenji@animetix.com',
      password: 'hunter2!',
    });
  });
});
