import { create } from 'zustand';
import type { TFunction } from 'i18next';
import { authService } from '../features/auth/services/authService';
import { User } from '../types';
import { useNotificationStore } from './notificationStore';
import { useToastStore } from './toastStore';
import { auth } from '../utils/firebase';
import { authErrorMessage } from '../utils/authErrors';
import i18n from '../i18n/config';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  OAuthProvider,
  TwitterAuthProvider,
  sendPasswordResetEmail,
  type AuthProvider,
  type User as FirebaseUser,
} from 'firebase/auth';

// Codes where the user deliberately backed out of the Google/social popup
// (closed it, or another popup request superseded it). Falling back to a
// full-page redirect here would hijack the browser right after someone
// chose to cancel — so these must keep rejecting exactly as before.
const POPUP_USER_CANCELLED_CODES = new Set([
  'auth/popup-closed-by-user',
  'auth/cancelled-popup-request',
  'auth/user-cancelled',
]);

const errorCodeOf = (error: unknown): string | undefined => {
  const code = (error as { code?: unknown } | null | undefined)?.code;
  return typeof code === 'string' ? code : undefined;
};

/**
 * Try the popup first — it's the better experience (no page reload, no lost
 * in-page state) and works for the overwhelming majority of users. Ad
 * blockers/privacy extensions and browsers that block popups outright kill
 * signInWithPopup with net::ERR_BLOCKED_BY_CLIENT before Google ever loads;
 * without a fallback those users simply cannot sign in. Only skip the
 * fallback when the user explicitly cancelled — see POPUP_USER_CANCELLED_CODES.
 */
async function signInWithPopupOrRedirectFallback(provider: AuthProvider): Promise<void> {
  try {
    await signInWithPopup(auth, provider);
  } catch (error) {
    if (POPUP_USER_CANCELLED_CODES.has(errorCodeOf(error) ?? '')) {
      throw error;
    }
    await signInWithRedirect(auth, provider);
  }
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  refetchUser: () => Promise<void>;
  login: (data: Record<string, string>) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  loginWithDiscord: () => Promise<void>;
  loginWithX: () => Promise<void>;
  loginWithMyAnimeList: () => Promise<void>;
  register: (data: Record<string, string>) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

let authListenerInitialized = false;

export const useAuthStore = create<AuthState>((set) => {
  const applyFirebaseUser = async (firebaseUser: FirebaseUser | null) => {
    if (firebaseUser) {
      try {
        const user = await authService.getAuthUser();
        set({ user, isAuthenticated: true, isLoading: false });
        useNotificationStore.getState().connect();
      } catch (_error) {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ user: null, isAuthenticated: false, isLoading: false });
      useNotificationStore.getState().disconnect();
    }
  };

  return {
    user: null,
    isAuthenticated: false,
    isLoading: true,
    refetchUser: async () => {
      try {
        const user = await authService.getAuthUser();
        set({ user, isAuthenticated: true });
      } catch (error) {
        console.error('Failed to refetch user data:', error);
      }
    },
    checkAuth: async () => {
      if (authListenerInitialized) return;
      authListenerInitialized = true;

      // `auth` est null quand la config Firebase manque au build (voir
      // utils/firebase). Sans ce garde, onAuthStateChanged(null) throw et
      // isLoading reste true pour toujours : tous les boutons d'auth restent
      // gelés sur « Chargement... » (vécu en prod le 2026-07-10).
      if (!auth) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }

      // Return leg of the signInWithPopup -> signInWithRedirect fallback. The
      // redirect can land the user back on any route (not just the login
      // page), so this has to run once at app boot, not inside a page
      // component. `null` is the normal case (this load isn't a redirect
      // return) and is a silent no-op; onAuthStateChanged below still fires
      // for it either way.
      //
      // Non-component code (this store) has no `useTranslation()` `t()`
      // available, but the app's i18n singleton (src/i18n/config.ts) is
      // already initialised before AuthProvider mounts, so it's used
      // directly here — the same localized strings LoginPage/RegisterPage
      // get via useTranslation(), not a hardcoded-French fallback.
      try {
        const redirectResult = await getRedirectResult(auth);
        if (redirectResult) {
          await applyFirebaseUser(redirectResult.user);
        }
      } catch (error) {
        const message = authErrorMessage(error, i18n.t.bind(i18n) as TFunction);
        if (message) {
          useToastStore.getState().addToast(message, 'error');
        }
      }

      onAuthStateChanged(auth, async (firebaseUser) => {
        await applyFirebaseUser(firebaseUser);
      });
    },
    login: async (data: Record<string, string>) => {
      set({ isLoading: true });
      try {
        await signInWithEmailAndPassword(auth, data.email, data.password);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    loginWithGoogle: async () => {
      set({ isLoading: true });
      try {
        const provider = new GoogleAuthProvider();
        await signInWithPopupOrRedirectFallback(provider);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    loginWithDiscord: async () => {
      set({ isLoading: true });
      try {
        const provider = new OAuthProvider('oauth.discord');
        provider.addScope('identify');
        provider.addScope('email');
        await signInWithPopupOrRedirectFallback(provider);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    loginWithX: async () => {
      set({ isLoading: true });
      try {
        const provider = new TwitterAuthProvider();
        await signInWithPopupOrRedirectFallback(provider);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    loginWithMyAnimeList: async () => {
      set({ isLoading: true });
      try {
        const provider = new OAuthProvider('oauth.myanimelist');
        await signInWithPopupOrRedirectFallback(provider);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    register: async (data: Record<string, string>) => {
      set({ isLoading: true });
      try {
        await createUserWithEmailAndPassword(auth, data.email, data.password);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    resetPassword: async (email: string) => {
      // Deliberately NOT wrapped in isLoading: the login form stays usable while
      // the mail goes out. Callers swallow auth/user-not-found — see LoginPage.
      await sendPasswordResetEmail(auth, email);
    },
    logout: async () => {
      set({ isLoading: true });
      try {
        await signOut(auth);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
  };
});
