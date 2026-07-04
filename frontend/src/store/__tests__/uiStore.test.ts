import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock SoundManager so no Howler/audio is constructed and we can assert clicks.
const playMock = vi.fn();
vi.mock('../../utils/SoundManager', () => ({
  default: { play: (...args: unknown[]) => playMock(...args) },
}));

// Mock i18next so the store import resolves without a real i18n instance.
const changeLanguageMock = vi.fn();
vi.mock('i18next', () => ({
  default: {
    language: 'fr',
    changeLanguage: (...args: unknown[]) => changeLanguageMock(...args),
  },
}));

import { useUIStore } from '../uiStore';

describe('useUIStore', () => {
  beforeEach(() => {
    localStorage.clear();
    playMock.mockClear();
    changeLanguageMock.mockClear();
    document.documentElement.className = '';
    document.documentElement.removeAttribute('data-bs-theme');
    // Reset to a known baseline.
    useUIStore.setState({
      isSidebarOpen: false,
      isSettingsOpen: false,
      theme: 'auto',
      currentLang: 'Français',
    });
  });

  it('initializes with sidebar and settings closed', () => {
    const state = useUIStore.getState();
    expect(state.isSidebarOpen).toBe(false);
    expect(state.isSettingsOpen).toBe(false);
  });

  it('toggleSidebar flips the sidebar and plays a click', () => {
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().isSidebarOpen).toBe(true);
    expect(playMock).toHaveBeenCalledWith('click');

    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().isSidebarOpen).toBe(false);
  });

  it('toggleSidebar with forceClose=true closes sidebar and settings', () => {
    useUIStore.setState({ isSidebarOpen: true, isSettingsOpen: true });
    useUIStore.getState().toggleSidebar(true);
    const state = useUIStore.getState();
    expect(state.isSidebarOpen).toBe(false);
    expect(state.isSettingsOpen).toBe(false);
  });

  it('toggleSidebar with forceClose=false opens the sidebar but leaves settings untouched', () => {
    useUIStore.setState({ isSidebarOpen: false, isSettingsOpen: true });
    useUIStore.getState().toggleSidebar(false);
    const state = useUIStore.getState();
    expect(state.isSidebarOpen).toBe(true);
    expect(state.isSettingsOpen).toBe(true);
  });

  it('toggleSettings flips settings and closes the sidebar when forceClose=true', () => {
    useUIStore.getState().toggleSettings();
    expect(useUIStore.getState().isSettingsOpen).toBe(true);
    expect(playMock).toHaveBeenCalledWith('click');

    useUIStore.setState({ isSidebarOpen: true, isSettingsOpen: true });
    useUIStore.getState().toggleSettings(true);
    const state = useUIStore.getState();
    expect(state.isSettingsOpen).toBe(false);
    expect(state.isSidebarOpen).toBe(false);
  });

  it('setTheme="dark" adds the dark class, sets data-bs-theme, and persists', () => {
    useUIStore.getState().setTheme('dark');
    expect(useUIStore.getState().theme).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.getAttribute('data-bs-theme')).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('setTheme="light" removes the dark class and persists', () => {
    document.documentElement.classList.add('dark');
    useUIStore.getState().setTheme('light');
    expect(useUIStore.getState().theme).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.getAttribute('data-bs-theme')).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('setTheme="auto" resolves via matchMedia and persists the literal "auto"', () => {
    // jsdom does not implement matchMedia; define it so "auto" resolves to dark.
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn((query: string) => ({
        matches: true,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    useUIStore.getState().setTheme('auto');
    // matchMedia.matches=true => resolves to dark.
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    // The raw preference (not the resolved value) is persisted.
    expect(localStorage.getItem('theme')).toBe('auto');
    expect(useUIStore.getState().theme).toBe('auto');
  });

  it('setCurrentLang updates state and maps English/Français to en/fr', () => {
    useUIStore.getState().setCurrentLang('English');
    expect(useUIStore.getState().currentLang).toBe('English');
    expect(changeLanguageMock).toHaveBeenCalledWith('en');

    useUIStore.getState().setCurrentLang('Français');
    expect(useUIStore.getState().currentLang).toBe('Français');
    expect(changeLanguageMock).toHaveBeenCalledWith('fr');
  });

  it('playClick plays the click sound', () => {
    useUIStore.getState().playClick();
    expect(playMock).toHaveBeenCalledWith('click');
  });
});
