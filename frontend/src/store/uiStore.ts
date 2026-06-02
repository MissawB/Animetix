import { create } from 'zustand';
import soundManager from '../utils/SoundManager';
import i18n from 'i18next';

interface UIState {
  isSidebarOpen: boolean;
  isSettingsOpen: boolean;
  theme: string;
  mediaType: 'Anime' | 'Manga' | 'Character';
  difficulty: 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Custom';
  currentLang: 'Français' | 'English';
  toggleSidebar: (forceClose?: boolean) => void;
  toggleSettings: (forceClose?: boolean) => void;
  setTheme: (theme: string) => void;
  setMediaType: (mode: 'Anime' | 'Manga' | 'Character') => void;
  setDifficulty: (diff: 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Custom') => void;
  setCurrentLang: (lang: 'Français' | 'English') => void;
  playClick: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  isSidebarOpen: false,
  isSettingsOpen: false,
  theme: localStorage.getItem('theme') || 'auto',
  mediaType: (localStorage.getItem('media_type') as any) || 'Anime',
  difficulty: (localStorage.getItem('difficulty') as any) || 'Normal',
  currentLang: i18n.language === 'en' ? 'English' : 'Français',
  
  toggleSidebar: (forceClose) => {
    soundManager.play('click');
    set((state) => ({ 
      isSidebarOpen: forceClose !== undefined ? !forceClose : !state.isSidebarOpen,
      isSettingsOpen: forceClose ? false : state.isSettingsOpen 
    }));
  },
  
  toggleSettings: (forceClose) => {
    soundManager.play('click');
    set((state) => ({ 
      isSettingsOpen: forceClose !== undefined ? !forceClose : !state.isSettingsOpen,
      isSidebarOpen: forceClose ? false : state.isSidebarOpen
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

  setMediaType: (mode) => {
    soundManager.play('click');
    localStorage.setItem('media_type', mode);
    set({ mediaType: mode });
  },

  setDifficulty: (diff) => {
    soundManager.play('click');
    localStorage.setItem('difficulty', diff);
    set({ difficulty: diff });
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
