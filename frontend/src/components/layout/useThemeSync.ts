import { useEffect } from 'react';

/**
 * Synchronizes the document theme (light/dark/auto) and the optional
 * user-custom visual theme class onto the root <html> element.
 *
 * Behavior is identical to the inline effects previously living in Layout:
 * the two effects are kept separate (and in the same order) so dependency
 * arrays and execution semantics are preserved exactly.
 */
export const useThemeSync = (theme: string, visualTheme: string | undefined): void => {
  // Sync theme
  useEffect(() => {
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
  }, [theme]);

  // Sync visual themes from user custom config
  useEffect(() => {
    if (visualTheme) {
      const themes = ['theme-naruto', 'theme-manga-classic'];
      document.documentElement.classList.remove(...themes);
      if (visualTheme !== 'default') {
        document.documentElement.classList.add(`theme-${visualTheme}`);
      }
    }
  }, [visualTheme]);
};
