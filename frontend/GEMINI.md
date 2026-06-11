# GEMINI - Frontend Mandates

This file defines the development constraints for the React Single Page Application (SPA).

## 🏗️ Architecture & Organization
- **Structure:** Follow **Feature-Driven Development (FDD)**. Organize code within `src/features/{feature_name}/` containing dedicated `components/`, `hooks/`, `store/`, and `utils/`.
- **Components:** Prefer functional components with hooks. Use **Error Boundaries** and `Suspense` for robust error handling and loading states.
- **Storybook:** Develop isolated UI components in Storybook (`.stories.tsx`) before integration.

## ⚛️ Technology Stack
- **Framework:** React 19 (TypeScript).
- **Routing:** React Router 7.
- **State Management:**
    - Global state: Lightweight `Zustand` stores.
    - Game logic: Use Zustand for complex state transitions and performance.
- **Data Fetching:** `TanStack Query` (React Query) with local indexDB persistence (`idb-keyval`).

## 🎨 UI & Styling
- **CSS:** `Tailwind CSS`. Respect design system parameters defined in `tailwind.config.js`.
- **Animations:** `Framer Motion` for smooth interface transitions and game UI elements.
- **Icons:** `Lucide React`.
- **Accessibility (a11y):** Strict adherence to WCAG standards.
    - Mandatory ARIA roles and labels for non-native interactive elements.
    - Full keyboard navigation support (focus management, `onKeyDown` listeners).
    - Media elements must include `<track>` for subtitles/captions.
    - Validated via `eslint-plugin-jsx-a11y` and `@axe-core/playwright`.

## 🛠️ Development & Typings
- **Strict TypeScript:** **Forbid the use of `any`**. Use `unknown` or explicit interfaces if necessary.
- **API Typings:** Types must be generated from the OpenAPI specification using `npm run generate:api` (outputting to `src/types/api.d.ts`). **Do not declare API models manually** in `src/types/index.ts` or `src/api.ts`.
- **Validation:** `Zod` for form and schema validations (`react-hook-form`).
- **Internationalization (i18n):** Use `i18next` for all user-facing strings. No hardcoded text in components.

## 📈 Observability & Quality
- **Monitoring:** Integrate `Sentry` for error tracking and `PostHog` for product analytics.
- **Unit Testing:** `Vitest` for logic and hooks.
- **E2E & VRT:** `Playwright`. Verify visual regressions (VRT) using visual snapshot comparison on major UI component updates.
