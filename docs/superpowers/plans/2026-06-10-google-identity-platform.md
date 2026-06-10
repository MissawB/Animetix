# Google Identity Platform Authentication Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate application authentication from local sessions and allauth to a managed Google Identity Platform (Firebase Auth client-side SDK and PyJWT verification on the Django backend).

**Architecture:** The React frontend authenticates users directly with Google Identity Platform (using Firebase Client SDK) and obtains a JWT ID Token. This token is passed in the `Authorization: Bearer <ID_TOKEN>` header for all API calls. The Django backend decodes and validates the token signature using cached Google public keys, automatically provisioning Django users on demand.

**Tech Stack:** React, Zustand, Firebase Auth JS SDK, Django, Django REST Framework, PyJWT.

---

## Proposed Changes Mapping

### Component: Frontend Authentication & API Client
- Create: `frontend/src/utils/firebase.ts` (Firebase Client SDK configuration)
- Modify: `frontend/src/utils/apiClient.ts` (Bearer token injection in requests)
- Modify: `frontend/src/store/authStore.ts` (Zustand store integration with Firebase)
- Modify: `frontend/src/pages/auth/LoginPage.tsx` (Use email instead of username, add Google Auth button)

### Component: Backend Django REST Framework
- Modify: `backend/api/animetix/auth.py` (Add `GoogleIdentityAuthentication` class)
- Modify: `backend/api/animetix_project/settings.py` (Register `GoogleIdentityAuthentication` as default)
- Modify: `backend/api/animetix/api/core.py` (Deprecate local sign-in/sign-up endpoints)
- Create: `tests/backend/test_gcip_auth.py` (Unit tests for the new authenticator)

---

## Tasks

### Task 1: Initialize Firebase Client SDK & Configure API Client

**Files:**
- Create: `frontend/src/utils/firebase.ts`
- Modify: `frontend/src/utils/apiClient.ts`

- [ ] **Step 1: Create Firebase Client configuration file**
  Create `frontend/src/utils/firebase.ts` with the following content:
  ```typescript
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
  ```

- [ ] **Step 2: Update API Client to inject ID Token**
  Modify `frontend/src/utils/apiClient.ts` to retrieve the current Firebase ID Token dynamically on each request and inject it in the `Authorization` header:
  ```typescript
  import { useToastStore } from '../store/toastStore';
  import { usePersonalizationStore } from '../store/personalizationStore';
  import { auth } from './firebase';

  export const apiClient = async (url: string, options: RequestInit & { skipToast?: boolean; isFormData?: boolean } = {}) => {
    const { skipToast, isFormData, ...fetchOptions } = options;
    const defaultHeaders: Record<string, string> = {
      'X-Requested-With': 'XMLHttpRequest',
    };

    if (!isFormData) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    // Inject Google Identity Platform ID Token if user is logged in
    const firebaseUser = auth.currentUser;
    if (firebaseUser) {
      try {
        const token = await firebaseUser.getIdToken();
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      } catch (err) {
        console.error("Failed to retrieve Firebase ID Token", err);
      }
    }

    // Récupération du CSRF Token
    const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
    if (match) {
      (defaultHeaders as Record<string, string>)['X-CSRFToken'] = match[2];
    }

    const config: RequestInit = {
      ...fetchOptions,
      headers: { ...defaultHeaders, ...fetchOptions.headers },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.message || `Erreur ${response.status}: Impossible de récupérer les données.`;
        
        if (!skipToast) {
          useToastStore.getState().addToast(errorMessage, 'error');
        }
        
        throw new Error(errorMessage);
      }

      if (response.status === 204) return null;

      const data = await response.json();

      const visualConfig = data?.meta?.visual_config;
      if (visualConfig) {
        usePersonalizationStore.getState().updateConfig(visualConfig);
      }

      return data;
    } catch (error: any) {
      if (error.name === 'TypeError') {
        if (!skipToast) {
          useToastStore.getState().addToast('Serveur injoignable. Vérifiez votre connexion.', 'error');
        }
      }
      throw error;
    }
  };
  ```

- [ ] **Step 3: Commit**
  ```bash
  git add frontend/src/utils/firebase.ts frontend/src/utils/apiClient.ts
  git commit -m "feat(auth): initialize firebase SDK and inject bearer token in API client"
  ```

---

### Task 2: Refactor Frontend Auth Store & Login Page

**Files:**
- Modify: `frontend/src/store/authStore.ts`
- Modify: `frontend/src/pages/auth/LoginPage.tsx`

- [ ] **Step 1: Refactor authStore using Firebase SDK**
  Update `frontend/src/store/authStore.ts` to implement reactive auth state tracking and proxy login/registration/logout to Firebase:
  ```typescript
  import { create } from 'zustand';
  import { getAuthUser } from '../api';
  import { User } from '../types';
  import { useNotificationStore } from './notificationStore';
  import { auth } from '../utils/firebase';
  import { 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword, 
    signOut, 
    onAuthStateChanged,
    GoogleAuthProvider,
    signInWithPopup
  } from 'firebase/auth';

  interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    checkAuth: () => Promise<void>;
    login: (data: Record<string, any>) => Promise<void>;
    loginWithGoogle: () => Promise<void>;
    register: (data: Record<string, any>) => Promise<void>;
    logout: () => Promise<void>;
  }

  let authListenerInitialized = false;

  export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    checkAuth: async () => {
      if (authListenerInitialized) return;
      authListenerInitialized = true;
      
      onAuthStateChanged(auth, async (firebaseUser) => {
        if (firebaseUser) {
          try {
            const user = await getAuthUser();
            set({ user, isAuthenticated: true, isLoading: false });
            useNotificationStore.getState().connect();
          } catch (error) {
            set({ user: null, isAuthenticated: false, isLoading: false });
          }
        } else {
          set({ user: null, isAuthenticated: false, isLoading: false });
          useNotificationStore.getState().disconnect();
        }
      });
    },
    login: async (data) => {
      set({ isLoading: true });
      try {
        await signInWithEmailAndPassword(auth, data.email, data.password);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    loginWithGoogle: async () => {
      set({ isLoading: true });
      try {
        const provider = new GoogleAuthProvider();
        await signInWithPopup(auth, provider);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    register: async (data) => {
      set({ isLoading: true });
      try {
        await createUserWithEmailAndPassword(auth, data.email, data.password);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    logout: async () => {
      set({ isLoading: true });
      try {
        await signOut(auth);
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
  }));
  ```

- [ ] **Step 2: Update LoginPage UI fields and actions**
  Modify `frontend/src/pages/auth/LoginPage.tsx` to use email input instead of username, hook up Google Sign-in button, and trigger `login` or `loginWithGoogle` appropriately:
  ```typescript
  import React, { useState } from 'react';
  import { useNavigate, useSearchParams, Link } from 'react-router-dom';
  import { useAuthStore } from '../../store/authStore';
  import { useTranslation } from 'react-i18next';
  import { LogIn, ArrowLeft } from 'lucide-react';

  const LoginPage: React.FC = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const redirectUrl = searchParams.get('redirect') || '/';

    const { login, loginWithGoogle, isLoading } = useAuthStore();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      try {
        await login({ email, password });
        navigate(redirectUrl);
      } catch (err: any) {
        setError(err.message || t('auth.loginFailed', 'Identifiants incorrects.'));
      }
    };

    const handleGoogleLogin = async () => {
      setError(null);
      try {
        await loginWithGoogle();
        navigate(redirectUrl);
      } catch (err: any) {
        setError(err.message || t('auth.loginFailed', 'Connexion Google échouée.'));
      }
    };

    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-800 p-8 rounded-2xl shadow-xl">
          <Link to="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6 no-underline">
            <ArrowLeft className="w-4 h-4" /> {t('common.back', 'Retour')}
          </Link>
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <LogIn className="text-blue-500" /> {t('auth.loginTitle', 'Connexion')}
          </h2>

          {error && <div className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded-lg mb-4 text-sm">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('auth.email', 'Email')}</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('auth.password', 'Mot de passe')}</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg p-2.5 font-semibold transition-colors flex justify-center items-center gap-2"
            >
              {isLoading ? t('common.loading', 'Chargement...') : t('auth.signIn', 'Se connecter')}
            </button>
          </form>

          <div className="relative flex py-5 items-center">
            <div className="flex-grow border-t border-slate-600"></div>
            <span className="flex-shrink mx-4 text-gray-400 text-sm">OU</span>
            <div className="flex-grow border-t border-slate-600"></div>
          </div>

          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full bg-white text-slate-900 hover:bg-gray-100 disabled:opacity-50 rounded-lg p-2.5 font-semibold transition-colors flex justify-center items-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Se connecter avec Google
          </button>

          <p className="mt-6 text-center text-sm text-gray-400">
            Nouveau sur Animetix ?{' '}
            <Link to="/auth/register/" className="text-blue-500 hover:underline">
              Créer un compte
            </Link>
          </p>
        </div>
      </div>
    );
  };

  export default LoginPage;
  ```

- [ ] **Step 3: Commit**
  ```bash
  git add frontend/src/store/authStore.ts frontend/src/pages/auth/LoginPage.tsx
  git commit -m "feat(auth): refactor Zustand authStore and LoginPage UI for Firebase Auth"
  ```

---

### Task 3: Implement Backend JWT Authenticator

**Files:**
- Modify: `backend/api/animetix/auth.py`

- [ ] **Step 1: Implement GCIP token validation in backend**
  Rewrite `backend/api/animetix/auth.py` to include `GoogleIdentityAuthentication` class using PyJWT and cached certificates:
  ```python
  import logging
  import jwt
  import time
  from django.conf import settings
  from django.contrib.auth import get_user_model
  from rest_framework import authentication
  from rest_framework import exceptions
  import requests

  logger = logging.getLogger('animetix.auth')
  User = get_user_model()

  GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken-system@system.gserviceaccount.com"
  _public_keys_cache = {}
  _public_keys_expiry = 0

  def get_google_public_keys():
      global _public_keys_cache, _public_keys_expiry
      now = time.time()
      if _public_keys_cache and now < _public_keys_expiry:
          return _public_keys_cache

      try:
          response = requests.get(GOOGLE_CERTS_URL, timeout=5)
          response.raise_for_status()
          
          cache_control = response.headers.get("Cache-Control", "")
          max_age = 3600
          for part in cache_control.split(","):
              if "max-age" in part:
                  try:
                      max_age = int(part.split("=")[1].strip())
                  except Exception:
                      pass
          
          _public_keys_cache = response.json()
          _public_keys_expiry = now + max_age
          return _public_keys_cache
      except Exception as e:
          logger.error(f"Failed to fetch Google public keys: {e}")
          return _public_keys_cache

  class GoogleIdentityAuthentication(authentication.BaseAuthentication):
      def authenticate(self, request):
          auth_header = request.META.get("HTTP_AUTHORIZATION")
          if not auth_header:
              return None

          parts = auth_header.split()
          if len(parts) != 2 or parts[0].lower() != "bearer":
              return None

          id_token = parts[1]
          project_id = getattr(settings, 'GOOGLE_CLOUD_PROJECT', 'animetix')

          # Support Local Emulator
          emulator_host = getattr(settings, 'FIREBASE_AUTH_EMULATOR_HOST', None)
          if emulator_host:
              try:
                  payload = jwt.decode(id_token, options={"verify_signature": False})
                  email = payload.get("email")
                  if not email:
                      raise exceptions.AuthenticationFailed("Emulator token missing email claim.")
                  user = self._get_or_create_user(email)
                  return (user, payload)
              except Exception as e:
                  raise exceptions.AuthenticationFailed(f"Invalid Emulator ID Token: {e}")

          # Standard Production Verification
          public_keys = get_google_public_keys()
          if not public_keys:
              raise exceptions.AuthenticationFailed("Google public keys unavailable.")

          try:
              header = jwt.get_unverified_header(id_token)
              kid = header.get("kid")
              if not kid or kid not in public_keys:
                  raise exceptions.AuthenticationFailed("Invalid kid in token header.")

              cert = public_keys[kid]
              
              payload = jwt.decode(
                  id_token,
                  cert,
                  algorithms=["RS256"],
                  audience=project_id,
                  issuer=f"https://securetoken.google.com/{project_id}"
              )
          except jwt.ExpiredSignatureError:
              raise exceptions.AuthenticationFailed("ID Token has expired.")
          except jwt.InvalidTokenError as e:
              raise exceptions.AuthenticationFailed(f"Invalid ID Token: {e}")
          except Exception as e:
              raise exceptions.AuthenticationFailed(f"Authentication failed: {e}")

          email = payload.get("email")
          if not email:
              raise exceptions.AuthenticationFailed("Token is missing email claim.")

          user = self._get_or_create_user(email)
          return (user, payload)

      def _get_or_create_user(self, email):
          try:
              return User.objects.get(email=email)
          except User.DoesNotExist:
              pass

          base_username = email.split('@')[0]
          username = base_username
          suffix_counter = 1
          
          while User.objects.filter(username=username).exists():
              username = f"{base_username}_{suffix_counter}"
              suffix_counter += 1

          user = User.objects.create_user(
              username=username,
              email=email,
          )
          user.set_unusable_password()
          user.save()
          logger.info(f"Automatically created User {username} for email {email}")
          return user
  ```

- [ ] **Step 2: Commit**
  ```bash
  git add backend/api/animetix/auth.py
  git commit -m "feat(auth): implement GoogleIdentityAuthentication backend token verifier"
  ```

---

### Task 4: Integrate settings.py, Deprecate Local Auth Views & Create Tests

**Files:**
- Modify: `backend/api/animetix_project/settings.py`
- Modify: `backend/api/animetix/api/core.py`
- Create: `tests/backend/test_gcip_auth.py`

- [ ] **Step 1: Update settings.py for default authentication classes**
  Modify the `REST_FRAMEWORK` and settings definitions in `backend/api/animetix_project/settings.py` to register the new authenticator and load emulator host env variable:
  Add `FIREBASE_AUTH_EMULATOR_HOST` config around lines 541:
  ```python
  # GCP Identity-Aware Proxy (IAP) Configuration
  GCP_IAP_AUDIENCE = env('GCP_IAP_AUDIENCE', default=None)
  IAP_APPROVED_ADMIN_EMAILS = env.list('IAP_APPROVED_ADMIN_EMAILS', default=[])
  FIREBASE_AUTH_EMULATOR_HOST = env('FIREBASE_AUTH_EMULATOR_HOST', default=None)
  ```

  Update `REST_FRAMEWORK` around line 243:
  ```python
  REST_FRAMEWORK = {
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
      'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
      'DEFAULT_AUTHENTICATION_CLASSES': [
          'backend.api.animetix.auth.GoogleIdentityAuthentication',
      ],
      'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
      'PAGE_SIZE': 20,
      'DEFAULT_THROTTLE_CLASSES': [
          'rest_framework.throttling.AnonRateThrottle',
          'rest_framework.throttling.UserRateThrottle'
      ],
      'DEFAULT_THROTTLE_RATES': {
          'anon': '100/day',
          'user': '1000/day'
      }
  }
  ```

- [ ] **Step 2: Deprecate local login, register, and logout views**
  Modify `backend/api/animetix/api/core.py` (lines 204-243) to disable local views:
  ```python
  @method_decorator(ensure_csrf_cookie, name='dispatch')
  @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
  class LoginView(APIView):
      permission_classes = [permissions.AllowAny]

      def post(self, request):
          return Response(
              {"success": False, "error": "Login is managed client-side via Google Identity Platform."},
              status=status.HTTP_405_METHOD_NOT_ALLOWED
          )


  class LogoutView(APIView):
      permission_classes = [permissions.AllowAny]

      def post(self, request):
          return Response(
              {"success": False, "error": "Logout is managed client-side via Google Identity Platform."},
              status=status.HTTP_405_METHOD_NOT_ALLOWED
          )


  @method_decorator(ensure_csrf_cookie, name='dispatch')
  @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
  class RegisterView(APIView):
      permission_classes = [permissions.AllowAny]

      def post(self, request):
          return Response(
              {"success": False, "error": "Registration is managed client-side via Google Identity Platform."},
              status=status.HTTP_405_METHOD_NOT_ALLOWED
          )
  ```

- [ ] **Step 3: Create backend tests for Google Identity Platform**
  Create `tests/backend/test_gcip_auth.py` with full coverage:
  ```python
  import pytest
  from unittest.mock import patch, MagicMock
  import jwt
  from django.test import RequestFactory
  from rest_framework.exceptions import AuthenticationFailed
  from django.contrib.auth import get_user_model
  from backend.api.animetix.auth import GoogleIdentityAuthentication

  User = get_user_model()

  @pytest.fixture
  def rf():
      return RequestFactory()

  @pytest.fixture
  def authenticator():
      return GoogleIdentityAuthentication()

  @pytest.mark.django_db
  @patch("backend.api.animetix.auth.get_google_public_keys")
  @patch("jwt.decode")
  def test_gcip_auth_success(mock_decode, mock_certs, rf, authenticator, settings):
      settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
      settings.FIREBASE_AUTH_EMULATOR_HOST = None
      
      mock_certs.return_value = {"key1": "cert_data"}
      mock_decode.return_value = {
          "email": "test@animetix.com",
          "sub": "gcip-uid-456"
      }
      
      # Mock unverified header kid lookup
      with patch("jwt.get_unverified_header", return_value={"kid": "key1"}):
          request = rf.get("/api/v1/auth/me/")
          request.META["HTTP_AUTHORIZATION"] = "Bearer valid-jwt-token"
          
          user, token = authenticator.authenticate(request)
          
          assert user is not None
          assert user.email == "test@animetix.com"
          assert user.username == "test"
          assert token["sub"] == "gcip-uid-456"

  @pytest.mark.django_db
  def test_gcip_auth_emulator_success(rf, authenticator, settings):
      settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
      settings.FIREBASE_AUTH_EMULATOR_HOST = "localhost:9099"
      
      # Mock decoding emulator token
      with patch("jwt.decode", return_value={"email": "emulator@animetix.com"}):
          request = rf.get("/api/v1/auth/me/")
          request.META["HTTP_AUTHORIZATION"] = "Bearer emulator-unsigned-token"
          
          user, token = authenticator.authenticate(request)
          
          assert user is not None
          assert user.email == "emulator@animetix.com"
          assert user.username == "emulator"

  @pytest.mark.django_db
  @patch("backend.api.animetix.auth.get_google_public_keys")
  def test_gcip_auth_invalid_header(rf, authenticator, mock_certs):
      request = rf.get("/api/v1/auth/me/")
      request.META["HTTP_AUTHORIZATION"] = "InvalidFormatHeader"
      
      result = authenticator.authenticate(request)
      assert result is None

  @pytest.mark.django_db
  @patch("backend.api.animetix.auth.get_google_public_keys")
  @patch("jwt.decode")
  def test_gcip_auth_expired_token(mock_decode, mock_certs, rf, authenticator, settings):
      settings.GOOGLE_CLOUD_PROJECT = "my-gcp-project"
      settings.FIREBASE_AUTH_EMULATOR_HOST = None
      
      mock_certs.return_value = {"key1": "cert_data"}
      mock_decode.side_effect = jwt.ExpiredSignatureError("Signature has expired")
      
      with patch("jwt.get_unverified_header", return_value={"kid": "key1"}):
          request = rf.get("/api/v1/auth/me/")
          request.META["HTTP_AUTHORIZATION"] = "Bearer expired-jwt-token"
          
          with pytest.raises(AuthenticationFailed) as exc_info:
              authenticator.authenticate(request)
          assert "ID Token has expired" in str(exc_info.value)
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add backend/api/animetix_project/settings.py backend/api/animetix/api/core.py tests/backend/test_gcip_auth.py
  git commit -m "feat(auth): configure settings, deprecate old auth views, and add unit tests"
  ```

---

## Verification Plan

### Automated Tests
- Run backend tests:
  ```bash
  poetry run pytest tests/backend/test_gcip_auth.py -v
  ```
  *(or `pytest` depending on the active environment).*

### Manual Verification
- Launch the application locally and check that clicking login/register triggers the Firebase authentication flow and forwards the bearer token in headers.
