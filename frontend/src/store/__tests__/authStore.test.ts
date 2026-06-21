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
  GoogleAuthProvider: vi.fn(function GoogleAuthProvider() {}),
  OAuthProvider: vi.fn(function OAuthProvider() {
    return { addScope: vi.fn() };
  }),
  TwitterAuthProvider: vi.fn(function TwitterAuthProvider() {}),
}));

// --- Mock the API getAuthUser call ---
vi.mock('../../api', () => ({
  getAuthUser: vi.fn(),
}));

// --- Mock the notification store (connect/disconnect are side effects) ---
const connect = vi.fn();
const disconnect = vi.fn();
vi.mock('../notificationStore', () => ({
  useNotificationStore: {
    getState: () => ({ connect, disconnect }),
  },
}));

import * as firebaseAuth from 'firebase/auth';
import * as api from '../../api';

const mockGetAuthUser = vi.mocked(api.getAuthUser);
const mockSignIn = vi.mocked(firebaseAuth.signInWithEmailAndPassword);
const mockCreateUser = vi.mocked(firebaseAuth.createUserWithEmailAndPassword);
const mockSignOut = vi.mocked(firebaseAuth.signOut);
const mockOnAuthStateChanged = vi.mocked(firebaseAuth.onAuthStateChanged);
const mockSignInWithPopup = vi.mocked(firebaseAuth.signInWithPopup);

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
      useAuthStore.getState().login({ email: 'a@b.com', password: 'wrong' })
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
      useAuthStore.getState().register({ email: 'dup@b.com', password: 'pw' })
    ).rejects.toThrow('email in use');
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('loginWithGoogle: opens popup with auth; on error resets isLoading and re-throws', async () => {
    const useAuthStore = await freshStore();
    mockSignInWithPopup.mockResolvedValue({} as never);
    await useAuthStore.getState().loginWithGoogle();
    expect(mockSignInWithPopup).toHaveBeenCalledTimes(1);
    expect(mockSignInWithPopup.mock.calls[0][0]).toBe(fakeAuth);

    mockSignInWithPopup.mockRejectedValue(new Error('popup closed'));
    await expect(useAuthStore.getState().loginWithGoogle()).rejects.toThrow('popup closed');
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it('loginWithDiscord / loginWithX / loginWithMyAnimeList: each opens a popup with auth', async () => {
    const useAuthStore = await freshStore();
    mockSignInWithPopup.mockResolvedValue({} as never);

    await useAuthStore.getState().loginWithDiscord();
    await useAuthStore.getState().loginWithX();
    await useAuthStore.getState().loginWithMyAnimeList();

    expect(mockSignInWithPopup).toHaveBeenCalledTimes(3);
    for (const call of mockSignInWithPopup.mock.calls) {
      expect(call[0]).toBe(fakeAuth);
    }
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

  it('checkAuth: second invocation is a no-op (listener wired at most once)', async () => {
    const useAuthStore = await freshStore();
    mockOnAuthStateChanged.mockImplementation((() => vi.fn()) as never);

    await useAuthStore.getState().checkAuth();
    await useAuthStore.getState().checkAuth();

    expect(mockOnAuthStateChanged).toHaveBeenCalledTimes(1);
  });
});
