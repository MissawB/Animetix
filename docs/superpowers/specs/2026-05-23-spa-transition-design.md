# Design de Transition SPA (API Pure) - 2026-05-23

## 1. Objectif
Transitionner l'application d'un modèle hybride (Templates Django + SPA React) vers une SPA React autonome utilisant Django comme API pure. Cette migration vise à réduire la dette technique liée à la duplication de code et à la complexité de synchronisation d'état.

## 2. Architecture de l'Authentification
- **Session** : Maintien des sessions Django via cookies `HttpOnly` pour garantir la compatibilité avec l'existant.
- **Hydratation SPA** : Ajout d'un endpoint `GET /api/v1/auth/me/` consommé au chargement de l'application pour initialiser l'état d'authentification.
- **Gestion d'état** : Création d'un `authStore` (Zustand) pour centraliser `isAuthenticated` et `user`.

## 3. Composants Techniques
- **API (backend)** :
  - `GET /api/v1/auth/me/` : Retourne l'utilisateur courant ou 401.
  - `POST /api/v1/auth/logout/` : Invalidation de la session.
- **Frontend (Store)** : `frontend/backend/store/authStore.ts` pour gérer l'état global utilisateur.
- **Frontend (Route Guard)** : Composant `<ProtectedRoute />` pour sécuriser les routes privées.

## 4. Stratégie de Migration
1. **Implémentation Infrastructure** : Création du `authStore` et ajout des endpoints API dans `api.ts`.
2. **Migration Layout** : Remplacement des composants Django (`Navbar`, `Sidebar`) par des composants React dans un `AppShell`.
3. **Nettoyage** : Suppression progressive des templates Django superflus.

## 5. Impact Utilisateur
- Navigation fluide (SPA).
- Aucune reconnexion nécessaire (utilisation des cookies existants).

---
*Date : 2026-05-23*
