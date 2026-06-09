# Frontend Build Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all ESLint parsing errors and TypeScript compilation errors in the frontend to stabilize the build.

**Architecture:** 
- Update ESLint configuration to support TypeScript using Flat Config.
- Fix specific JSX syntax errors in page components.
- Standardize verification scripts.

**Tech Stack:** React 19, TypeScript, ESLint (Flat Config), typescript-eslint.

---

### Task 1: ESLint Infrastructure & Dependencies

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/eslint.config.js`

- [ ] **Step 1: Install typescript-eslint dependencies**

Run: `npm install --save-dev typescript-eslint` (in `frontend` directory)
Expected: `typescript-eslint` added to `devDependencies`.

- [ ] **Step 2: Update eslint.config.js to support TypeScript**

```javascript
import storybook from "eslint-plugin-storybook";
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import tseslint from 'typescript-eslint';
import { defineConfig, globalIgnores } from 'eslint/config';

export default defineConfig([
  globalIgnores(['dist']),
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
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'jsx-a11y/no-autofocus': 'off', // Relaxing some accessibility rules if needed
    },
  },
  ...storybook.configs["flat/recommended"]
]);
```

- [ ] **Step 3: Verify ESLint can now parse TSX**

Run: `npm run lint`
Expected: Parsing errors should be gone. Remaining errors should be logical/syntax errors in components.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/eslint.config.js
git commit -m "build: configure eslint for typescript support"
```

---

### Task 2: Fix MangaVoicePage.tsx Syntax

**Files:**
- Modify: `frontend/src/pages/labs/MangaVoicePage.tsx:155`

- [ ] **Step 1: Fix closing tag for Button**

Find:
```tsx
                                <Button variant="outline" className="border-white/10 hover:bg-white/5 rounded-xl px-8">
                                    <Save className="w-4 h-4 mr-2" /> SAUVEGARDER
                                </p>
```
Replace with:
```tsx
                                <Button variant="outline" className="border-white/10 hover:bg-white/5 rounded-xl px-8">
                                    <Save className="w-4 h-4 mr-2" /> SAUVEGARDER
                                </Button>
```

- [ ] **Step 2: Verify fix**

Run: `npm run check-types`
Expected: Error at `MangaVoicePage.tsx:160` should be gone.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/labs/MangaVoicePage.tsx
git commit -m "fix(frontend): correct button closing tag in MangaVoicePage"
```

---

### Task 3: Fix ArchetypeNexusPage.tsx Syntax

**Files:**
- Modify: `frontend/src/pages/social/ArchetypeNexusPage.tsx`

- [ ] **Step 1: Fix mismatched JSX tags and StatBar declaration**

Replace the end of the file (from `StatBar` declaration onwards) and check the `AnimatedPage` closing.

Find:
```tsx
        {/* Global Warning / Alpha Status */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 text-center">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-30 italic">
                Avertissement : Les déductions neuro-symboliques sont basées sur des modèles stochastiques résolus en temps réel. <br />
                Le drift d'archétype est recalculé après chaque session de forge ou de débat.
            </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

interface StatBarProps {
  label: string;
  value: number;
  color: string;
}

const StatBar: React.FC<StatBarProps> = ({ label, value, color }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-end">
      <span className="text-[9px] font-black uppercase tracking-widest opacity-40">{label}</span>
      <span className="text-xs font-black italic">{Math.round(value * 100)}%</span>
    </div>
    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${value * 100}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
        className={`h-full ${color}`} 
      />
    </div>
  </div>
);

export default ArchetypeNexusPage;
```

Actually, looking at the previous `read_file` output, the file was cut off or had invalid syntax. Let's fix the structure.

- [ ] **Step 2: Verify fix**

Run: `npm run check-types`
Expected: All errors in `ArchetypeNexusPage.tsx` should be resolved.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/social/ArchetypeNexusPage.tsx
git commit -m "fix(frontend): resolve malformed JSX and syntax in ArchetypeNexusPage"
```

---

### Task 4: Final Verification

- [ ] **Step 1: Run full lint**

Run: `npm run lint`
Expected: 0 errors (or only logical warnings).

- [ ] **Step 2: Run type check**

Run: `npm run check-types`
Expected: `Found 0 errors`.

- [ ] **Step 3: Final Commit**

```bash
git commit --allow-empty -m "chore: build stabilization complete"
```
