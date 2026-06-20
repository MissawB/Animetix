import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// jsdom does not implement scrollIntoView; components that auto-scroll (e.g.
// chat/history views) call it in effects on mount.
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn();
}

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => {
    return {
      t: (key: string) => key,
      i18n: {
        changeLanguage: () => new Promise(() => {}),
        language: 'en',
      },
    };
  },
  initReactI18next: {
    type: '3rdParty',
    init: () => {},
  }
}));

afterEach(() => {
  cleanup();
});

// Fallback fetch mock to prevent relative URL fetch failures in JSDOM tests
global.fetch = vi.fn(async (input) => {
  return {
    ok: true,
    status: 200,
    json: async () => ([]),
    text: async () => '',
    blob: async () => new Blob(),
  } as Response;
});

