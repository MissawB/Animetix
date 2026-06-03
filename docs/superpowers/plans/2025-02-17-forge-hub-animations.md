# Forge Hub Animations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance ForgeHubPage with a particle background and floating animations.

**Architecture:** Utilize `framer-motion` for particle animations (using a `motion.div` layer) and `framer-motion` `animate` prop for floating `RelicItem` cards.

**Tech Stack:** React, TypeScript, TailwindCSS, `framer-motion`.

---

### Task 1: Add Particle Animation Layer

**Files:**
- Modify: `C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\frontend\src\features\labs\ForgeHubPage.tsx`

- [ ] **Step 1: Add framer-motion import**
Add `import { motion } from 'framer-motion';` to imports.

- [ ] **Step 2: Add Particle Background Layer**
Inside the main container, add:
```tsx
<div className="fixed inset-0 pointer-events-none z-0">
  {[...Array(20)].map((_, i) => (
    <motion.div
      key={i}
      className="absolute w-1 h-1 bg-white rounded-full"
      initial={{ x: Math.random() * 1000, y: Math.random() * 1000 }} // Simplified initial position
      animate={{ y: [0, -500], opacity: [0, 0.5, 0] }}
      transition={{ duration: 10 + Math.random() * 10, repeat: Infinity }}
    />
  ))}
</div>
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/features/labs/ForgeHubPage.tsx
git commit -m "style: add particle background to Forge Hub"
```

### Task 2: Add Floating Animation to RelicItem

**Files:**
- Modify: `C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\frontend\src\features\labs\ForgeHubPage.tsx`

- [ ] **Step 1: Wrap RelicItem with motion.div**
In the mapping loop for `categories`:
```tsx
<motion.div
  animate={{ y: [0, -10, 0] }}
  transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
>
  <RelicItem
    key={cat.id}
    ...
  >
    <cat.icon className="w-full h-full stroke-[0.5]" />
  </RelicItem>
</motion.div>
```

- [ ] **Step 2: Commit**
```bash
git add frontend/src/features/labs/ForgeHubPage.tsx
git commit -m "style: add final polish and animations to Forge Hub"
```
