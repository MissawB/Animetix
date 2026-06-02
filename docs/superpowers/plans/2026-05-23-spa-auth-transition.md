# Transition SPA Authentification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize authentication in the React SPA by exposing Django user state via API and creating a React `AuthContext`.

**Architecture:**
1. Backend: Expose `GET /api/v1/auth/me/` (Django view/API).
2. Frontend: Create `useAuthStore` (Zustand) and `AuthProvider` (React Context).
3. Logic: Protect private routes with a `ProtectedRoute` component.

**Tech Stack:** Django (Backend), React + Vite (Frontend), Zustand (State), Axios/Fetch (Client).

---

### Task 1: Backend Auth API

**Files:**
- Modify: `backend/api/animetix/urls.py`
- Modify: `backend/api/animetix/views/auth_views.py` (create if not exist)

- [ ] **Step 1: Create auth view**
Write or modify `auth_views.py`:
```python
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def get_user_me(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        })
    return JsonResponse({"detail": "Not authenticated"}, status=401)
```

- [ ] **Step 2: Add URL mapping**
In `backend/api/animetix/urls.py`:
```python
from .views.auth_views import get_user_me

urlpatterns += [
    path('api/v1/auth/me/', get_user_me, name='api_auth_me'),
]
```

- [ ] **Step 3: Commit**
```bash
git add backend/api/animetix/urls.py backend/api/animetix/views/auth_views.py
git commit -m "feat(backend): add /api/v1/auth/me/ endpoint"
```

### Task 2: Frontend Auth Store

**Files:**
- Create: `frontend/backend/store/authStore.ts`
- Modify: `frontend/backend/api.ts`

- [ ] **Step 1: Create Auth Store**
`frontend/backend/store/authStore.ts`:
```typescript
import { create } from 'zustand';
import { api } from '../api';

interface AuthState {
  user: any | null;
  isAuthenticated: boolean;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  checkAuth: async () => {
    try {
      const user = await api.get('/api/v1/auth/me/');
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },
}));
```

- [ ] **Step 2: Add API calls**
`frontend/backend/api.ts`:
```typescript
// Add to api.ts
export async function getAuthUser() {
  return apiClient('/api/v1/auth/me/');
}
```

- [ ] **Step 3: Commit**
```bash
git add frontend/backend/store/authStore.ts frontend/backend/api.ts
git commit -m "feat(frontend): add authStore and api client helper"
```

### Task 3: Auth Provider & Route Protection

**Files:**
- Create: `frontend/backend/context/AuthProvider.tsx`
- Modify: `frontend/backend/main.tsx`

- [ ] **Step 1: Create Auth Provider**
`frontend/backend/context/AuthProvider.tsx`:
```typescript
import React, { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return <>{children}</>;
};
```

- [ ] **Step 2: Wrap App**
`frontend/backend/main.tsx`:
```tsx
import { AuthProvider } from './context/AuthProvider';
// ...
root.render(
  <AuthProvider>
    <App />
  </AuthProvider>
);
```

- [ ] **Step 3: Commit**
```bash
git add frontend/backend/context/AuthProvider.tsx frontend/backend/main.tsx
git commit -m "feat(frontend): initialize AuthProvider"
```
