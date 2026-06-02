import { create } from 'zustand';
import { getAuthUser, loginUser, registerUser, logoutUser } from '../api';
import { User } from '../types';
import { useNotificationStore } from './notificationStore';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  login: (data: Record<string, any>) => Promise<void>;
  register: (data: Record<string, any>) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  checkAuth: async () => {
    try {
      const user = await getAuthUser();
      set({ user, isAuthenticated: true, isLoading: false });
      useNotificationStore.getState().connect();
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
  login: async (data) => {
    set({ isLoading: true });
    try {
      const user = await loginUser(data);
      set({ user, isAuthenticated: true, isLoading: false });
      useNotificationStore.getState().connect();
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  register: async (data) => {
    set({ isLoading: true });
    try {
      const user = await registerUser(data);
      set({ user, isAuthenticated: true, isLoading: false });
      useNotificationStore.getState().connect();
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  logout: async () => {
    set({ isLoading: true });
    try {
      await logoutUser();
      set({ user: null, isAuthenticated: false, isLoading: false });
      useNotificationStore.getState().disconnect();
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
}));
