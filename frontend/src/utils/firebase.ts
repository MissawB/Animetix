import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, type Auth } from 'firebase/auth';
import { getAnalytics, type Analytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

// Initialise defensively. A missing/invalid VITE_FIREBASE_* config (e.g. the build
// ran without env vars) used to throw `auth/invalid-api-key` at import time, which
// crashed the entire SPA and rendered a blank page. We now catch that: on failure we
// log and leave the handles null, so Firebase-backed features (login, analytics)
// degrade at call time instead of killing the whole app at load.
let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;
let _analytics: Analytics | null = null;

try {
  if (!firebaseConfig.apiKey) {
    throw new Error('VITE_FIREBASE_API_KEY is not set at build time');
  }
  _app = initializeApp(firebaseConfig);
  _auth = getAuth(_app);
  _analytics = getAnalytics(_app);

  const emulatorHost = import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST;
  if (emulatorHost) {
    connectAuthEmulator(_auth, `http://${emulatorHost}`);
  }
} catch (err) {
  console.error(
    '[firebase] initialization skipped — auth & analytics are disabled. ' +
      'Provide VITE_FIREBASE_* at build time to enable them.',
    err
  );
}

// Exported types stay non-null so existing consumers compile unchanged. At runtime
// these are null only when the Firebase config is absent, in which case the features
// fail at call time (handled by callers) rather than at module load.
export const app = _app as FirebaseApp;
export const auth = _auth as Auth;
export const analytics = _analytics as Analytics;
