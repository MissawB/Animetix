import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { User } from '../../types';

// --- Mock firebase app/auth instance (../utils/firebase) ---
// The store imports `{ auth }` from '../utils/firebase'. We expose a sentinel
// object so we can assert it is forwarded to the firebase/auth functions.
const fakeAuth = { __isFakeAuth: true };
vi.mock('../../utils/firebase', () => ({
  auth: fakeAuth,
}));

// --- Mock the firebase/auth SDK functions ---
vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: vi.fn(),
  createUserWithEmailAndPassword: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn(),
  signInWithPopup: vi.fn(),
  signInWithRedirect: vi.fn(),
  getRedirectResult: vi.fn(),
  GoogleAuthProvider: vi.fn(function GoogleAuthProvider() {}),
  OAuthProvider: vi.fn(function OAuthProvider() {
    return { addScope: vi.fn() };
  }),
  TwitterAuthProvider: vi.fn(function TwitterAuthProvider() {}),
}));

// --- Mock the authService getAuthUser call ---
vi.mock('../../features/auth/services/authService', () => ({
  authService: {
    getAuthUser: vi.fn(),
  },
}));

// --- Mock the notification store (connect/disconnect are side effects) ---
const connect = vi.fn();
const disconnect = vi.fn();
vi.mock('../notificationStore', () => ({
  useNotificationStore: {
    getState: () => ({ connect, disconnect }),
  },
}));

// --- Mock the toast store (redirect-result errors surface as a toast: the
// user can land back on any route, so there is no login-page error banner
// to render into) ---
const addToast = vi.fn();
vi.mock('../toastStore', () => ({
  useToastStore: {
    getState: () => ({ addToast }),
  },
}));

// --- Mock the app's i18n singleton (../../i18n/config) ---
// By default this mirrors the old fallback-only behavior (return the
// provided fallback verbatim, ignoring the key) so every existing test in
// this file keeps observing the same French default strings baked into
// authErrors.ts. The dedicated localization test below swaps this mock out
// (via vi.doMock + vi.resetModules, same pattern as the "auth null" test)
// to prove the store actually calls through the singleton instead of a
// hardcoded-French shim.
vi.mock('../../i18n/config', () => ({
  default: { t: (key: string, fallback?: string) => fallback ?? key },
}));

import * as firebaseAuth from 'firebase/auth';
import { authService } from '../../features/auth/services/authService';

const mockGetAuthUser = vi.mocked(authService.getAuthUser);
const mockSignIn = vi.mocked(firebaseAuth.signInWithEmailAndPassword);
const mockCreateUser = vi.mocked(firebaseAuth.createUserWithEmailAndPassword);
const mockSignOut = vi.mocked(firebaseAuth.signOut);
const mockOnAuthStateChanged = vi.mocked(firebaseAuth.onAuthStateChanged);
const mockSignInWithPopup = vi.mocked(firebaseAuth.signInWithPopup);
const mockSignInWithRedirect = vi.mocked(firebaseAuth.signInWithRedirect);
const mockGetRedirectResult = vi.mocked(firebaseAuth.getRedirectResult);

const sampleUser = { id: 1, username: 'kira', email: 'kira@example.com' } as unknown as User;

// The store keeps a module-private `authListenerInitialized` guard so the
// onAuthStateChanged listener is wired at most once per module instance.
// We reset modules per test so each `checkAuth` test gets a fresh guard, and
// re-import the store after the mocks are registered.
async function freshStore() {
  vi.resetModules();
  const mod = await import('../authStore');
  return mod.useAuthStore;
}

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    connect.mockReset();
    disconnect.mockReset();
    addToast.mockReset();
    // Default: no pending redirect on boot (the overwhelmingly common case —
    // most page loads are not the return leg of a signInWithRedirect trip).
    mockGetRedirectResult.mockResolvedValue(null);
  });

  it('login: sets isLoading true, calls firebase with auth+creds, resolves leaving isLoading true', async () => {
    const useAuthStore = await freshStore();
    mockSignIn.mockResolvedValue({} as never);
    useAuthStore.setState({ isLoading: false });

    const promise = useAuthStore.getState().login({ email: 'a@b.com', password: 'pw' });
    // isLoading flipped to true synchronously at the start of the action
    expect(useAuthStore.getState().isLoading).toBe(true);

    await promise;

    expect(mockSignIn).toHaveBeenCalledWith(fakeAuth, 'a@b.com', 'pw');
    // On success login does NOT reset isLoading (the auth listener does)
    expect(useAuthStore.getState().isLoading).toBe(true);
  });

  it('login: on firebase error sets isLoading false and re-throws', async () => {
    const useAuthStore = await freshStore();
    mockSignIn.mockRejectedValue(new Error('bad credentials'));

    await expect(
      useAuthStore.getState().login({ email: 'a@b.com', password: 'wrong' }),
    ).rejects.toThrow('bad credentials');

    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('register: forwards creds and on error resets isLoading and re-throws', async () => {
    const useAuthStore = await freshStore();
    mockCreateUser.mockResolvedValue({} as never);
    await useAuthStore.getState().register({ email: 'new@b.com', password: 'pw' });
    expect(mockCreateUser).toHaveBeenCalledWith(fakeAuth, 'new@b.com', 'pw');

    mockCreateUser.mockRejectedValue(new Error('email in use'));
    await expect(
      useAuthStore.getState().register({ email: 'dup@b.com', password: 'pw' }),
    ).rejects.toThrow('email in use');
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('loginWithGoogle: opens popup with auth; on error resets isLoading and re-throws', async () => {
    const useAuthStore = await freshStore();
    mockSignInWithPopup.mockResolvedValue({} as never);
    await useAuthStore.getState().loginWithGoogle();
    expect(mockSignInWithPopup).toHaveBeenCalledTimes(1);
    expect(mockSignInWithPopup.mock.calls[0][0]).toBe(fakeAuth);

    // A deliberate cancel (user closed the popup): must reject as before and
    // must NOT fall back to a redirect — see the dedicated test below.
    const cancelled = new Error('popup closed');
    (cancelled as unknown as { code: string }).code = 'auth/cancelled-popup-request';
    mockSignInWithPopup.mockRejectedValue(cancelled);
    await expect(useAuthStore.getState().loginWithGoogle()).rejects.toThrow('popup closed');
    expect(useAuthStore.getState().isLoading).toBe(false);
    expect(mockSignInWithRedirect).not.toHaveBeenCalled();
  });

  it('loginWithGoogle: popup blocked falls back to signInWithRedirect (same provider, same auth)', async () => {
    const useAuthStore = await freshStore();
    const blocked = new Error('blocked');
    (blocked as unknown as { code: string }).code = 'auth/popup-blocked';
    mockSignInWithPopup.mockRejectedValue(blocked);
    mockSignInWithRedirect.mockResolvedValue(undefined as never);

    await useAuthStore.getState().loginWithGoogle();

    expect(mockSignInWithPopup).toHaveBeenCalledTimes(1);
    expect(mockSignInWithRedirect).toHaveBeenCalledTimes(1);
    expect(mockSignInWithRedirect.mock.calls[0][0]).toBe(fakeAuth);
    // Same provider instance that was handed to signInWithPopup.
    expect(mockSignInWithRedirect.mock.calls[0][1]).toBe(mockSignInWithPopup.mock.calls[0][1]);
  });

  it('loginWithGoogle: user-cancelled popup errors never fall back to redirect', async () => {
    const useAuthStore = await freshStore();
    for (const code of [
      'auth/popup-closed-by-user',
      'auth/cancelled-popup-request',
      'auth/user-cancelled',
    ]) {
      const err = new Error(code);
      (err as unknown as { code: string }).code = code;
      mockSignInWithPopup.mockRejectedValue(err);

      await expect(useAuthStore.getState().loginWithGoogle()).rejects.toThrow();
      expect(mockSignInWithRedirect).not.toHaveBeenCalled();
    }
  });

  it('loginWithGoogle: a code-less error (e.g. an ad-blocker killing the popup pre-flight) still falls back to redirect', async () => {
    // net::ERR_BLOCKED_BY_CLIENT and similar low-level rejections never carry
    // a Firebase `.code` at all. This is exactly the case the fallback exists
    // for, and unlike a deliberate cancellation (which always has one of the
    // POPUP_USER_CANCELLED_CODES) it must NOT be treated as a user cancel.
    const useAuthStore = await freshStore();
    const blocked = new Error('blocked by client');
    expect((blocked as unknown as { code?: string }).code).toBeUndefined();
    mockSignInWithPopup.mockRejectedValue(blocked);
    mockSignInWithRedirect.mockResolvedValue(undefined as never);

    await useAuthStore.getState().loginWithGoogle();

    expect(mockSignInWithPopup).toHaveBeenCalledTimes(1);
    expect(mockSignInWithRedirect).toHaveBeenCalledTimes(1);
    expect(mockSignInWithRedirect.mock.calls[0][1]).toBe(mockSignInWithPopup.mock.calls[0][1]);
  });

  it('loginWithDiscord / loginWithX / loginWithMyAnimeList: each opens a popup with auth, and each falls back to redirect on a blocked popup', async () => {
    const useAuthStore = await freshStore();
    mockSignInWithPopup.mockResolvedValue({} as never);

    await useAuthStore.getState().loginWithDiscord();
    await useAuthStore.getState().loginWithX();
    await useAuthStore.getState().loginWithMyAnimeList();

    expect(mockSignInWithPopup).toHaveBeenCalledTimes(3);
    for (const call of mockSignInWithPopup.mock.calls) {
      expect(call[0]).toBe(fakeAuth);
    }

    const blocked = new Error('blocked');
    (blocked as unknown as { code: string }).code = 'auth/popup-blocked';
    mockSignInWithPopup.mockRejectedValue(blocked);
    mockSignInWithRedirect.mockResolvedValue(undefined as never);

    await useAuthStore.getState().loginWithDiscord();
    await useAuthStore.getState().loginWithX();
    await useAuthStore.getState().loginWithMyAnimeList();

    expect(mockSignInWithRedirect).toHaveBeenCalledTimes(3);
  });

  it('logout: calls signOut with auth; on error resets isLoading and re-throws', async () => {
    const useAuthStore = await freshStore();
    mockSignOut.mockResolvedValue(undefined as never);
    useAuthStore.setState({ user: sampleUser, isAuthenticated: true, isLoading: false });

    await useAuthStore.getState().logout();
    expect(mockSignOut).toHaveBeenCalledWith(fakeAuth);

    mockSignOut.mockRejectedValue(new Error('network'));
    await expect(useAuthStore.getState().logout()).rejects.toThrow('network');
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('refetchUser: on success sets user + isAuthenticated', async () => {
    const useAuthStore = await freshStore();
    mockGetAuthUser.mockResolvedValue(sampleUser);

    await useAuthStore.getState().refetchUser();

    const state = useAuthStore.getState();
    expect(mockGetAuthUser).toHaveBeenCalledTimes(1);
    expect(state.user).toEqual(sampleUser);
    expect(state.isAuthenticated).toBe(true);
  });

  it('refetchUser: on failure logs error and leaves auth state unchanged', async () => {
    const useAuthStore = await freshStore();
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockGetAuthUser.mockRejectedValue(new Error('401'));
    useAuthStore.setState({ user: null, isAuthenticated: false });

    await useAuthStore.getState().refetchUser();

    expect(errSpy).toHaveBeenCalled();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('checkAuth: wires onAuthStateChanged; authed user => sets user, connects notifications', async () => {
    const useAuthStore = await freshStore();
    mockGetAuthUser.mockResolvedValue(sampleUser);
    let callback!: (u: unknown) => void | Promise<void>;
    mockOnAuthStateChanged.mockImplementation(((authArg: unknown, cb: unknown) => {
      expect(authArg).toBe(fakeAuth);
      callback = cb as (u: unknown) => void | Promise<void>;
      return vi.fn(); // unsubscribe
    }) as never);

    await useAuthStore.getState().checkAuth();
    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);

    // Simulate firebase reporting a signed-in user
    await callback({ uid: 'abc' });

    const state = useAuthStore.getState();
    expect(state.user).toEqual(sampleUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
    expect(connect).toHaveBeenCalledTimes(1);
    expect(disconnect).not.toHaveBeenCalled();
  });

  it('checkAuth: null firebaseUser => clears state and disconnects notifications', async () => {
    const useAuthStore = await freshStore();
    let callback!: (u: unknown) => void | Promise<void>;
    mockOnAuthStateChanged.mockImplementation(((_authArg: unknown, cb: unknown) => {
      callback = cb as (u: unknown) => void | Promise<void>;
      return vi.fn();
    }) as never);
    useAuthStore.setState({ user: sampleUser, isAuthenticated: true, isLoading: true });

    await useAuthStore.getState().checkAuth();
    await callback(null);

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(disconnect).toHaveBeenCalledTimes(1);
    expect(connect).not.toHaveBeenCalled();
  });

  it('checkAuth: authed user but getAuthUser fails => clears state, isLoading false', async () => {
    const useAuthStore = await freshStore();
    mockGetAuthUser.mockRejectedValue(new Error('backend down'));
    let callback!: (u: unknown) => void | Promise<void>;
    mockOnAuthStateChanged.mockImplementation(((_authArg: unknown, cb: unknown) => {
      callback = cb as (u: unknown) => void | Promise<void>;
      return vi.fn();
    }) as never);

    await useAuthStore.getState().checkAuth();
    await callback({ uid: 'abc' });

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });

  it('checkAuth: auth null (config Firebase absente au build) => isLoading false, aucun listener', async () => {
    // Régression prod 2026-07-10 : bundle construit sans VITE_FIREBASE_* →
    // auth null → onAuthStateChanged(null) throwait et isLoading restait true
    // pour toujours (tous les boutons d'auth gelés sur « Chargement... »).
    vi.resetModules();
    vi.doMock('../../utils/firebase', () => ({ auth: null }));
    const { useAuthStore } = await import('../authStore');

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(mockOnAuthStateChanged).not.toHaveBeenCalled();
    // Ré-enregistre le mock nominal (doUnmock rendrait le VRAI module aux
    // imports suivants, dont l'init échoue en test → auth null partout).
    vi.doMock('../../utils/firebase', () => ({ auth: fakeAuth }));
  });

  it('checkAuth: second invocation is a no-op (listener wired at most once)', async () => {
    const useAuthStore = await freshStore();
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();
    await useAuthStore.getState().checkAuth();

    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);
  });

  // ── Redirect-fallback return leg ──────────────────────────────────────────
  // getRedirectResult(auth) must be called once on boot so a user coming back
  // from the signInWithRedirect fallback actually ends up signed in, no
  // matter which route the browser lands them on.

  it('checkAuth: getRedirectResult resolving null on boot is a silent no-op', async () => {
    const useAuthStore = await freshStore();
    mockGetRedirectResult.mockResolvedValue(null);
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();

    expect(mockGetRedirectResult).toHaveBeenCalledTimes(1);
    expect(mockGetRedirectResult.mock.calls[0][0]).toBe(fakeAuth);
    expect(addToast).not.toHaveBeenCalled();
    // Still falls through to wiring the normal auth-state listener.
    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);
  });

  it('checkAuth: a successful redirect result signs the user in', async () => {
    const useAuthStore = await freshStore();
    mockGetAuthUser.mockResolvedValue(sampleUser);
    mockGetRedirectResult.mockResolvedValue({ user: { uid: 'abc' } } as never);
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.user).toEqual(sampleUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
    expect(connect).toHaveBeenCalledTimes(1);
  });

  it('checkAuth: an error on the redirect return leg surfaces via authErrorMessage as a toast', async () => {
    const useAuthStore = await freshStore();
    const err = new Error('account exists');
    (err as unknown as { code: string }).code = 'auth/account-exists-with-different-credential';
    mockGetRedirectResult.mockRejectedValue(err);
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();

    expect(addToast).toHaveBeenCalledTimes(1);
    expect(addToast.mock.calls[0][0]).toMatch(/liée à une autre méthode/i);
    // Still wires the listener afterwards — a redirect error must not brick auth.
    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);
  });

  it('checkAuth: an error on the redirect return leg is localized through the app i18n singleton (English), not hardcoded French', async () => {
    // Regression guard: the toast used to come from a `fallbackT` shim that
    // ignored the translation key entirely and always returned authErrors.ts's
    // French fallback string — so an English-speaking visitor who hit an
    // error on the redirect-return leg got a French toast, while the exact
    // same error through the popup path (LoginPage/RegisterPage, which pass
    // the real `t` from useTranslation()) rendered correctly in English.
    //
    // Simulate the real i18n singleton as it would be for an English visitor
    // (translation.json's `auth.error.*` resources loaded) instead of the
    // fallback-pass-through default mocked above for every other test here.
    vi.resetModules();
    const EN_OTHER_PROVIDER =
      'This address is already linked to another sign-in method. Use the one you created the account with.';
    vi.doMock('../../i18n/config', () => ({
      default: {
        t: (key: string, fallback?: string) =>
          key === 'auth.error.other_provider' ? EN_OTHER_PROVIDER : (fallback ?? key),
      },
    }));
    const { useAuthStore } = await import('../authStore');

    const err = new Error('account exists');
    (err as unknown as { code: string }).code = 'auth/account-exists-with-different-credential';
    mockGetRedirectResult.mockRejectedValue(err);
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();

    expect(addToast).toHaveBeenCalledTimes(1);
    expect(addToast.mock.calls[0][0]).toBe(EN_OTHER_PROVIDER);
    expect(addToast.mock.calls[0][0]).not.toMatch(/liée à une autre méthode/i);

    // Restore the nominal fallback-pass-through mock for subsequent tests —
    // doUnmock would hand the REAL i18n/config module to later imports,
    // which eagerly calls i18n.init() and is unnecessary/unwanted here.
    vi.doMock('../../i18n/config', () => ({
      default: { t: (key: string, fallback?: string) => fallback ?? key },
    }));
  });

  it('checkAuth: a user-cancelled error on the redirect return leg stays silent (no toast)', async () => {
    const useAuthStore = await freshStore();
    const err = new Error('cancelled');
    (err as unknown as { code: string }).code = 'auth/user-cancelled';
    mockGetRedirectResult.mockRejectedValue(err);
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();

    expect(addToast).not.toHaveBeenCalled();
    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);
  });
});
