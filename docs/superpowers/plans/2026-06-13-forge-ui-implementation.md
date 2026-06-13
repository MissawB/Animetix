# Forge UI Cyberpunk Immersive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the `/static/forge/` UI from a standard interface into a high-contrast, immersive Cyberpunk terminal experience.

**Architecture:** Transition using CSS (Tailwind) for aesthetic updates, Framer Motion for interactivity/glitch effects, and functional refactoring of `ForgePage.tsx` for terminal-styled component wrappers.

**Tech Stack:** React, Tailwind CSS, Framer Motion, Playwright (for VRT).

---

### Task 1: Setup Dependencies and Theme

**Files:**
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/package.json`

- [ ] **Step 1: Install Framer Motion**
Run: `npm install framer-motion`
Expected: `framer-motion` added to `package.json`.

- [ ] **Step 2: Update Tailwind Theme for Cyberpunk Palette**

Modify `frontend/tailwind.config.js` to add cyberpunk colors.

```javascript
// Add to extend -> colors:
cyberpunk: {
  bg: '#050505',
  panel: 'rgba(255, 255, 255, 0.05)',
  panelBorder: 'rgba(255, 255, 255, 0.1)',
  neonCyan: '#00F3FF',
  neonMagenta: '#FF00FF',
}
```

- [ ] **Step 3: Commit**
`git add frontend/package.json frontend/tailwind.config.js`
`git commit -m "chore: setup dependencies and theme for cyberpunk ui"`

---

### Task 2: Create Terminal-Style Wrappers

**Files:**
- Create: `frontend/src/components/forge/CyberTerminalPanel.tsx`
- Create: `frontend/src/components/forge/GlitchText.tsx`

- [ ] **Step 1: Implement `CyberTerminalPanel`**

```tsx
import React from 'react';

export const CyberTerminalPanel: React.FC<{children: React.ReactNode, className?: string}> = ({children, className}) => (
  <div className={`backdrop-blur-md bg-cyberpunk-panel border border-cyberpunk-panelBorder rounded-3xl ${className}`}>
    {children}
  </div>
);
```

- [ ] **Step 2: Implement `GlitchText` using Framer Motion**

```tsx
import React from 'react';
import { motion } from 'framer-motion';

export const GlitchText: React.FC<{children: React.ReactNode, className?: string}> = ({children, className}) => (
  <motion.div
    whileHover={{ x: [-1, 1, -1], transition: { repeat: Infinity, duration: 0.1 } }}
    className={className}
  >
    {children}
  </motion.div>
);
```

- [ ] **Step 3: Commit**
`git add frontend/src/components/forge/CyberTerminalPanel.tsx frontend/src/components/forge/GlitchText.tsx`
`git commit -m "feat: add CyberTerminalPanel and GlitchText components"`

---

### Task 3: Refactor Sliders and Buttons

**Files:**
- Create: `frontend/src/components/forge/CyberSlider.tsx`
- Create: `frontend/src/components/forge/CyberButton.tsx`

- [ ] **Step 1: Implement `CyberSlider` (for Chaos/Balance)**

*Note: Needs custom range styles in Tailwind.*

- [ ] **Step 2: Implement `CyberButton` (for Forging)**

*Note: Add pulsating neon glow.*

- [ ] **Step 3: Commit**
`git add frontend/src/components/forge/CyberSlider.tsx frontend/src/components/forge/CyberButton.tsx`
`git commit -m "feat: add CyberSlider and CyberButton components"`

---

### Task 4: Integrate into ForgePage

**Files:**
- Modify: `frontend/src/pages/games/ForgePage.tsx`

- [ ] **Step 1: Apply Cyberpunk theme to `ForgePage`**
Replace standard containers with `CyberTerminalPanel`. Use `font-mono` for technical data. Apply glitch effect to title.

- [ ] **Step 2: Verify functionality**
Check that sliders and fusion still work.

- [ ] **Step 3: Commit**
`git add frontend/src/pages/games/ForgePage.tsx`
`git commit -m "feat: integrate cyberpunk UI elements into ForgePage"`

---

### Task 5: VRT Snapshot Setup

**Files:**
- Create: `frontend/e2e/forge-ui.spec.ts`

- [ ] **Step 1: Add Playwright VRT snapshot**

```typescript
import { test, expect } from '@playwright/test';

test('Forge UI cyberpunk styling', async ({ page }) => {
  await page.goto('/static/forge/');
  await expect(page).toHaveScreenshot('forge-ui-idle.png');
});
```

- [ ] **Step 2: Commit**
`git add frontend/e2e/forge-ui.spec.ts`
`git commit -m "test: add visual regression test for Forge UI"`
