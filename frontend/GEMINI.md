# GEMINI - Frontend Mandates

This file defines the development constraints for the React Single Page Application (SPA).

## ⚛️ Technology Stack
- **Framework:** React 19 (TypeScript).
- **Routing:** React Router 7.
- **State Management:**
    - Global state: Lightweight `Zustand` stores.
    - Game timelines and interactions: Refactored to Zustand stores for optimal package size.
- **Data Fetching:** `TanStack Query` (React Query) with local indexDB persistence (`idb-keyval`).

## 🎨 UI & Styling
- **CSS:** `Tailwind CSS`. Respect design system parameters defined in `tailwind.config.js`.
- **Animations:** `Framer Motion` for smooth interface transitions and game UI elements.
- **Icons:** `Lucide React`.
- **Accessibility:** Adhere to WCAG standards (validated via `eslint-plugin-jsx-a11y` and `axe-core`).

## 🛠️ Development & Typings
- **Validation:** `Zod` for form and schema validations (`react-hook-form`).
- **API Typings:** Types must be generated from the OpenAPI specification using `npm run generate:api` (outputting to `src/types/api.d.ts`). Do not declare API models manually.
- **Internationalization:** Use `i18next` for all user-facing strings.

## 🧪 Testing & Verification
- **Unit Testing:** `Vitest`.
- **E2E & VRT:** `Playwright`. Verify visual regressions using visual snapshot comparison tests on major UI component updates.
- **Storybook:** Develop isolated UI components in Storybook before integration.
