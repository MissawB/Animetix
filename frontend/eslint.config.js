import storybook from "eslint-plugin-storybook";
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier';
import { defineConfig, globalIgnores } from 'eslint/config';

export default defineConfig([
  // `dist` is the build output; `src/types/api.d.ts` is generated from schema.yaml
  // (`npm run generate:api`) and would otherwise drown lint output in
  // no-irregular-whitespace noise we don't control.
  globalIgnores(['dist', 'src/types/api.d.ts']),
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.flatConfigs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'jsx-a11y/no-autofocus': 'off',
      // --- Durcissement a11y (au-delà du recommended) ---
      // Règles déjà à 0 violation → en `error` (enforcement, sans risque).
      'jsx-a11y/no-static-element-interactions': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/no-noninteractive-element-interactions': 'error',
      'jsx-a11y/no-noninteractive-tabindex': 'error',
      // Contrôles sans nom accessible : tous les cas existants ont été étiquetés
      // (aria-label), la règle est donc durcie en `error` pour empêcher les régressions.
      'jsx-a11y/control-has-associated-label': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
    },
  },
  ...storybook.configs["flat/recommended"],
  // Must stay LAST: turns off ESLint rules that would conflict with Prettier
  // formatting (we run Prettier for style, ESLint for correctness).
  eslintConfigPrettier,
]);
