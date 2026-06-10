import { create } from 'zustand';
import { getAuthUser } from '../api';
import { User } from '../types';
import { useNotificationStore } from './notificationStore';
import { auth } from '../utils/firebase';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  OAuthProvider,
  TwitterAuthProvider
} from 'firebase/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  login: (data: Record<string, any>) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  loginWithDiscord: () => Promise<void>;
  loginWithX: () => Promise<void>;
  loginWithMyAnimeList: () => Promise<void>;
  register: (data: Record<string, any>) => Promise<void>;
  logout: () => Promise<void>;
}

let authListenerInitialized = false;

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  checkAuth: async () => {
    if (authListenerInitialized) return;
    authListenerInitialized = true;
    
    onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const user = await getAuthUser();
          set({ user, isAuthenticated: true, isLoading: false });
          useNotificationStore.getState().connect();
        } catch (error) {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
        useNotificationStore.getState().disconnect();
      }
    });
  },
  login: async (data) => {
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
      await signInWithPopup(auth, provider);
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
      await signInWithPopup(auth, provider);
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  loginWithX: async () => {
    set({ isLoading: true });
    try {
      const provider = new TwitterAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  loginWithMyAnimeList: async () => {
    set({ isLoading: true });
    try {
      const provider = new OAuthProvider('oauth.myanimelist');
      await signInWithPopup(auth, provider);
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  register: async (data) => {
    set({ isLoading: true });
    try {
      await createUserWithEmailAndPassword(auth, data.email, data.password);
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
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
}));
