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

// Mock react-i18next.
// Mirrors runtime behavior with no translations loaded: t('key') -> 'key',
// t('key', 'défaut') -> 'défaut', t('key', { defaultValue, ...vars }) ->
// defaultValue with {{var}} interpolation. Tests can keep asserting the
// French defaultValue text.
vi.mock('react-i18next', () => ({
  useTranslation: () => {
    return {
      t: (key: string, arg2?: unknown, arg3?: unknown) => {
        const opts = (arg2 !== null && typeof arg2 === 'object' ? arg2
          : arg3 !== null && typeof arg3 === 'object' ? arg3
          : {}) as Record<string, unknown>;
        const def = typeof arg2 === 'string' ? arg2
          : typeof opts.defaultValue === 'string' ? opts.defaultValue
          : undefined;
        return (def ?? key).replace(/\{\{(\w+)\}\}/g, (m, name: string) =>
          name in opts ? String(opts[name]) : m,
        );
      },
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

