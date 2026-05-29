# GEMINI - Mandats Frontend

Ce fichier définit les contraintes de développement pour l'interface React SPA.

## ⚛️ Stack Technologique
- **Framework :** React 19 (TypeScript).
- **Routage :** React Router 7.
- **Gestion d'État :**
    - État global simple : `Zustand`.
    - Logique de jeu/états complexes : `XState`.
- **Data Fetching :** `TanStack Query` (React Query) avec persistance locale (`idb-keyval`).

## 🎨 UI & Styling
- **CSS :** `Tailwind CSS`. Respecter le design system défini dans `tailwind.config.js`.
- **Animations :** `Framer Motion` pour les transitions d'interface.
- **Icons :** `Lucide React`.
- **Accessibilité :** Respecter les normes WCAG (vérification via `eslint-plugin-jsx-a11y` et `axe-core`).

## 🛠️ Développement & Types
- **Validation :** `Zod` pour la validation des schémas de données et des formulaires (`react-hook-form`).
- **Typage API :** Les types doivent être générés à partir du schéma OpenAPI via `npm run generate:api` (vers `src/types/api.d.ts`). Ne pas définir les types API manuellement.
- **Internationalisation :** Utiliser `i18next` pour toutes les chaînes de caractères visibles.

## 🧪 Tests & Validation
- **Unitaires :** `Vitest`.
- **E2E & VRT :** `Playwright`. Toujours vérifier les régressions visuelles lors de changements de composants UI majeurs.
- **Storybook :** Développer les composants isolés dans Storybook avant intégration.
