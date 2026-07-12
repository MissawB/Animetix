import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';
import { useAuthStore } from '../../../store/authStore';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate, useLocation: () => ({ state: null }) };
});

vi.mock('../../../store/authStore', () => ({ useAuthStore: vi.fn() }));
const mockedStore = vi.mocked(useAuthStore);

const login = vi.fn();
const loginWithGoogle = vi.fn();
const resetPassword = vi.fn();

const renderPage = () =>
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );

const typeEmail = (value: string) => userEvent.type(screen.getByLabelText(/adresse email/i), value);

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedStore.mockReturnValue({
      login,
      loginWithGoogle,
      resetPassword,
      isLoading: false,
    } as unknown as ReturnType<typeof useAuthStore>);
  });

  it('translates a bad password instead of quoting Firebase', async () => {
    login.mockRejectedValue({ code: 'auth/invalid-credential' });
    renderPage();

    await typeEmail('kenji@animetix.com');
    await userEvent.type(screen.getByLabelText(/mot de passe/i), 'mauvais');
    await userEvent.click(screen.getByRole('button', { name: /^se connecter$/i }));

    expect(await screen.findByText(/email ou mot de passe incorrect/i)).toBeInTheDocument();
    expect(screen.queryByText(/firebase/i)).not.toBeInTheDocument();
    expect(navigate).not.toHaveBeenCalled();
  });

  // ── Password reset ────────────────────────────────────────────────────────
  it('offers a password reset', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /mot de passe oublié/i })).toBeInTheDocument();
  });

  it('sends the reset link to the address already typed', async () => {
    resetPassword.mockResolvedValue(undefined);
    renderPage();

    await typeEmail('kenji@animetix.com');
    await userEvent.click(screen.getByRole('button', { name: /mot de passe oublié/i }));

    expect(resetPassword).toHaveBeenCalledWith('kenji@animetix.com');
    expect(await screen.findByRole('status')).toHaveTextContent(/lien de réinitialisation/i);
  });

  it('answers an unknown address EXACTLY like a known one', async () => {
    // Anything else turns this button into a way to discover which emails have
    // an account here.
    const reset = async (email: string) => {
      renderPage();
      await typeEmail(email);
      await userEvent.click(screen.getByRole('button', { name: /mot de passe oublié/i }));
      const text = (await screen.findByRole('status')).textContent;
      expect(screen.queryByText(/aucun compte|n'existe pas|inconnu/i)).not.toBeInTheDocument();
      cleanup();
      return text;
    };

    resetPassword.mockResolvedValue(undefined);
    const known = await reset('connu@animetix.com');

    resetPassword.mockRejectedValue({ code: 'auth/user-not-found' });
    const unknown = await reset('inconnu@animetix.com');

    expect(unknown).toBe(known);
  });

  it('asks for the email first when the field is empty', async () => {
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /mot de passe oublié/i }));

    expect(await screen.findByText(/saisissez votre adresse email/i)).toBeInTheDocument();
    expect(resetPassword).not.toHaveBeenCalled();
  });

  it('surfaces a real reset failure', async () => {
    resetPassword.mockRejectedValue({ code: 'auth/too-many-requests' });
    renderPage();

    await typeEmail('kenji@animetix.com');
    await userEvent.click(screen.getByRole('button', { name: /mot de passe oublié/i }));

    expect(await screen.findByText(/trop de tentatives/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());
  });
});
