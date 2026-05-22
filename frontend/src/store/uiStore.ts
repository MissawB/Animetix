import { create } from 'zustand';
import soundManager from '../utils/SoundManager';

interface UIState {
  isSidebarOpen: boolean;
  theme: string;
  toggleSidebar: () => void;
  setTheme: (theme: string) => void;
  playClick: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: false,
  theme: localStorage.getItem('theme') || 'auto',
  
  toggleSidebar: () => {
    soundManager.play('click');
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen }));
  },
  
  setTheme: (theme: string) => {
    const html = document.documentElement;
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
    set({ theme });
  },

  playClick: () => soundManager.play('click'),
}));
