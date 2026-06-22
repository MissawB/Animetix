import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// jsdom does not implement scrollIntoView; components that auto-scroll (e.g.
// chat/history views) call it in effects on mount.
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn();
}

// Stub the Firebase client module globally.
// src/utils/firebase.ts eagerly calls getAuth()/getAnalytics() at import time,
// which throws `auth/invalid-api-key` whenever the VITE_FIREBASE_* env vars are
// absent (CI, fresh checkout). Any test whose import graph reaches firebase.ts
// would otherwise fail to load. Tests needing real auth behavior override this
// with their own vi.mock (a per-file mock takes precedence over this one).
vi.mock('../utils/firebase', () => ({
  app: {},
  auth: { currentUser: null },
  analytics: {},
}));

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
global.fetch = vi.fn(async (_input) => {
  return {
    ok: true,
    status: 200,
    json: async () => ([]),
    text: async () => '',
    blob: async () => new Blob(),
  } as Response;
});

