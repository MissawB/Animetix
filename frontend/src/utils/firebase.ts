import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'fake-api-key',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'fake-auth-domain',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'fake-project-id',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || 'fake-app-id',
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

const emulatorHost = import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST;
if (emulatorHost) {
  connectAuthEmulator(auth, `http://${emulatorHost}`);
}
