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
  // no-irregular-whitespace noise we don't control. `playwright-report`,
  // `test-results` and `coverage` are local test artifacts (minified JS) that
  // made local `npm run lint` explode with ~4000 vendor errors.
  globalIgnores(['dist', 'src/types/api.d.ts', 'playwright-report', 'test-results', 'coverage']),
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
      // Keep diagnostic chatter out of the prod console: console.log/info/debug are
      // forbidden (use the dev-only `logger` in src/utils/logger.ts instead);
      // console.warn/error stay allowed for real problems.
      'no-console': ['error', { allow: ['warn', 'error'] }],
      // Verrou du plafond « 0 fichiers > 500 lignes » (PR 93-96 + audit dette
      // 2026-07-22) : les 8 pages décomposées avaient re-régressé faute de
      // garde-fou. Lignes brutes (pas de skip) pour coller au `wc -l` des audits.
      'max-lines': ['error', { max: 500, skipBlankLines: false, skipComments: false }],
    },
  },
  {
    // Dette connue, trackée dans TODO.md (audit 2026-07-22) : exemptions à
    // retirer une par une au fil des décompositions. Ne RIEN ajouter ici —
    // décomposer le fichier à la place.
    files: [
      'src/types/index.ts',
      'src/pages/games/CovertestPage.tsx',
      'src/pages/games/ClassicLobbyPage.tsx',
    ],
    rules: { 'max-lines': 'off' },
  },
  ...storybook.configs["flat/recommended"],
  // Must stay LAST: turns off ESLint rules that would conflict with Prettier
  // formatting (we run Prettier for style, ESLint for correctness).
  eslintConfigPrettier,
]);
