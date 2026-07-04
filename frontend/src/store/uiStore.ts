import { create } from 'zustand';
import soundManager from '../utils/SoundManager';
import i18n from 'i18next';

interface UIState {
  isSidebarOpen: boolean;
  isSettingsOpen: boolean;
  theme: string;
  currentLang: 'Français' | 'English';
  toggleSidebar: (forceClose?: boolean) => void;
  toggleSettings: (forceClose?: boolean) => void;
  setTheme: (theme: string) => void;
  setCurrentLang: (lang: 'Français' | 'English') => void;
  playClick: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: false,
  isSettingsOpen: false,
  theme: localStorage.getItem('theme') || 'auto',
  currentLang: i18n.language === 'en' ? 'English' : 'Français',
  
  toggleSidebar: (forceClose) => {
    soundManager.play('click');
    set((state) => ({ 
      isSidebarOpen: forceClose !== undefined ? !forceClose : !state.isSidebarOpen,
      isSettingsOpen: forceClose === true ? false : state.isSettingsOpen 
    }));
  },
  
  toggleSettings: (forceClose) => {
    soundManager.play('click');
    set((state) => ({ 
      isSettingsOpen: forceClose !== undefined ? !forceClose : !state.isSettingsOpen,
      isSidebarOpen: forceClose === true ? false : state.isSidebarOpen
    }));
  },
  
  setTheme: (theme: string) => {
    const html = document.documentElement;
    const actualTheme = theme === 'auto' 
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;

    if (actualTheme === 'dark') {
      html.classList.add('dark');
      html.setAttribute('data-bs-theme', 'dark');
    } else {
      html.classList.remove('dark');
      html.setAttribute('data-bs-theme', 'light');
    }
    
    localStorage.setItem('theme', theme);
    set({ theme });
  },

  setCurrentLang: (lang) => {
    soundManager.play('click');
    const code = lang === 'English' ? 'en' : 'fr';
    i18n.changeLanguage(code);
    
    // Recalculate basename or reload if router needs update, but setting state is standard
    set({ currentLang: lang });
  },

  playClick: () => soundManager.play('click'),
}));
